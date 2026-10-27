"""Write data/tasks.jsonl: 30 tasks, each with the calendar end state it should reach.

12 bookings, 6 reschedules, 4 "find a slot for all of us", 4 cancellations and 4 that must not complete (a person
outside the calendar, a slot that does not exist), where the right end state is the unchanged calendar.
Expected changes come from the calendar's own free-slot search over the seeded data, so a change to the seed
regenerates the expectations (run this script again). 10 tasks come with facts told in an earlier session.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from scheduling_agent.domain.memory import Constraints, compact, parse_statement
from scheduling_agent.infrastructure.calendar_db import SqliteCalendar
from scheduling_agent.infrastructure.sqlite import apply_sql, connect

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 10, 27)


def calendar() -> SqliteCalendar:
    db = connect(":memory:")
    apply_sql(db, ROOT / "sql/calendar/001_schema.sql", ROOT / "sql/calendar/002_seed.sql")
    return SqliteCalendar(db)


def constraints(facts: list[tuple[str, str]], people: list[str]) -> Constraints:
    stored: list = []
    for person, statement in facts:
        fact = parse_statement(person, statement, "earlier", TODAY)
        assert fact is not None, statement
        stored = compact([f for f in stored if f.person == person], fact, TODAY) + [
            f for f in stored if f.person != person
        ]
    return Constraints.from_facts(stored, people)


def first_slot(cal, people, first_day, last_day, minutes, after, before, facts):
    c = constraints(facts, people)
    floors = [t for t in (time.fromisoformat(after) if after else None, c.not_before) if t]
    ceilings = [t for t in (time.fromisoformat(before) if before else None, c.not_after) if t]
    start = date.fromisoformat(first_day)
    end = date.fromisoformat(last_day)
    while start <= end and start.weekday() in c.avoid_weekdays:
        start += timedelta(days=1)
    slots = cal.free_slots(
        people, start, end, minutes, max(floors) if floors else None, min(ceilings) if ceilings else None
    )
    slots = [s for s in slots if s.weekday() not in c.avoid_weekdays]
    assert slots, (people, first_day, last_day, minutes, after, before, facts)
    return slots[0]


def key(people, start: datetime, minutes: int) -> dict:
    return {"people": sorted(people), "start": start.isoformat(timespec="minutes"), "minutes": minutes}


def names(people: list[str]) -> str:
    return people[0] if len(people) == 1 else ", ".join(people[:-1]) + " and " + people[-1]


def main() -> None:
    cal = calendar()
    seed = {e.id: e for e in cal.active_events()}
    tasks: list[dict] = []

    def book(i, people, minutes, day, after=None, before=None, facts=()):
        facts = list(facts)
        text = (
            f"Book a {minutes}-minute meeting with {names(people)} on {day}"
            + (f" after {after}" if after else "")
            + (f" before {before}" if before else "")
            + "."
        )
        start = first_slot(cal, people, day, day, minutes, after, before, facts)
        tasks.append(
            {
                "id": f"t-book-{i:02d}",
                "kind": "book",
                "text": text,
                "facts": facts,
                "add": [key(people, start, minutes)],
                "remove": [],
            }
        )

    book(1, ["alice", "bob"], 30, "2026-11-03", facts=[("alice", "I never want meetings before 10")])
    book(2, ["carol", "dave"], 60, "2026-11-04", after="13:00")
    book(3, ["alice", "erin"], 30, "2026-11-05")
    book(4, ["bob", "carol", "dave"], 30, "2026-11-06", after="14:00", facts=[("dave", "No meetings before 15")])
    book(
        5,
        ["alice", "erin"],
        60,
        "2026-11-09",
        facts=[("alice", "no meetings before 9"), ("alice", "Actually, nothing before 11 from now on")],
    )
    book(6, ["dave", "erin"], 30, "2026-11-10", after="09:00")
    book(7, ["carol", "erin"], 30, "2026-11-11", before="12:00")
    book(8, ["alice", "bob", "carol"], 30, "2026-11-12", after="15:00", facts=[("alice", "Nothing before 16")])
    book(9, ["bob", "dave"], 60, "2026-11-03", after="10:30")
    book(10, ["erin"], 30, "2026-11-04")
    book(11, ["alice", "carol"], 90, "2026-11-09", after="09:30")
    book(12, ["bob", "erin"], 30, "2026-11-10", facts=[("erin", "No meetings before 10:30")])

    def find(i, people, minutes, first_day, last_day, after=None, facts=()):
        facts = list(facts)
        text = (
            f"Find the earliest {minutes}-minute slot for {names(people)} between {first_day} and {last_day}"
            + (f" after {after}" if after else "")
            + " and book it."
        )
        start = first_slot(cal, people, first_day, last_day, minutes, after, None, facts)
        tasks.append(
            {
                "id": f"t-find-{i:02d}",
                "kind": "find_slot",
                "text": text,
                "facts": facts,
                "add": [key(people, start, minutes)],
                "remove": [],
            }
        )

    find(1, ["alice", "bob", "carol"], 60, "2026-11-02", "2026-11-04")
    find(
        2,
        ["bob", "carol", "dave"],
        30,
        "2026-11-05",
        "2026-11-06",
        after="13:00",
        facts=[("carol", "No meetings on Thursdays")],
    )
    find(3, ["alice", "dave", "erin"], 60, "2026-11-09", "2026-11-11", facts=[("dave", "nothing before 10")])
    find(4, ["alice", "bob", "carol", "dave"], 30, "2026-11-12", "2026-11-13", after="10:00")

    def move(i, event_id, first_day, last_day, after=None, facts=()):
        facts = list(facts)
        event = seed[event_id]
        text = (
            f"Move event {event_id} to the earliest free slot between {first_day} and {last_day}"
            + (f" after {after}" if after else "")
            + "."
        )
        start = first_slot(cal, list(event.people), first_day, last_day, event.minutes, after, None, facts)
        tasks.append(
            {
                "id": f"t-move-{i:02d}",
                "kind": "reschedule",
                "text": text,
                "facts": facts,
                "add": [key(list(event.people), start, event.minutes)],
                "remove": [event_id],
            }
        )

    by_day = sorted(seed.values(), key=lambda e: (e.start, e.id))
    week1 = [e for e in by_day if e.start.date() <= date(2026, 11, 6)]
    week2 = [e for e in by_day if e.start.date() > date(2026, 11, 6)]
    picks = [week1[1], week1[3], week1[5], week1[7], week1[9], week1[11]]
    windows = [
        ("2026-11-09", "2026-11-10"),
        ("2026-11-09", "2026-11-11"),
        ("2026-11-10", "2026-11-12"),
        ("2026-11-11", "2026-11-12"),
        ("2026-11-12", "2026-11-13"),
        ("2026-11-09", "2026-11-13"),
    ]
    afters = [None, "13:00", None, "14:00", None, "15:00"]
    fact_sets = [
        [],
        [],
        [(picks[2].people[0], "no meetings before 10")],
        [],
        [(picks[4].people[0], "Nothing before 11")],
        [(picks[5].people[0], "No meetings on Mondays")],
    ]
    for i, (event, (a, b), after, facts) in enumerate(zip(picks, windows, afters, fact_sets, strict=True), start=1):
        move(i, event.id, a, b, after, facts)

    cancels = [week2[0], week2[3], week2[6], week2[9]]
    for i, event in enumerate(cancels, start=1):
        tasks.append(
            {
                "id": f"t-cancel-{i:02d}",
                "kind": "cancel",
                "text": f"Cancel event {event.id}.",
                "facts": [],
                "add": [],
                "remove": [event.id],
            }
        )

    impossible = [
        "Book a 30-minute meeting with zed and alice on 2026-11-04.",
        "Book a 60-minute meeting with alice and mallory on 2026-11-05 after 09:00.",
        "Book a 30-minute meeting with bob and carol on 2026-11-06 after 17:00. Do not give up.",
        "Book a 30-minute meeting with dave and erin on 2026-11-07.",
    ]
    for i, text in enumerate(impossible, start=1):
        tasks.append(
            {"id": f"t-impossible-{i:02d}", "kind": "impossible", "text": text, "facts": [], "add": [], "remove": []}
        )

    assert len(tasks) == 30, len(tasks)
    with_facts = sum(bool(t["facts"]) for t in tasks)
    out = ROOT / "data" / "tasks.jsonl"
    out.write_text("".join(json.dumps(t) + "\n" for t in tasks), encoding="utf-8")
    print(f"wrote {len(tasks)} tasks ({with_facts} with facts told in an earlier session) to {out}")


if __name__ == "__main__":
    main()
