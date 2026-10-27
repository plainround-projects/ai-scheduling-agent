# Python source, the data-generating scripts

## What it is

The scripts under `scripts/` are small standalone Python programs. Each one **writes a data file** of the repository (prompts, emails, help-center pages, calendar or order seed data, tasks). They are not part of the installed package and the program never runs them; they exist so the data is reproducible and its rules are visible.

This note walks through every script line by line.

## Why this repository uses it

Synthetic data is only trustworthy when you can see how it was made. A fixed random seed and plain code mean the same command always writes the same file, so the data can be regenerated, audited and changed on purpose. The committed copies are the ones the tests and the measured numbers use.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `scripts/make_calendar_seed.py` | 59 non-blank lines |
| `scripts/make_tasks.py` | 188 non-blank lines |

## How it works underneath

A script starts with its imports, defines the data it draws from (lists of names, templates, rules), builds the records with a *seeded* random generator (`random.Random(seed)`: the same seed gives the same sequence of numbers), checks the result against rules, and writes it with `json.dumps` or plain text. Because nothing depends on the date or the machine, the output is identical every time.

The explanations follow the same format as the source notes.

## Walkthrough of this repository's use

### `scripts/make_calendar_seed.py`

In its own words: "Write sql/calendar/002_seed.sql: five people and two weeks of meetings (Monday 2026-11-02 to Friday 2026-11-13)."

59 non-blank lines; it defines `main`.

`scripts/make_calendar_seed.py`, lines 1 to 14:

```python
"""Write sql/calendar/002_seed.sql: five people and two weeks of meetings (Monday 2026-11-02 to Friday 2026-11-13).

Deterministic: running it twice writes the same file. No two meetings overlap for the same person.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path

PEOPLE = [("alice", "Alice"), ("bob", "Bob"), ("carol", "Carol"), ("dave", "Dave"), ("erin", "Erin")]
FIRST_DAY = date(2026, 11, 2)
DAYS = 10
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `random` (standard library) available.
- Brings in `date`, `datetime`, `timedelta` from the standard library module `datetime`.
- Brings in `Path` from the standard library module `pathlib`.
- Stores a list of 5 item(s) under the name `PEOPLE`.
- Stores the result of calling `date` under the name `FIRST_DAY`.
  - `date` from the standard library module `datetime`.
- Stores the number `10` under the name `DAYS`.

`scripts/make_calendar_seed.py`, lines 15 to 27:

```python
TOPICS = ["Planning", "Review", "Sync", "1:1", "Demo", "Retro"]


def main() -> None:
    rng = random.Random(1102)
    busy: dict[str, list[tuple[datetime, datetime]]] = {name: [] for name, _ in PEOPLE}
    events: list[tuple[str, datetime, int, list[str]]] = []
    day = FIRST_DAY
    number = 0
    while len(events) < 44:
        if day.weekday() < 5:
            for _ in range(rng.randrange(3, 6)):
                minutes = rng.choice([30, 30, 60])
```

- Stores a list of 6 item(s) under the name `TOPICS`.
- Defines the function `main`. It returns nothing (None).
- It takes no parameters.
- Stores the result of calling `random.Random` under the name `rng`.
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Declares `busy` as a dictionary from text to a list of a fixed list of a date and time, a date and time and sets it to a dictionary built by looping.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Declares `events` as a list of a fixed list of text, a date and time, a whole number, a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the value named `FIRST_DAY` under the name `day`.
- Stores the number `0` under the name `number`.
- Loop: the indented lines below repeat as long as `len(events) < 44` is true.
  - `<` means less than.
  - `len` counts the items in a collection (or the characters in text).
- Decision: the indented lines below run only when `day.weekday() < 5` is true.
  - `<` means less than.
  - The method `weekday` of `day`.
- Loop: the indented lines below run once for each item of `range(rng.randrange(3, 6))`; `_` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - The method `randrange` of `rng`.
- Stores the result of calling `rng.choice` under the name `minutes`.
  - The method `choice` of `rng`.

`scripts/make_calendar_seed.py`, lines 28 to 41:

```python
                start = datetime.combine(day, datetime.min.time()) + timedelta(
                    hours=9, minutes=30 * rng.randrange(0, 15)
                )
                end = start + timedelta(minutes=minutes)
                if end.hour > 17 or (end.hour == 17 and end.minute > 0):
                    continue
                people = sorted(rng.sample([n for n, _ in PEOPLE], rng.choice([1, 2, 2, 3])))
                if any(b0 < end and start < b1 for p in people for b0, b1 in busy[p]):
                    continue
                for p in people:
                    busy[p].append((start, end))
                number += 1
                events.append((f"ev-{number:04d}", start, minutes, people))
        day += timedelta(days=1)
```

- Stores the result of `datetime.combine(day, datetime.min.time()) + timedelta(ho...` under the name `start`.
  - `+` is add.
  - `datetime.combine` from the standard library module `datetime`.
  - `timedelta` from the standard library module `datetime`.
  - `datetime.min.time` from the standard library module `datetime`.
  - `*` is multiply.
  - The method `randrange` of `rng`.
- Stores the result of `start + timedelta(minutes=minutes)` under the name `end`.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Decision: the indented lines below run only when `end.hour > 17 or (end.hour == 17 and end.minute > 0)` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `>` means greater than.
  - `==` means equal.
- Skips the rest of this round of the loop and starts the next.
- Stores the result of calling `sorted` under the name `people`.
  - `sorted` returns a new list with the items in order.
  - The method `sample` of `rng`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `choice` of `rng`.
- Decision: the indented lines below run only when `any((b0 < end and start < b1 for p in people for b0, b1 in busy[p]))` is true.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Skips the rest of this round of the loop and starts the next.
- Loop: the indented lines below run once for each item of `people`; `p` names the current item.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Updates `number` in place: `+=` applies `+` with the number `1` and stores the result back.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Updates `day` in place: `+=` applies `+` with the result of calling `timedelta` and stores the result back.
  - `timedelta` from the standard library module `datetime`.

`scripts/make_calendar_seed.py`, lines 42 to 43:

```python
        if (day - FIRST_DAY).days >= DAYS + 4:
            break
```

- Decision: the indented lines below run only when `(day - FIRST_DAY).days >= DAYS + 4` is true.
  - `>=` means greater than or equal.
  - `+` is add.
  - `-` is subtract.
- Leaves the loop at once.

`scripts/make_calendar_seed.py`, lines 44 to 60:

```python
    lines = [
        "-- DML: five people and two weeks of existing meetings (generated by scripts/make_calendar_seed.py).",
        "",
        "INSERT INTO people (name, display_name) VALUES",
        ",\n".join(f"    ('{n}', '{d}')" for n, d in PEOPLE) + ";",
        "",
        "INSERT INTO events (id, start, minutes, cancelled, created_at) VALUES",
        ",\n".join(
            f"    ('{i}', '{s:%Y-%m-%dT%H:%M}', {m}, 0, '2026-10-27T00:00')"
            for i, s, m, _ in sorted(events, key=lambda e: e[0])
        )
        + ";",
        "",
        "INSERT INTO event_people (event_id, person) VALUES",
        ",\n".join(f"    ('{i}', '{p}')" for i, _, _, ps in sorted(events, key=lambda e: e[0]) for p in ps) + ";",
        "",
    ]
```

- Stores a list of 11 item(s) under the name `lines`.
  - `+` is add.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sorted` returns a new list with the items in order.
  - `lambda args: expression` is a small unnamed function written inline.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_calendar_seed.py`, lines 61 to 67:

```python
    out = Path(__file__).resolve().parent.parent / "sql" / "calendar" / "002_seed.sql"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(events)} events for {len(PEOPLE)} people to {out}")


if __name__ == "__main__":
    main()
```

- Stores the result of `Path(__file__).resolve().parent.parent / 'sql' / 'calenda...` under the name `out`.
  - `/` is divide.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `main`, a function of this file; the result is not kept.
  - `main`, a function of this file.

### `scripts/make_tasks.py`

In its own words: "Write data/tasks.jsonl: 30 tasks, each with the calendar end state it should reach."

188 non-blank lines; it defines `calendar`, `constraints`, `first_slot`, `key`, `names`, `main`.

`scripts/make_tasks.py`, lines 1 to 13:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `date`, `datetime`, `time`, `timedelta` from the standard library module `datetime`.
- Brings in `Path` from the standard library module `pathlib`.

`scripts/make_tasks.py`, lines 15 to 26:

```python
from scheduling_agent.domain.memory import Constraints, compact, parse_statement
from scheduling_agent.infrastructure.calendar_db import SqliteCalendar
from scheduling_agent.infrastructure.sqlite import apply_sql, connect

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 10, 27)


def calendar() -> SqliteCalendar:
    db = connect(":memory:")
    apply_sql(db, ROOT / "sql/calendar/001_schema.sql", ROOT / "sql/calendar/002_seed.sql")
    return SqliteCalendar(db)
```

- Brings in `Constraints` (What recalled facts mean for a search: earliest start, latest end and weekdays to avoid.), `compact` (The facts to keep after writing `new`.), `parse_statement` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.) from the project module `scheduling_agent.domain.memory`.
- Brings in `SqliteCalendar` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.) from the project module `scheduling_agent.infrastructure.calendar_db`.
- Brings in `apply_sql` (Run SQL script files in the order given (the numbered files under sql/).), `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Stores the `parent` of `Path(__file__).resolve().parent` under the name `ROOT`.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Stores the result of calling `date` under the name `TODAY`.
  - `date` from the standard library module `datetime`.
- Defines the function `calendar`. It returns the project type `SqliteCalendar`.
- It takes no parameters.
- Stores the result of calling `connect` under the name `db`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).
- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 3 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Ends the function and gives back the result of calling `SqliteCalendar` to the caller.
  - `SqliteCalendar` from the project's `scheduling_agent.infrastructure.calendar_db` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.).

`scripts/make_tasks.py`, lines 29 to 40:

```python
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
```

- Defines the function `constraints`. It returns the project type `Constraints`.
- Its parameters:
    - `facts` holds a list of a fixed list of text, text.
    - `people` holds a list of text.
- Declares `stored` as a list and sets it to an empty list.
- Loop: the indented lines below run once for each item of `facts`; `(person, statement)` names the current item.
- Stores the result of calling `parse_statement` under the name `fact`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `fact is not None` is true; if it is not, the test fails with an `AssertionError` and the message `statement`.
  - `is not` means not the same object.
- Stores the result of `compact([f for f in stored if f.person == person], fact, ...` under the name `stored`.
  - `+` is add.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `!=` means not equal.
  - `==` means equal.
- Ends the function and gives back the result of calling `Constraints.from_facts` to the caller.
  - The method `from_facts` of the project's `Constraints` (The strictest constraint of each kind among the facts of the people in the meeting.).
- Defines the function `first_slot`.
- Its parameters:
    - `cal`.
    - `people`.
    - `first_day`.
    - `last_day`.
    - `minutes`.
    - `after`.
    - `before`.
    - `facts`.

`scripts/make_tasks.py`, lines 41 to 53:

```python
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
```

- Stores the result of calling `constraints` under the name `c`.
  - `constraints`, a function of this file.
- Stores a list built by looping under the name `floors`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Stores a list built by looping under the name `ceilings`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Stores the result of calling `date.fromisoformat` under the name `start`.
  - `date.fromisoformat` reads a date from ISO text.
- Stores the result of calling `date.fromisoformat` under the name `end`.
  - `date.fromisoformat` reads a date from ISO text.
- Loop: the indented lines below repeat as long as `start <= end and start.weekday() in c.avoid_weekdays` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<=` means less than or equal.
  - `in` means is contained in.
  - The method `weekday` of `start`.
- Updates `start` in place: `+=` applies `+` with the result of calling `timedelta` and stores the result back.
  - `timedelta` from the standard library module `datetime`.
- Stores the result of calling `cal.free_slots` under the name `slots`.
  - The method `free_slots` of `cal`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `max` picks the largest value.
  - `min` picks the smallest value.
- Stores a list built by looping under the name `slots`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not in` means is not contained in.
  - The method `weekday` of `s`.
- Checks that `slots` is true; if it is not, the test fails with an `AssertionError` and the message `(people, first_day, last_day, minutes...`.
- Ends the function and gives back the part of `slots` picked by `0` to the caller.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_tasks.py`, lines 56 to 67:

```python
def key(people, start: datetime, minutes: int) -> dict:
    return {"people": sorted(people), "start": start.isoformat(timespec="minutes"), "minutes": minutes}


def names(people: list[str]) -> str:
    return people[0] if len(people) == 1 else ", ".join(people[:-1]) + " and " + people[-1]


def main() -> None:
    cal = calendar()
    seed = {e.id: e for e in cal.active_events()}
    tasks: list[dict] = []
```

- Defines the function `key`. It returns a dictionary.
- Its parameters:
    - `people`.
    - `start` holds a date and time.
    - `minutes` holds a whole number.
- Ends the function and gives back a dictionary with 3 entries to the caller.
  - `sorted` returns a new list with the items in order.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Defines the function `names`. It returns text.
- Its parameters:
    - `people` holds a list of text.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Defines the function `main`. It returns nothing (None).
- It takes no parameters.
- Stores the result of calling `calendar` under the name `cal`.
  - `calendar`, a function of this file.
- Stores a dictionary built by looping under the name `seed`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `cal`.
- Declares `tasks` as a list of a dictionary and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_tasks.py`, lines 69 to 77:

```python
    def book(i, people, minutes, day, after=None, before=None, facts=()):
        facts = list(facts)
        text = (
            f"Book a {minutes}-minute meeting with {names(people)} on {day}"
            + (f" after {after}" if after else "")
            + (f" before {before}" if before else "")
            + "."
        )
        start = first_slot(cal, people, day, day, minutes, after, before, facts)
```

- Defines the function `book`.
- Its parameters:
    - `i`.
    - `people`.
    - `minutes`.
    - `day`.
    - `after`; if the caller leaves it out it is nothing (`None`).
    - `before`; if the caller leaves it out it is nothing (`None`).
    - `facts`; if the caller leaves it out it is a tuple of 0 item(s).
- Stores the result of calling `list` under the name `facts`.
  - `list` makes a list (a copy when given a collection).
- Stores the result of `f'Book a {minutes}-minute meeting with {names(people)} on...` under the name `text`.
  - `+` is add.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `names`, a function of this file.
- Stores the result of calling `first_slot` under the name `start`.
  - `first_slot`, a function of this file.

`scripts/make_tasks.py`, lines 78 to 91:

```python
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
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `key`, a function of this file.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 4 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.

`scripts/make_tasks.py`, lines 92 to 105:

```python
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
```

- Calls `book`, a function defined in this file or passed in with 6 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 6 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 4 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.

`scripts/make_tasks.py`, lines 106 to 115:

```python
    book(12, ["bob", "erin"], 30, "2026-11-10", facts=[("erin", "No meetings before 10:30")])

    def find(i, people, minutes, first_day, last_day, after=None, facts=()):
        facts = list(facts)
        text = (
            f"Find the earliest {minutes}-minute slot for {names(people)} between {first_day} and {last_day}"
            + (f" after {after}" if after else "")
            + " and book it."
        )
        start = first_slot(cal, people, first_day, last_day, minutes, after, None, facts)
```

- Calls `book`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `book`, a function defined in this file or passed in.
- Defines the function `find`.
- Its parameters:
    - `i`.
    - `people`.
    - `minutes`.
    - `first_day`.
    - `last_day`.
    - `after`; if the caller leaves it out it is nothing (`None`).
    - `facts`; if the caller leaves it out it is a tuple of 0 item(s).
- Stores the result of calling `list` under the name `facts`.
  - `list` makes a list (a copy when given a collection).
- Stores the result of `f'Find the earliest {minutes}-minute slot for {names(peop...` under the name `text`.
  - `+` is add.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `names`, a function of this file.
- Stores the result of calling `first_slot` under the name `start`.
  - `first_slot`, a function of this file.

`scripts/make_tasks.py`, lines 116 to 127:

```python
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
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `key`, a function of this file.
- Calls `find`, a function defined in this file or passed in with 5 argument(s); the result is not kept.
  - `find`, a function defined in this file or passed in.

`scripts/make_tasks.py`, lines 128 to 141:

```python
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
```

- Calls `find`, a function defined in this file or passed in with 7 argument(s); the result is not kept.
  - `find`, a function defined in this file or passed in.
- Calls `find`, a function defined in this file or passed in with 6 argument(s); the result is not kept.
  - `find`, a function defined in this file or passed in.
- Calls `find`, a function defined in this file or passed in with 6 argument(s); the result is not kept.
  - `find`, a function defined in this file or passed in.
- Defines the function `move`.
- Its parameters:
    - `i`.
    - `event_id`.
    - `first_day`.
    - `last_day`.
    - `after`; if the caller leaves it out it is nothing (`None`).
    - `facts`; if the caller leaves it out it is a tuple of 0 item(s).
- Stores the result of calling `list` under the name `facts`.
  - `list` makes a list (a copy when given a collection).

`scripts/make_tasks.py`, lines 142 to 148:

```python
        event = seed[event_id]
        text = (
            f"Move event {event_id} to the earliest free slot between {first_day} and {last_day}"
            + (f" after {after}" if after else "")
            + "."
        )
        start = first_slot(cal, list(event.people), first_day, last_day, event.minutes, after, None, facts)
```

- Stores the part of `seed` picked by `event_id` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of `f'Move event {event_id} to the earliest free slot between...` under the name `text`.
  - `+` is add.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Stores the result of calling `first_slot` under the name `start`.
  - `first_slot`, a function of this file.
  - `list` makes a list (a copy when given a collection).

`scripts/make_tasks.py`, lines 149 to 162:

```python
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
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `key`, a function of this file.
  - `list` makes a list (a copy when given a collection).
- Stores the result of calling `sorted` under the name `by_day`.
  - `sorted` returns a new list with the items in order.
  - `.values(...)` gives the values of a dictionary.
  - `lambda args: expression` is a small unnamed function written inline.
- Stores a list built by looping under the name `week1`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<=` means less than or equal.
  - The method `date` of `e.start`.
  - `date` from the standard library module `datetime`.
- Stores a list built by looping under the name `week2`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `>` means greater than.
  - The method `date` of `e.start`.
  - `date` from the standard library module `datetime`.

`scripts/make_tasks.py`, lines 163 to 172:

```python
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
```

- Stores a list of 6 item(s) under the name `picks`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a list of 6 item(s) under the name `windows`.
- Stores a list of 6 item(s) under the name `afters`.

`scripts/make_tasks.py`, lines 173 to 185:

```python
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
```

- Stores a list of 6 item(s) under the name `fact_sets`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `enumerate(zip(picks, windows, afters, fact_sets, strict=T...`; `(i, (event, (a, b), after, ...` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `zip` walks several collections side by side, item by item.
- Calls `move`, a function defined in this file or passed in with 6 argument(s); the result is not kept.
  - `move`, a function defined in this file or passed in.
- Stores a list of 4 item(s) under the name `cancels`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `enumerate(cancels, start=1)`; `(i, event)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).

`scripts/make_tasks.py`, lines 186 to 195:

```python
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
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`scripts/make_tasks.py`, lines 197 to 209:

```python
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
```

- Stores a list of 4 item(s) under the name `impossible`.
- Loop: the indented lines below run once for each item of `enumerate(impossible, start=1)`; `(i, text)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `len(tasks) == 30` is true; if it is not, the test fails with an `AssertionError` and the message `len(tasks)`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of calling `sum` under the name `with_facts`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `bool` turns a value into true or false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_tasks.py`, lines 210 to 216:

```python
    out = ROOT / "data" / "tasks.jsonl"
    out.write_text("".join(json.dumps(t) + "\n" for t in tasks), encoding="utf-8")
    print(f"wrote {len(tasks)} tasks ({with_facts} with facts told in an earlier session) to {out}")


if __name__ == "__main__":
    main()
```

- Stores the result of `ROOT / 'data' / 'tasks.jsonl'` under the name `out`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `main`, a function of this file; the result is not kept.
  - `main`, a function of this file.

## Try it yourself

1. Check that `scripts/make_calendar_seed.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_calendar_seed.py && echo 'compiles: scripts/make_calendar_seed.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_calendar_seed.py
```

2. Check that `scripts/make_tasks.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_tasks.py && echo 'compiles: scripts/make_tasks.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_tasks.py
```

## Mistakes people make

- **Editing a generated file by hand.** The next run of the script would overwrite it. Change the script and run it again.
- **Using unseeded randomness.** Two runs would differ. The scripts create `random.Random(seed)` objects.
- **Letting the script read the clock.** A date inside the output would change every day; the scripts use fixed dates.
- **Forgetting to commit the output.** The tests read the committed file, not a fresh one.

## Check yourself

1. What does `scripts/make_calendar_seed.py` do?

   *Answer:* Write sql/calendar/002_seed.sql: five people and two weeks of meetings (Monday 2026-11-02 to Friday 2026-11-13).

2. What does `scripts/make_tasks.py` do?

   *Answer:* Write data/tasks.jsonl: 30 tasks, each with the calendar end state it should reach.

3. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

4. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

5. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

## Further reading

- Python `random` module, https://docs.python.org/3/library/random.html (Python 3.13).
