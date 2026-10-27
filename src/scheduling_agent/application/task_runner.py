"""Run the task set and judge every task by the calendar's real end state, never by what the agent said."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from scheduling_agent.application.agent import SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import ApprovalStore, AuditLog, CalendarPort, CheckpointStore, Clock
from scheduling_agent.domain.approvals import AuditLine
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
from scheduling_agent.domain.run import RunState, RunStatus
from scheduling_agent.domain.tasks import TaskSpec, end_state, expected_end_state

_log = logging.getLogger(__name__)
MAX_APPROVAL_ROUNDS = 6


class Approver(Protocol):
    """The person: decides whether a proposal is what the task asked for."""

    def decide(self, task: TaskSpec, proposal: Proposal) -> bool: ...


class ExpectedWritesApprover:
    """Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else."""

    def decide(self, task: TaskSpec, proposal: Proposal) -> bool:
        args = proposal.args
        if proposal.action is Action.BOOK:
            return (tuple(sorted(args["people"])), args["start"], args["minutes"]) in task.add
        if proposal.action is Action.CANCEL:
            return args["event_id"] in task.remove
        new_key = (tuple(sorted(args["people"])), args["new_start"], args["minutes"])
        return args["event_id"] in task.remove and new_key in task.add


class CalendarAdmin(Protocol):
    """Resets the calendar to its seed between task runs (a demo and test aid)."""

    def reset(self) -> None: ...


@dataclass(frozen=True, slots=True)
class AgentKit:
    """One agent with the stores it was built on, so a runner can read what it did."""

    agent: SchedulingAgent
    approvals: ApprovalStore
    audit: AuditLog
    checkpoints: CheckpointStore
    memory: MemoryService
    calendar: CalendarPort


@dataclass(frozen=True, slots=True)
class TaskResult:
    """One attempt at one task."""

    task_id: str
    attempt: int
    passed: bool
    status: RunStatus
    steps: int
    tokens: int
    approvals_granted: int
    approvals_rejected: int
    writes_without_approval: int
    final_text: str
    stop_reason: str


class TaskRunner:
    """Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects."""

    def __init__(
        self,
        admin: CalendarAdmin,
        build: Callable[[], AgentKit],
        approver: Approver,
        clock: Clock,
    ) -> None:
        self._admin = admin
        self._build = build
        self._approver = approver
        self._clock = clock

    def run_once(self, task: TaskSpec, attempt: int) -> TaskResult:
        """One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task."""
        self._admin.reset()
        kit = self._build()
        seed = kit.calendar.active_events()
        for person, statement in task.facts:
            kit.memory.remember(person, statement, session=f"{task.id}-earlier")
        state = kit.agent.start(task.text, session=f"{task.id}-run{attempt}", run_id=f"{task.id}-r{attempt}")
        granted = rejected = rounds = 0
        while state.status is RunStatus.AWAITING_APPROVAL and rounds < MAX_APPROVAL_ROUNDS:
            rounds += 1
            for approval in [a for a in kit.approvals.pending() if a.run_id == state.run_id]:
                approve = self._approver.decide(task, approval.proposal)
                kit.approvals.decide(approval.id, approve, "task-runner", self._clock.now())
                granted += approve
                rejected += not approve
            state = kit.agent.resume(state.run_id)
        actual = end_state(kit.calendar.active_events())
        passed = actual == expected_end_state(seed, task)
        return TaskResult(
            task.id,
            attempt,
            passed,
            state.status,
            state.steps,
            state.tokens,
            granted,
            rejected,
            _writes_without_approval(kit, state),
            state.final_text,
            state.stop_reason,
        )

    def run_all(
        self, tasks: list[TaskSpec], repeats: int, stop_requested: Callable[[], bool] = lambda: False
    ) -> list[TaskResult]:
        """Every task `repeats` times, in order."""
        results: list[TaskResult] = []
        for task in tasks:
            for attempt in range(1, repeats + 1):
                if stop_requested():
                    return results
                result = self.run_once(task, attempt)
                _log.info(
                    "task attempt",
                    extra={
                        "fields": {"task": task.id, "attempt": attempt, "passed": result.passed, "steps": result.steps}
                    },
                )
                results.append(result)
        return results


def _writes_without_approval(kit: AgentKit, state: RunState) -> int:
    """'written' audit lines whose approval is missing or not approved: must be zero."""
    lines: list[AuditLine] = kit.audit.lines(state.run_id)
    bad = 0
    for line in lines:
        if line.outcome != "written":
            continue
        approval = kit.approvals.get(line.approval_id) if line.approval_id else None
        if approval is None or approval.status is not ApprovalStatus.APPROVED:
            bad += 1
    return bad
