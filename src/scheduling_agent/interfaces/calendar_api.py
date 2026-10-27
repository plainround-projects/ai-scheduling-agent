"""The calendar service over HTTP: free slots, one event, book and cancel with an Idempotency-Key header."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, time
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    CalendarError,
    IdempotencyConflict,
    InvalidSlot,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.calendar_db import SqliteCalendar

_log = logging.getLogger("calendar.http")
_STATUS: dict[type[CalendarError], int] = {
    UnknownEvent: 404,
    UnknownPerson: 404,
    InvalidSlot: 422,
    SlotUnavailable: 409,
    AlreadyCancelled: 409,
    IdempotencyConflict: 409,
}


class BookRequest(BaseModel):
    """The body of POST /events."""

    model_config = ConfigDict(extra="forbid")
    people: Annotated[list[str], Field(min_length=1, max_length=8)]
    start: datetime
    minutes: Annotated[int, Field(ge=1, le=1440)]


def event_json(event: Event) -> dict[str, Any]:
    """An event as the API returns it."""
    return {
        "id": event.id,
        "people": list(event.people),
        "start": event.start.isoformat(timespec="minutes"),
        "minutes": event.minutes,
        "cancelled": event.cancelled,
    }


def create_app(calendar: SqliteCalendar, reset: Callable[[], None] | None = None) -> FastAPI:
    """Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data."""
    app = FastAPI(title="calendar-service", version="0.1.0")

    def fail(error: CalendarError) -> HTTPException:
        status = _STATUS.get(type(error), 400)
        return HTTPException(status_code=status, detail={"error": type(error).__name__, "message": str(error)})

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "people": len(calendar.people())}

    @app.get("/people")
    def people() -> list[str]:
        return calendar.people()

    @app.get("/free-slots")
    def free_slots(
        people: Annotated[list[str], Query(min_length=1)],
        first_day: date,
        last_day: date,
        minutes: Annotated[int, Query(ge=30, le=240)],
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> dict[str, list[str]]:
        try:
            slots = calendar.free_slots(people, first_day, last_day, minutes, not_before, not_after)
        except CalendarError as error:
            raise fail(error) from error
        return {"slots": [s.isoformat(timespec="minutes") for s in slots]}

    @app.get("/events")
    def events() -> list[dict[str, Any]]:
        return [event_json(e) for e in calendar.active_events()]

    @app.get("/events/{event_id}")
    def get_event(event_id: str) -> dict[str, Any]:
        try:
            return event_json(calendar.get_event(event_id))
        except CalendarError as error:
            raise fail(error) from error

    @app.post("/events", status_code=201)
    def book(
        body: BookRequest, response: Response, idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]
    ) -> dict[str, Any]:
        try:
            result = calendar.book(body.people, body.start, body.minutes, idempotency_key)
        except CalendarError as error:
            raise fail(error) from error
        response.status_code = 200 if result.replayed else 201
        _log.info("booked", extra={"fields": {"event_id": result.event.id, "replayed": result.replayed}})
        return {"event": event_json(result.event), "replayed": result.replayed}

    @app.post("/events/{event_id}/cancel")
    def cancel(event_id: str, idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]) -> dict[str, Any]:
        try:
            result = calendar.cancel(event_id, idempotency_key)
        except CalendarError as error:
            raise fail(error) from error
        _log.info("cancelled", extra={"fields": {"event_id": event_id, "replayed": result.replayed}})
        return {"event": event_json(result.event), "replayed": result.replayed}

    if reset is not None:

        @app.post("/admin/reset")
        def admin_reset() -> dict[str, str]:
            reset()
            return {"status": "reseeded"}

    return app
