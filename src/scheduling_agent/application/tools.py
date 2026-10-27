"""The agent's tools: reads run as they are, every write is a proposal that waits for a person's approval."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import date, datetime, time
from typing import Any

from scheduling_agent.application.ports import ApprovalStore, AuditLog, CalendarPort, Clock, FailPoints
from scheduling_agent.domain.approvals import AuditLine
from scheduling_agent.domain.errors import ApprovalError, CalendarError
from scheduling_agent.domain.llm import ToolSpec
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal, write_key

READ_TOOLS = ("find_free_slots", "get_event")
WRITE_TOOLS = {"book_meeting": Action.BOOK, "move_meeting": Action.MOVE, "cancel_meeting": Action.CANCEL}
MAX_SLOTS_SHOWN = 12


def tool_specs() -> tuple[ToolSpec, ...]:
    """The tool definitions as the model sees them."""
    people = {"type": "array", "items": {"type": "string"}, "description": "lowercase first names, for example alice"}
    return (
        ToolSpec(
            "find_free_slots",
            "Find start times at which every listed person is free. Weekdays, 09:00 to 17:00, on the half hour.",
            {
                "type": "object",
                "properties": {
                    "people": people,
                    "first_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "last_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "minutes": {"type": "integer", "description": "length, a multiple of 30"},
                    "not_before": {"type": "string", "description": "HH:MM, earliest start"},
                    "not_after": {"type": "string", "description": "HH:MM, latest end"},
                },
                "required": ["people", "first_day", "last_day", "minutes"],
            },
        ),
        ToolSpec(
            "get_event",
            "Read one event by id: who is in it, when it starts and how long it is.",
            {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]},
        ),
        ToolSpec(
            "book_meeting",
            "Propose a new meeting. A person must approve it before it is booked.",
            {
                "type": "object",
                "properties": {
                    "people": people,
                    "start": {"type": "string", "description": "YYYY-MM-DDTHH:MM"},
                    "minutes": {"type": "integer"},
                },
                "required": ["people", "start", "minutes"],
            },
        ),
        ToolSpec(
            "move_meeting",
            "Propose moving an event to a new start. A person must approve it first.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "new_start": {"type": "string", "description": "YYYY-MM-DDTHH:MM"},
                },
                "required": ["event_id", "new_start"],
            },
        ),
        ToolSpec(
            "cancel_meeting",
            "Propose cancelling an event. A person must approve it first.",
            {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]},
        ),
    )


def dump(value: Mapping[str, Any]) -> str:
    """Tool results are compact, sorted JSON."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _time(text: str | None) -> time | None:
    return time.fromisoformat(text) if text else None


class ToolBox:
    """Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly."""

    def __init__(
        self,
        calendar: CalendarPort,
        approvals: ApprovalStore,
        audit: AuditLog,
        clock: Clock,
        failpoints: FailPoints,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._calendar = calendar
        self._approvals = approvals
        self._audit = audit
        self._clock = clock
        self._failpoints = failpoints
        self._now = now or clock.now

    @staticmethod
    def is_write(name: str) -> bool:
        return name in WRITE_TOOLS

    def read(self, name: str, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run a read tool. A problem with the arguments or the calendar comes back as an error the model can read."""
        try:
            if name == "find_free_slots":
                slots = self._calendar.free_slots(
                    [str(p) for p in args["people"]],
                    date.fromisoformat(str(args["first_day"])),
                    date.fromisoformat(str(args["last_day"])),
                    int(args["minutes"]),
                    _time(args.get("not_before")),
                    _time(args.get("not_after")),
                )
                shown = [s.isoformat(timespec="minutes") for s in slots[:MAX_SLOTS_SHOWN]]
                return {"slots": shown, "count": len(slots), "truncated": len(slots) > MAX_SLOTS_SHOWN}
            if name == "get_event":
                event = self._calendar.get_event(str(args["event_id"]))
                return {
                    "event_id": event.id,
                    "people": list(event.people),
                    "start": event.start.isoformat(timespec="minutes"),
                    "minutes": event.minutes,
                    "cancelled": event.cancelled,
                }
        except CalendarError as error:
            return {"error": f"{type(error).__name__}: {error}"}
        except (KeyError, ValueError, TypeError) as error:
            return {"error": f"bad arguments: {error}"}
        return {"error": f"unknown tool {name}"}

    def propose(self, name: str, args: Mapping[str, Any]) -> Proposal | dict[str, Any]:
        """Build the proposal for a write tool call, or an error result when the arguments or the target are bad."""
        action = WRITE_TOOLS[name]
        try:
            if action is Action.BOOK:
                people = sorted(str(p) for p in args["people"])
                start = datetime.fromisoformat(str(args["start"])).isoformat(timespec="minutes")
                return Proposal(action, {"people": people, "start": start, "minutes": int(args["minutes"])})
            event = self._calendar.get_event(str(args["event_id"]))
            if event.cancelled:
                return {"error": f"event {event.id} is already cancelled"}
            snapshot = {
                "event_id": event.id,
                "people": sorted(event.people),
                "minutes": event.minutes,
                "start": event.start.isoformat(timespec="minutes"),
            }
            if action is Action.CANCEL:
                return Proposal(action, snapshot)
            new_start = datetime.fromisoformat(str(args["new_start"])).isoformat(timespec="minutes")
            return Proposal(action, {**snapshot, "new_start": new_start})
        except CalendarError as error:
            return {"error": f"{type(error).__name__}: {error}"}
        except (KeyError, ValueError, TypeError) as error:
            return {"error": f"bad arguments: {error}"}

    def request_approval(self, run_id: str, step: int, proposal: Proposal) -> dict[str, Any]:
        """Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write."""
        approval = self._approvals.request(run_id, step, proposal, self._now())
        self._audit.append(
            AuditLine(
                self._now(),
                run_id,
                step,
                proposal.action.value,
                "refused",
                approval.id,
                "no approval yet; proposal recorded",
            )
        )
        return {"status": "needs_approval", "approval_id": approval.id, "proposal": json.loads(proposal.canonical())}

    def execute_write(self, run_id: str, step: int, proposal: Proposal, approval_id: str | None) -> dict[str, Any]:
        """Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.

        The calendar calls carry keys built from the run id and the step, so running this twice after a crash is safe.
        """
        try:
            self._check_approval(proposal, approval_id)
        except ApprovalError as error:
            self._audit.append(
                AuditLine(self._now(), run_id, step, proposal.action.value, "refused", approval_id, str(error))
            )
            return {"status": "refused", "detail": str(error)}
        try:
            result = self._apply(run_id, step, proposal)
        except CalendarError as error:
            self._audit.append(
                AuditLine(
                    self._now(),
                    run_id,
                    step,
                    proposal.action.value,
                    "failed",
                    approval_id,
                    f"{type(error).__name__}: {error}",
                )
            )
            return {"status": "failed", "error": f"{type(error).__name__}: {error}"}
        self._audit.append(
            AuditLine(self._now(), run_id, step, proposal.action.value, "written", approval_id, result["event_id"])
        )
        return result

    def _check_approval(self, proposal: Proposal, approval_id: str | None) -> None:
        if approval_id is None:
            raise ApprovalError("no approval id: a person has to approve every write")
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ApprovalError(f"unknown approval {approval_id}")
        if approval.status is not ApprovalStatus.APPROVED:
            raise ApprovalError(f"approval {approval_id} is {approval.status.value}")
        if approval.proposal.digest() != proposal.digest():
            raise ApprovalError(f"approval {approval_id} was granted for a different proposal")

    def _apply(self, run_id: str, step: int, proposal: Proposal) -> dict[str, Any]:
        args = proposal.args
        if proposal.action is Action.BOOK:
            booked = self._calendar.book(
                args["people"], datetime.fromisoformat(args["start"]), args["minutes"], write_key(run_id, step)
            )
            return {"status": "booked", "event_id": booked.event.id, "replayed": booked.replayed}
        if proposal.action is Action.CANCEL:
            cancelled = self._calendar.cancel(args["event_id"], write_key(run_id, step))
            return {"status": "cancelled", "event_id": cancelled.event.id, "replayed": cancelled.replayed}
        cancelled = self._calendar.cancel(args["event_id"], write_key(run_id, step, "cancel"))
        self._failpoints.hit("between_move_cancel_and_book")
        booked = self._calendar.book(
            args["people"], datetime.fromisoformat(args["new_start"]), args["minutes"], write_key(run_id, step, "book")
        )
        return {
            "status": "moved",
            "event_id": booked.event.id,
            "cancelled": cancelled.event.id,
            "replayed": booked.replayed,
        }
