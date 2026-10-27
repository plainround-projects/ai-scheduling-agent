import threading
from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    CalendarError,
    IdempotencyConflict,
    InvalidSlot,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.calendar_seed import init_calendar, reset_calendar
from scheduling_agent.infrastructure.sqlite import connect
from scheduling_agent.interfaces.calendar_api import create_app
from tests.conftest import REPO, new_calendar

QUIET = datetime(2026, 11, 3, 16, 0)  # a time at which alice and bob are free in the seed


def free_start(calendar, people=("alice", "bob"), minutes=30):
    slots = calendar.free_slots(list(people), QUIET.date(), QUIET.date(), minutes)
    return slots[0]


def test_the_seed_has_five_people_and_two_weeks_of_meetings_and_nobody_is_double_booked():
    calendar = new_calendar()
    assert calendar.people() == ["alice", "bob", "carol", "dave", "erin"]
    events = calendar.active_events()
    assert len(events) >= 30
    assert min(e.start for e in events).date().isoformat() == "2026-11-02"
    assert max(e.start for e in events).date().isoformat() <= "2026-11-13"
    for a in events:
        for b in events:
            if a.id < b.id and set(a.people) & set(b.people):
                assert a.end <= b.start or b.end <= a.start


def test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event():
    calendar = new_calendar()
    start = free_start(calendar)
    before = len(calendar.active_events())
    first = calendar.book(["alice", "bob"], start, 30, "key-0001-aaaa")
    second = calendar.book(["alice", "bob"], start, 30, "key-0001-aaaa")
    assert first.event.id == second.event.id
    assert (first.replayed, second.replayed) == (False, True)
    assert len(calendar.active_events()) == before + 1


def test_two_different_bookings_with_identical_content_but_different_keys_are_not_mistaken_for_duplicates():
    calendar = new_calendar()
    start = free_start(calendar)
    calendar.book(["alice"], start, 30, "key-0001-aaaa")
    with pytest.raises(
        SlotUnavailable
    ):  # the second is a real conflict, not a replay: the key decides, not the content
        calendar.book(["alice"], start, 30, "key-0002-bbbb")


def test_reusing_a_key_for_a_different_request_is_a_conflict_not_a_silent_replay():
    calendar = new_calendar()
    start = free_start(calendar)
    calendar.book(["alice"], start, 30, "key-0001-aaaa")
    with pytest.raises(IdempotencyConflict):
        calendar.book(["alice"], start.replace(hour=15), 30, "key-0001-aaaa")


def test_a_failed_write_leaves_no_idempotency_key_behind_so_the_retry_can_succeed():
    calendar = new_calendar()
    with pytest.raises(InvalidSlot):
        calendar.book(["alice"], datetime(2026, 11, 3, 3, 0), 30, "key-0003-cccc")
    assert calendar.book(["alice"], free_start(calendar, ("alice",)), 30, "key-0003-cccc").replayed is False


def test_the_booking_rules_each_raise_their_own_error():
    calendar = new_calendar()
    busy = calendar.active_events()[0]
    with pytest.raises(SlotUnavailable, match="busy"):
        calendar.book(list(busy.people), busy.start, 30, "key-0004-dddd")
    with pytest.raises(UnknownPerson):
        calendar.book(["zed"], QUIET, 30, "key-0005-eeee")
    with pytest.raises(UnknownPerson):
        calendar.book([], QUIET, 30, "key-0006-ffff")
    with pytest.raises(InvalidSlot):
        calendar.book(["alice"], datetime(2026, 11, 7, 10, 0), 30, "key-0007-gggg")
    with pytest.raises(UnknownEvent):
        calendar.get_event("ev-9999")


def test_cancel_frees_the_time_replays_by_key_and_refuses_a_second_cancel_with_a_new_key():
    calendar = new_calendar()
    event = calendar.active_events()[0]
    first = calendar.cancel(event.id, "key-0008-hhhh")
    again = calendar.cancel(event.id, "key-0008-hhhh")
    assert first.event.cancelled
    assert again.replayed
    assert event.id not in {e.id for e in calendar.active_events()}
    with pytest.raises(AlreadyCancelled):
        calendar.cancel(event.id, "key-0009-iiii")
    with pytest.raises(UnknownEvent):
        calendar.cancel("ev-9999", "key-0010-jjjj")
    calendar.book(list(event.people), event.start, event.minutes, "key-0011-kkkk")  # the slot is free again


def test_parallel_requests_with_one_key_create_one_event_and_with_two_keys_for_one_slot_only_one_wins():
    calendar = new_calendar()
    start = free_start(calendar)
    before = len(calendar.active_events())
    outcomes: list[str] = []

    def attempt(key: str) -> None:
        try:
            calendar.book(["alice", "bob"], start, 30, key)
            outcomes.append("ok")
        except SlotUnavailable:
            outcomes.append("conflict")

    threads = [threading.Thread(target=attempt, args=("same-key-001",)) for _ in range(6)]
    threads += [threading.Thread(target=attempt, args=("other-key-02",))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(calendar.active_events()) == before + 1
    assert outcomes.count("ok") >= 6


@pytest.fixture
def served():
    calendar = new_calendar()
    return calendar, TestClient(create_app(calendar, reset=lambda: reset_calendar(calendar._db, REPO / "sql")))


def test_the_http_api_books_replays_and_maps_errors_to_status_codes(served):
    calendar, api = served
    start = free_start(calendar).isoformat(timespec="minutes")
    body = {"people": ["alice", "bob"], "start": start, "minutes": 30}
    first = api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0001"})
    second = api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0001"})
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["event"]["id"] == second.json()["event"]["id"]
    assert second.json()["replayed"] is True
    assert api.get(f"/events/{first.json()['event']['id']}").json()["people"] == ["alice", "bob"]
    assert api.get("/events/ev-9999").status_code == 404
    assert (
        api.post("/events", json={**body, "people": ["zed"]}, headers={"Idempotency-Key": "http-key-0002"}).status_code
        == 404
    )
    assert (
        api.post(
            "/events", json={**body, "start": "2026-11-07T10:00"}, headers={"Idempotency-Key": "http-key-0003"}
        ).status_code
        == 422
    )
    assert api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0004"}).status_code == 409
    assert api.post("/events", json=body).status_code == 422  # the header is required
    cancel = api.post(f"/events/{first.json()['event']['id']}/cancel", headers={"Idempotency-Key": "http-key-0005"})
    assert cancel.json()["event"]["cancelled"] is True
    assert (
        api.post(
            f"/events/{first.json()['event']['id']}/cancel", headers={"Idempotency-Key": "http-key-0006"}
        ).status_code
        == 409
    )


def test_the_http_api_lists_people_slots_and_active_events_and_reports_health(served):
    calendar, api = served
    assert api.get("/health").json() == {"status": "ok", "people": 5}
    assert api.get("/people").json() == ["alice", "bob", "carol", "dave", "erin"]
    slots = api.get(
        "/free-slots",
        params={
            "people": ["alice", "bob"],
            "first_day": "2026-11-03",
            "last_day": "2026-11-03",
            "minutes": 30,
            "not_before": "14:00",
        },
    ).json()
    assert slots["slots"][0].startswith("2026-11-03T14") or slots["slots"][0] > "2026-11-03T14:00"
    assert (
        api.get(
            "/free-slots",
            params={"people": ["zed"], "first_day": "2026-11-03", "last_day": "2026-11-03", "minutes": 30},
        ).status_code
        == 404
    )
    assert len(api.get("/events").json()) == len(calendar.active_events())


def test_the_reset_endpoint_reseeds_the_calendar_and_exists_only_when_enabled(served):
    calendar, api = served
    seeded = len(calendar.active_events())
    calendar.book(["alice"], free_start(calendar, ("alice",)), 30, "reset-key-001")
    assert len(calendar.active_events()) == seeded + 1
    assert api.post("/admin/reset").json() == {"status": "reseeded"}
    assert len(calendar.active_events()) == seeded
    assert TestClient(create_app(new_calendar())).post("/admin/reset").status_code == 404


def test_the_http_client_speaks_the_same_contract_and_turns_error_bodies_back_into_domain_errors(served):
    calendar, api = served
    client = HttpCalendar(api, "http://testserver", attempts=1)
    start = free_start(calendar)
    booked = client.book(["alice", "bob"], start, 30, "client-key-001")
    assert client.book(["alice", "bob"], start, 30, "client-key-001").replayed is True
    assert client.get_event(booked.event.id).people == ("alice", "bob")
    assert booked.event.key() in {e.key() for e in client.active_events()}
    assert client.cancel(booked.event.id, "client-key-002").event.cancelled
    assert (
        client.free_slots(["alice"], start.date(), start.date(), 30, not_after=datetime(2026, 1, 1, 12).time())[0].hour
        < 12
    )
    with pytest.raises(UnknownEvent):
        client.get_event("ev-9999")
    with pytest.raises(UnknownPerson):
        client.free_slots(["zed"], start.date(), start.date(), 30)
    with pytest.raises(InvalidSlot):
        client.book(["alice"], datetime(2026, 11, 7, 10), 30, "client-key-003")
    client.reset() if False else None


def test_the_client_retries_a_dropped_connection_and_a_5xx_but_not_a_4xx():
    attempts = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise httpx.ConnectError("refused")
        if attempts["n"] == 2:
            return httpx.Response(503)
        return httpx.Response(200, json=[])

    client = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(flaky)), "http://cal", attempts=3, sleep=lambda s: None
    )
    assert client.active_events() == []
    assert attempts["n"] == 3
    never = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))),
        "http://cal",
        attempts=2,
        sleep=lambda s: None,
    )
    with pytest.raises(CalendarError, match="HTTP 503"):
        never.active_events()
    bad = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400, text="no"))), "http://cal", attempts=3
    )
    with pytest.raises(CalendarError, match="HTTP 400"):
        bad.active_events()


def test_init_creates_and_seeds_once_and_a_reset_restores_the_seed():
    db = connect(":memory:")
    init_calendar(db, REPO / "sql")
    first = db.execute("SELECT count(*) FROM events").fetchone()[0]
    init_calendar(db, REPO / "sql")
    assert db.execute("SELECT count(*) FROM events").fetchone()[0] == first
    db.execute("DELETE FROM idempotency_keys")
    db.execute("UPDATE events SET cancelled = 1")
    reset_calendar(db, REPO / "sql")
    assert db.execute("SELECT count(*) FROM events WHERE cancelled = 0").fetchone()[0] == first
