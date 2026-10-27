"""Calendar rules: working hours, the half-hour grid, overlaps and the search for free slots."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from scheduling_agent.domain.errors import InvalidSlot

WORK_START = time(9, 0)
WORK_END = time(17, 0)
GRID_MINUTES = 30
MAX_MINUTES = 240

Interval = tuple[datetime, datetime]


@dataclass(frozen=True, slots=True)
class Event:
    """A meeting: who, when and for how long. `cancelled` events no longer block anyone's time."""

    id: str
    people: tuple[str, ...]
    start: datetime
    minutes: int
    cancelled: bool = False

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.minutes)

    def key(self) -> tuple[tuple[str, ...], str, int]:
        """What the end-state check compares: the people, the start and the length (not the generated id)."""
        return (tuple(sorted(self.people)), self.start.isoformat(timespec="minutes"), self.minutes)


def validate_slot(start: datetime, minutes: int) -> None:
    """Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours."""
    if minutes < GRID_MINUTES or minutes > MAX_MINUTES or minutes % GRID_MINUTES:
        raise InvalidSlot(
            f"length must be a multiple of {GRID_MINUTES} minutes between {GRID_MINUTES} and {MAX_MINUTES}"
        )
    if start.weekday() >= 5:
        raise InvalidSlot(f"{start.date()} is a weekend")
    if start.minute % GRID_MINUTES or start.second or start.microsecond:
        raise InvalidSlot("start must be on the half hour")
    if (
        start.time() < WORK_START
        or (start + timedelta(minutes=minutes)).time() > WORK_END
        or (start + timedelta(minutes=minutes)).date() != start.date()
    ):
        raise InvalidSlot(f"outside working hours {WORK_START:%H:%M} to {WORK_END:%H:%M}")


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """True when two half-open intervals share any time."""
    return a_start < b_end and b_start < a_end


def free_slots(
    busy: Mapping[str, Sequence[Interval]],
    people: Sequence[str],
    first_day: date,
    last_day: date,
    minutes: int,
    not_before: time | None = None,
    not_after: time | None = None,
    avoid_weekdays: Collection[int] = (),
) -> list[datetime]:
    """Start times, earliest first, at which every listed person is free for `minutes`.

    Only weekdays, only on the half-hour grid, only inside working hours. `not_before` and `not_after` narrow the
    hours (for example a stated preference); `avoid_weekdays` skips days (Monday is 0).
    """
    slots: list[datetime] = []
    day = first_day
    while day <= last_day:
        if day.weekday() < 5 and day.weekday() not in avoid_weekdays:
            start = datetime.combine(day, max(WORK_START, not_before or WORK_START))
            limit = datetime.combine(day, min(WORK_END, not_after or WORK_END))
            while start + timedelta(minutes=minutes) <= limit:
                end = start + timedelta(minutes=minutes)
                if not any(overlaps(start, end, b0, b1) for person in people for b0, b1 in busy.get(person, ())):
                    slots.append(start)
                start += timedelta(minutes=GRID_MINUTES)
        day += timedelta(days=1)
    return slots
