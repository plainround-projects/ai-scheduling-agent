"""Long-term memory: facts a person states, a write policy that keeps one fact per topic, and recall by score."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, time, timedelta
from enum import StrEnum

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_DAY = r"(" + "|".join(_WEEKDAYS) + r")s?"
_TIME = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
_EARLIEST = re.compile(rf"\b(?:no|nothing|not|never)\b[^.]{{0,30}}?\bbefore\s+{_TIME}", re.IGNORECASE)
_LATEST = re.compile(rf"\b(?:no|nothing|not|never)\b[^.]{{0,30}}?\bafter\s+{_TIME}", re.IGNORECASE)
_AVOID = re.compile(rf"\bno\s+meetings?\s+on\s+{_DAY}\b|\b{_DAY}\s+are\s+(?:off|blocked)\b", re.IGNORECASE)
_ALLOW = re.compile(rf"\b{_DAY}\s+(?:are|is)\s+(?:fine|ok|okay|open)(?:\s+again)?\b", re.IGNORECASE)


class FactKind(StrEnum):
    """What a fact constrains."""

    EARLIEST_START = "earliest_start"
    LATEST_END = "latest_end"
    AVOID_DAY = "avoid_day"
    ALLOW_DAY = "allow_day"


@dataclass(frozen=True, slots=True)
class Fact:
    """Something a person said about their own calendar, with where and when they said it and when it lapses.

    `value` is `HH:MM` for the two time kinds and a weekday number (Monday is 0) for the day kinds.
    """

    person: str
    kind: FactKind
    value: str
    text: str
    session: str
    stated_on: date
    expires_on: date | None = None

    @property
    def topic(self) -> tuple[str, str, str]:
        """Facts with the same topic contradict or repeat each other: one per person, kind and (for days) weekday."""
        day = self.value if self.kind in (FactKind.AVOID_DAY, FactKind.ALLOW_DAY) else ""
        return (self.person, "day" if day else self.kind.value, day)

    def alive(self, today: date) -> bool:
        return self.expires_on is None or self.expires_on >= today


def _clock(hour: str, minute: str | None, meridiem: str | None, assume_afternoon_below: int) -> time:
    h, m = int(hour), int(minute or 0)
    if meridiem:
        h = h % 12 + (12 if meridiem.lower() == "pm" else 0)
    elif h < assume_afternoon_below:
        h += 12
    return time(h, m)


def parse_statement(person: str, text: str, session: str, stated_on: date, ttl_days: int | None = 365) -> Fact | None:
    """Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep."""
    expires = stated_on + timedelta(days=ttl_days) if ttl_days else None
    if match := _EARLIEST.search(text):
        when = _clock(match.group(1), match.group(2), match.group(3), assume_afternoon_below=0)
        return Fact(person, FactKind.EARLIEST_START, f"{when:%H:%M}", text.strip(), session, stated_on, expires)
    if match := _LATEST.search(text):
        when = _clock(match.group(1), match.group(2), match.group(3), assume_afternoon_below=8)
        return Fact(person, FactKind.LATEST_END, f"{when:%H:%M}", text.strip(), session, stated_on, expires)
    if match := _ALLOW.search(text):
        return Fact(
            person, FactKind.ALLOW_DAY, str(_weekday(match.group(1))), text.strip(), session, stated_on, expires
        )
    if match := _AVOID.search(text):
        day = match.group(1) or match.group(2)
        return Fact(person, FactKind.AVOID_DAY, str(_weekday(day)), text.strip(), session, stated_on, expires)
    return None


def _weekday(name: str) -> int:
    return _WEEKDAYS.index(name.lower().rstrip("s"))


def compact(existing: Sequence[Fact], new: Fact, today: date) -> list[Fact]:
    """The facts to keep after writing `new`.

    Lapsed facts are dropped. A fact about the same person and topic is replaced (a changed preference, or a repeat
    that is merged into one). A statement that a day is fine again retracts the avoid-day fact and is not stored.
    """
    kept = [f for f in existing if f.alive(today) and f.topic != new.topic]
    if new.kind is FactKind.ALLOW_DAY:
        return kept
    return [*kept, new]


def recall_score(
    similarity: float, stated_on: date, today: date, half_life_days: float = 180.0, weight: float = 0.7
) -> float:
    """Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`."""
    age = max(0, (today - stated_on).days)
    recency = math.exp(-math.log(2) * age / half_life_days)
    return weight * similarity + (1 - weight) * recency


def rank_facts(scored: Sequence[tuple[Fact, float]], today: date, top: int = 3) -> list[Fact]:
    """The `top` live facts with the best blended score, best first (ties broken by newer first, then text)."""
    live = [(fact, sim) for fact, sim in scored if fact.alive(today)]
    ranked = sorted(
        live,
        key=lambda item: (
            -recall_score(item[1], item[0].stated_on, today),
            -item[0].stated_on.toordinal(),
            item[0].text,
        ),
    )
    return [fact for fact, _ in ranked[:top]]


@dataclass(frozen=True, slots=True)
class Constraints:
    """What recalled facts mean for a search: earliest start, latest end and weekdays to avoid."""

    not_before: time | None = None
    not_after: time | None = None
    avoid_weekdays: frozenset[int] = frozenset()

    @classmethod
    def from_facts(cls, facts: Sequence[Fact], people: Sequence[str]) -> Constraints:
        """The strictest constraint of each kind among the facts of the people in the meeting."""
        mine = [f for f in facts if f.person in people]
        starts = [time.fromisoformat(f.value) for f in mine if f.kind is FactKind.EARLIEST_START]
        ends = [time.fromisoformat(f.value) for f in mine if f.kind is FactKind.LATEST_END]
        days = frozenset(int(f.value) for f in mine if f.kind is FactKind.AVOID_DAY)
        return cls(max(starts) if starts else None, min(ends) if ends else None, days)
