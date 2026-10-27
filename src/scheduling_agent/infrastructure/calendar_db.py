"""The calendar service's storage: events, attendees and idempotency keys in SQLite."""

from __future__ import annotations

import functools
import hashlib
import json
import sqlite3
import threading
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta
from typing import Concatenate

from scheduling_agent.domain.approvals import BookingResult
from scheduling_agent.domain.calendar import Event, Interval, free_slots, overlaps, validate_slot
from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    IdempotencyConflict,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.sqlite import transaction


def _event(connection: sqlite3.Connection, event_id: str) -> Event | None:
    row = connection.execute("SELECT id, start, minutes, cancelled FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        return None
    people = [
        r[0]
        for r in connection.execute("SELECT person FROM event_people WHERE event_id = ? ORDER BY person", (event_id,))
    ]
    return Event(row["id"], tuple(people), datetime.fromisoformat(row["start"]), row["minutes"], bool(row["cancelled"]))


def _request_hash(operation: str, payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps({"op": operation, **payload}, sort_keys=True).encode()).hexdigest()


def _locked[**P, R](method: Callable[Concatenate[SqliteCalendar, P], R]) -> Callable[Concatenate[SqliteCalendar, P], R]:
    """Run a method while holding the calendar's lock."""

    @functools.wraps(method)
    def wrapper(self: SqliteCalendar, *args: P.args, **kwargs: P.kwargs) -> R:
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


class SqliteCalendar:
    """Reads and idempotent writes. Every write and its idempotency key are committed in one transaction."""

    def __init__(self, connection: sqlite3.Connection, now: str = "2026-10-27T00:00") -> None:
        self._db = connection
        self._now = now
        self._lock = threading.RLock()  # one connection, many request threads: calls take turns

    @_locked
    def people(self) -> list[str]:
        return [r[0] for r in self._db.execute("SELECT name FROM people ORDER BY name")]

    @_locked
    def get_event(self, event_id: str) -> Event:
        event = _event(self._db, event_id)
        if event is None:
            raise UnknownEvent(f"no event {event_id}")
        return event

    @_locked
    def active_events(self) -> list[Event]:
        ids = [r[0] for r in self._db.execute("SELECT id FROM events WHERE cancelled = 0 ORDER BY start, id")]
        return [e for i in ids if (e := _event(self._db, i)) is not None]

    @_locked
    def busy(self, people: Sequence[str]) -> dict[str, list[Interval]]:
        known = set(self.people())
        for person in people:
            if person not in known:
                raise UnknownPerson(f"{person} is not on this calendar")
        out: dict[str, list[Interval]] = {p: [] for p in people}
        marks = ",".join("?" for _ in people)
        rows = self._db.execute(
            "SELECT ep.person, e.start, e.minutes FROM events e JOIN event_people ep ON ep.event_id = e.id "
            f"WHERE e.cancelled = 0 AND ep.person IN ({marks})",
            list(people),
        )
        for row in rows:
            start = datetime.fromisoformat(row["start"])
            out[row["person"]].append((start, start + timedelta(minutes=row["minutes"])))
        return out

    @_locked
    def free_slots(
        self,
        people: Sequence[str],
        first_day: date,
        last_day: date,
        minutes: int,
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> list[datetime]:
        return free_slots(self.busy(people), people, first_day, last_day, minutes, not_before, not_after)

    @_locked
    def book(self, people: Sequence[str], start: datetime, minutes: int, idempotency_key: str) -> BookingResult:
        names = sorted(set(people))
        digest = _request_hash(
            "book", {"people": names, "start": start.isoformat(timespec="minutes"), "minutes": minutes}
        )
        with transaction(self._db):
            replay = self._replay(idempotency_key, "book", digest)
            if replay:
                return replay
            validate_slot(start, minutes)
            if not names:
                raise UnknownPerson("a meeting needs at least one person")
            busy = self.busy(names)
            end = start + timedelta(minutes=minutes)
            for person in names:
                if any(overlaps(start, end, b0, b1) for b0, b1 in busy[person]):
                    raise SlotUnavailable(f"{person} is busy at {start:%Y-%m-%d %H:%M}")
            number = self._db.execute(
                "SELECT COALESCE(MAX(CAST(substr(id, 4) AS INTEGER)), 0) + 1 FROM events"
            ).fetchone()[0]
            event_id = f"ev-{number:04d}"
            self._db.execute(
                "INSERT INTO events (id, start, minutes, cancelled, created_at) VALUES (?, ?, ?, 0, ?)",
                (event_id, start.isoformat(timespec="minutes"), minutes, self._now),
            )
            self._db.executemany(
                "INSERT INTO event_people (event_id, person) VALUES (?, ?)", [(event_id, p) for p in names]
            )
            self._db.execute(
                "INSERT INTO idempotency_keys (key, operation, request_hash, event_id, created_at) "
                "VALUES (?, 'book', ?, ?, ?)",
                (idempotency_key, digest, event_id, self._now),
            )
            return BookingResult(self.get_event(event_id), replayed=False)

    @_locked
    def cancel(self, event_id: str, idempotency_key: str) -> BookingResult:
        digest = _request_hash("cancel", {"event_id": event_id})
        with transaction(self._db):
            replay = self._replay(idempotency_key, "cancel", digest)
            if replay:
                return replay
            event = self.get_event(event_id)
            if event.cancelled:
                raise AlreadyCancelled(f"{event_id} is already cancelled")
            self._db.execute("UPDATE events SET cancelled = 1 WHERE id = ?", (event_id,))
            self._db.execute(
                "INSERT INTO idempotency_keys (key, operation, request_hash, event_id, created_at) "
                "VALUES (?, 'cancel', ?, ?, ?)",
                (idempotency_key, digest, event_id, self._now),
            )
            return BookingResult(self.get_event(event_id), replayed=False)

    def _replay(self, key: str, operation: str, digest: str) -> BookingResult | None:
        row = self._db.execute(
            "SELECT operation, request_hash, event_id FROM idempotency_keys WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        if row["operation"] != operation or row["request_hash"] != digest:
            raise IdempotencyConflict("this Idempotency-Key was used for a different request")
        return BookingResult(self.get_event(row["event_id"]), replayed=True)
