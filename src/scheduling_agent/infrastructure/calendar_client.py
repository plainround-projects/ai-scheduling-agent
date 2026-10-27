"""The calendar service as seen from the agent: an HTTP client with timeouts, retries and an Idempotency-Key header."""

from __future__ import annotations

import time as time_module
from collections.abc import Callable, Sequence
from datetime import date, datetime, time
from typing import Any

import httpx

from scheduling_agent.domain.approvals import BookingResult
from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    CalendarError,
    CalendarUnavailable,
    IdempotencyConflict,
    InvalidSlot,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.retry import retry

_ERRORS: dict[str, type[CalendarError]] = {
    "UnknownEvent": UnknownEvent,
    "UnknownPerson": UnknownPerson,
    "InvalidSlot": InvalidSlot,
    "SlotUnavailable": SlotUnavailable,
    "AlreadyCancelled": AlreadyCancelled,
    "IdempotencyConflict": IdempotencyConflict,
}


def _event(data: dict[str, Any]) -> Event:
    return Event(
        data["id"], tuple(data["people"]), datetime.fromisoformat(data["start"]), data["minutes"], data["cancelled"]
    )


class HttpCalendar:
    """Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key."""

    def __init__(
        self,
        http: httpx.Client,
        base_url: str,
        attempts: int = 3,
        base_delay_seconds: float = 0.2,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._http = http
        self._base = base_url.rstrip("/")
        self._attempts = attempts
        self._delay = base_delay_seconds
        self._sleep = sleep

    def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        def once() -> dict[str, Any] | list[Any]:
            try:
                reply = self._http.request(method, f"{self._base}{path}", **kwargs)
            except httpx.TransportError as error:
                raise CalendarUnavailable(f"{type(error).__name__}: {error}") from error
            if reply.status_code >= 500:
                raise CalendarUnavailable(f"HTTP {reply.status_code}")
            if reply.status_code >= 400:
                detail = (
                    reply.json().get("detail", {})
                    if reply.headers.get("content-type", "").startswith("application/json")
                    else {}
                )
                if isinstance(detail, dict) and detail.get("error") in _ERRORS:
                    raise _ERRORS[detail["error"]](detail.get("message", ""))
                raise CalendarError(f"HTTP {reply.status_code}: {reply.text[:200]}")
            body: dict[str, Any] | list[Any] = reply.json()
            return body

        return retry(
            once,
            attempts=self._attempts,
            base_delay_seconds=self._delay,
            retry_on=(CalendarUnavailable,),
            sleep=self._sleep or time_module.sleep,
        )

    def free_slots(
        self,
        people: Sequence[str],
        first_day: date,
        last_day: date,
        minutes: int,
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> list[datetime]:
        params: dict[str, Any] = {
            "people": list(people),
            "first_day": first_day.isoformat(),
            "last_day": last_day.isoformat(),
            "minutes": minutes,
        }
        if not_before:
            params["not_before"] = not_before.isoformat(timespec="minutes")
        if not_after:
            params["not_after"] = not_after.isoformat(timespec="minutes")
        body = self._call("GET", "/free-slots", params=params)
        assert isinstance(body, dict)
        return [datetime.fromisoformat(s) for s in body["slots"]]

    def get_event(self, event_id: str) -> Event:
        body = self._call("GET", f"/events/{event_id}")
        assert isinstance(body, dict)
        return _event(body)

    def book(self, people: Sequence[str], start: datetime, minutes: int, idempotency_key: str) -> BookingResult:
        payload = {"people": list(people), "start": start.isoformat(timespec="minutes"), "minutes": minutes}
        body = self._call("POST", "/events", json=payload, headers={"Idempotency-Key": idempotency_key})
        assert isinstance(body, dict)
        return BookingResult(_event(body["event"]), bool(body["replayed"]))

    def cancel(self, event_id: str, idempotency_key: str) -> BookingResult:
        body = self._call("POST", f"/events/{event_id}/cancel", headers={"Idempotency-Key": idempotency_key})
        assert isinstance(body, dict)
        return BookingResult(_event(body["event"]), bool(body["replayed"]))

    def active_events(self) -> list[Event]:
        body = self._call("GET", "/events")
        assert isinstance(body, list)
        return [_event(item) for item in body]

    def reset(self) -> None:
        """Reseed the calendar (needs the service started with resets enabled; a demo and test aid)."""
        self._call("POST", "/admin/reset")
