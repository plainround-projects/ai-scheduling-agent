"""A task for the agent and the calendar end state it must reach."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.errors import DomainError

EventKey = tuple[tuple[str, ...], str, int]


class InvalidTasks(DomainError):
    """The task file breaks a rule of the lesson."""


class TaskKind(StrEnum):
    """The five kinds of task in the set."""

    BOOK = "book"
    RESCHEDULE = "reschedule"
    FIND_SLOT = "find_slot"
    CANCEL = "cancel"
    IMPOSSIBLE = "impossible"


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """A task in words, what people told the agent earlier, and the changes to the calendar it should end with.

    `add` lists the events that should exist afterwards as (people, start, minutes) keys; `remove` lists the ids of the
    seeded events that should be cancelled. The end state is the seeded calendar with those changes applied.
    """

    id: str
    kind: TaskKind
    text: str
    facts: tuple[tuple[str, str], ...]
    add: tuple[EventKey, ...]
    remove: tuple[str, ...]

    @classmethod
    def from_json(cls, row: Mapping[str, Any]) -> TaskSpec:
        return cls(
            id=str(row["id"]),
            kind=TaskKind(row["kind"]),
            text=str(row["text"]),
            facts=tuple((str(p), str(t)) for p, t in row.get("facts", [])),
            add=tuple((tuple(a["people"]), str(a["start"]), int(a["minutes"])) for a in row.get("add", [])),
            remove=tuple(str(r) for r in row.get("remove", [])),
        )


def validate_tasks(tasks: Sequence[TaskSpec]) -> None:
    """The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete."""
    ids = [t.id for t in tasks]
    if len(set(ids)) != len(ids):
        raise InvalidTasks("task ids must be unique")
    want = {
        TaskKind.BOOK: 12,
        TaskKind.RESCHEDULE: 6,
        TaskKind.FIND_SLOT: 4,
        TaskKind.CANCEL: 4,
        TaskKind.IMPOSSIBLE: 4,
    }
    have = {kind: sum(t.kind is kind for t in tasks) for kind in TaskKind}
    if have != want:
        raise InvalidTasks(f"expected {dict(want)}, found {dict(have)}")
    for task in tasks:
        if task.kind is TaskKind.IMPOSSIBLE and (task.add or task.remove):
            raise InvalidTasks(f"{task.id}: a task that must not complete changes nothing")


def expected_end_state(seed: Collection[Event], task: TaskSpec) -> set[EventKey]:
    """The seeded calendar with the task's removals and additions applied, as comparable keys."""
    removed = set(task.remove)
    kept = {e.key() for e in seed if e.id not in removed and not e.cancelled}
    return kept | set(task.add)


def end_state(active: Collection[Event]) -> set[EventKey]:
    """The calendar's real state as comparable keys."""
    return {e.key() for e in active}
