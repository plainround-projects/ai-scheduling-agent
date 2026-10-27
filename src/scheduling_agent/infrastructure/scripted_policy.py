"""A deterministic stand-in for the model: a rule-based planner that speaks the same tool-calling protocol.

It is not a language model. It exists so the whole agent (loop, approvals, budgets, checkpoints, crash recovery,
memory) can be run and tested offline with exact, repeatable behavior, and so the 30 tasks can be judged by calendar
end state without a model key. A real model replaces it by changing `MODEL_PROVIDER`.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from typing import Any

from scheduling_agent.domain.llm import ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage
from scheduling_agent.domain.memory import Constraints, parse_statement

_DAY = r"(\d{4}-\d{2}-\d{2})"
_BOOK = re.compile(
    rf"book an? (\d+)-minute meeting with (.+?) on {_DAY}(?: after (\d{{2}}:\d{{2}}))?(?: before (\d{{2}}:\d{{2}}))?",
    re.I,
)
_FIND = re.compile(
    rf"find the earliest (\d+)-minute slot for (.+?) between {_DAY} and {_DAY}(?: after (\d{{2}}:\d{{2}}))?", re.I
)
_MOVE = re.compile(
    rf"move event (ev-\d+) to the earliest free slot between {_DAY} and {_DAY}(?: after (\d{{2}}:\d{{2}}))?", re.I
)
_CANCEL = re.compile(r"cancel event (ev-\d+)", re.I)
Decision = tuple[tuple[str, dict[str, Any]] | None, str]
_MEMORY_LINE = re.compile(r"^- (\w+): (.+?) \(said (\d{4}-\d{2}-\d{2}), session (\S+)\)$", re.M)


def _names(text: str) -> list[str]:
    return [n.lower() for n in re.split(r",\s*|\s+and\s+", text.strip()) if n.strip()]


def _constraints(first_message: str, people: list[str]) -> Constraints:
    facts = []
    for match in _MEMORY_LINE.finditer(first_message):
        person, said, stated, session = match.groups()
        fact = parse_statement(person, said, session, date.fromisoformat(stated))
        if fact:
            facts.append(fact)
    return Constraints.from_facts(facts, people)


class ScriptedPolicyModel:
    """Reads the task and the tool results in the conversation and decides the next tool call or the final answer."""

    @property
    def name(self) -> str:
        return "scripted-policy"

    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        messages = request.messages
        first = messages[0].content
        task = first.split("\n\nWhat people told you earlier")[0].strip()
        turns = sum(1 for m in messages if m.role is Role.ASSISTANT)
        results = [json.loads(m.content) for m in messages if m.role is Role.TOOL]
        call, text = self._decide(task, first, turns, results)
        calls = (ToolCall(f"call_{turns + 1}", call[0], call[1]),) if call else ()
        tokens_in = 30 + sum(len(m.content) for m in messages) // 4
        tokens_out = 25 if calls else max(8, len(text) // 4)
        return ChatResponse(
            text,
            StopReason.TOOL_CALLS if calls else StopReason.END,
            Usage(tokens_in, tokens_out),
            0.001,
            self.name,
            calls,
        )

    def _decide(
        self, task: str, first: str, turns: int, results: list[dict[str, Any]]
    ) -> tuple[tuple[str, dict[str, Any]] | None, str]:
        if match := _BOOK.search(task):
            minutes, people_text, day, after, before = match.groups()
            return self._book(
                first,
                _names(people_text),
                int(minutes),
                day,
                day,
                after,
                before,
                turns,
                results,
                persistent="do not give up" in task.lower(),
            )
        if match := _FIND.search(task):
            minutes, people_text, first_day, last_day, after = match.groups()
            return self._book(
                first,
                _names(people_text),
                int(minutes),
                first_day,
                last_day,
                after,
                None,
                turns,
                results,
                persistent=False,
            )
        if match := _MOVE.search(task):
            return self._move(first, match.group(1), match.group(2), match.group(3), match.group(4), turns, results)
        if match := _CANCEL.search(task):
            return self._cancel(match.group(1), turns, results)
        return None, "I did not understand the task, so I changed nothing."

    def _book(
        self,
        first: str,
        people: list[str],
        minutes: int,
        first_day: str,
        last_day: str,
        after: str | None,
        before: str | None,
        turns: int,
        results: list[dict[str, Any]],
        persistent: bool,
    ) -> Decision:
        constraints = _constraints(first, people)
        floors = [t for t in (time.fromisoformat(after) if after else None, constraints.not_before) if t]
        ceilings = [t for t in (time.fromisoformat(before) if before else None, constraints.not_after) if t]
        start_day = date.fromisoformat(first_day)
        end_day = date.fromisoformat(last_day)
        while start_day <= end_day and start_day.weekday() in constraints.avoid_weekdays:
            start_day += timedelta(days=1)
        last = results[-1] if results else None
        searching = last is None or (persistent and ("error" in last or ("slots" in last and not last["slots"])))
        if searching:
            shift = timedelta(days=7 * turns) if persistent else timedelta(0)
            args: dict[str, Any] = {
                "people": people,
                "first_day": (start_day + shift).isoformat(),
                "last_day": (max(start_day, end_day) + shift).isoformat(),
                "minutes": minutes,
            }
            if floors:
                args["not_before"] = f"{max(floors):%H:%M}"
            if ceilings:
                args["not_after"] = f"{min(ceilings):%H:%M}"
            return ("find_free_slots", args), ""
        assert last is not None
        if "error" in last:
            return None, f"I could not book it and changed nothing: {last['error']}"
        if "slots" in last:
            fitting = [
                x for x in last["slots"] if datetime.fromisoformat(x).weekday() not in constraints.avoid_weekdays
            ]
            if not fitting:
                return None, "There is no free slot that fits, so I changed nothing."
            return ("book_meeting", {"people": people, "start": fitting[0], "minutes": minutes}), ""
        if last.get("status") == "booked":
            return None, f"Booked event {last['event_id']}."
        return None, f"The booking did not happen ({last.get('status') or last.get('error')}), so nothing changed."

    def _move(
        self,
        first: str,
        event_id: str,
        first_day: str,
        last_day: str,
        after: str | None,
        turns: int,
        results: list[dict[str, Any]],
    ) -> Decision:
        if turns == 0:
            return ("get_event", {"event_id": event_id}), ""
        if "error" in results[0]:
            return None, f"I could not find that event and changed nothing: {results[0]['error']}"
        event = results[0]
        if turns == 1:
            constraints = _constraints(first, event["people"])
            floor = time.fromisoformat(after) if after else None
            if constraints.not_before and (floor is None or constraints.not_before > floor):
                floor = constraints.not_before
            args: dict[str, Any] = {
                "people": event["people"],
                "first_day": first_day,
                "last_day": last_day,
                "minutes": event["minutes"],
            }
            if floor:
                args["not_before"] = f"{floor:%H:%M}"
            return ("find_free_slots", args), ""
        if turns == 2:
            avoid = _constraints(first, event["people"]).avoid_weekdays
            fitting = [x for x in results[1].get("slots", []) if datetime.fromisoformat(x).weekday() not in avoid]
            if not fitting:
                return None, "There is no free slot that fits, so I changed nothing."
            return ("move_meeting", {"event_id": event_id, "new_start": fitting[0]}), ""
        last = results[-1]
        return None, (
            f"Moved {event_id}; the new event is {last['event_id']}."
            if last.get("status") == "moved"
            else f"The move did not happen ({last.get('status') or last.get('error')})."
        )

    def _cancel(self, event_id: str, turns: int, results: list[dict[str, Any]]) -> Decision:
        if turns == 0:
            return ("get_event", {"event_id": event_id}), ""
        if "error" in results[0]:
            return None, f"I could not find that event and changed nothing: {results[0]['error']}"
        if turns == 1:
            return ("cancel_meeting", {"event_id": event_id}), ""
        last = results[-1]
        return None, (
            f"Cancelled {event_id}."
            if last.get("status") == "cancelled"
            else f"The cancellation did not happen ({last.get('status') or last.get('error')})."
        )
