# Python source, the domain layer

## What it is

This note walks through every Python file of the `domain` layer of `scheduling_agent`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **domain** is the core of the program: plain Python objects and functions that hold the rules of the problem (prices, estimates, state changes, validation). It imports nothing from outside the standard library except small helpers, so it can be understood and tested without a network, a database or a web framework.

## Why this repository uses it

The domain is where the project's decisions live, and import-linter forbids it from importing a vendor SDK, an HTTP client, a web framework or a database driver. Reading it first shows what the program *means*; the other layers only connect it to the world.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/__init__.py` | 2 non-blank lines |
| `src/scheduling_agent/domain/__init__.py` | 1 non-blank lines |
| `src/scheduling_agent/domain/approvals.py` | 32 non-blank lines |
| `src/scheduling_agent/domain/budget.py` | 25 non-blank lines |
| `src/scheduling_agent/domain/calendar.py` | 71 non-blank lines |
| `src/scheduling_agent/domain/errors.py` | 37 non-blank lines |
| `src/scheduling_agent/domain/llm.py` | 114 non-blank lines |
| `src/scheduling_agent/domain/memory.py` | 108 non-blank lines |
| `src/scheduling_agent/domain/prompts.py` | 12 non-blank lines |
| `src/scheduling_agent/domain/proposals.py` | 35 non-blank lines |
| `src/scheduling_agent/domain/retrieval.py` | 9 non-blank lines |
| `src/scheduling_agent/domain/run.py` | 43 non-blank lines |
| `src/scheduling_agent/domain/tasks.py` | 66 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/scheduling_agent/__init__.py`

In its own words: "A scheduling agent: approval for every write, budgets, crash-safe resumption and long-term memory."

2 non-blank lines.

`src/scheduling_agent/__init__.py`, lines 1 to 3:

```python
"""A scheduling agent: approval for every write, budgets, crash-safe resumption and long-term memory."""

__version__ = "0.1.0"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `0.1.0` under the name `__version__`.

### `src/scheduling_agent/domain/__init__.py`

In its own words: "Pure domain logic. Depends on nothing outside the standard library."

1 non-blank lines.

`src/scheduling_agent/domain/__init__.py`, lines 1 to 1:

```python
"""Pure domain logic. Depends on nothing outside the standard library."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/scheduling_agent/domain/approvals.py`

In its own words: "Value objects for approvals, audit lines and the result of a calendar write."

32 non-blank lines; it defines `Approval`, `AuditLine`, `BookingResult`.

`src/scheduling_agent/domain/approvals.py`, lines 1 to 14:

```python
"""Value objects for approvals, audit lines and the result of a calendar write."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.proposals import ApprovalStatus, Proposal


@dataclass(frozen=True, slots=True)
class Approval:
    """A proposal and what a person decided about it."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `datetime` from the standard library module `datetime`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Defines the class `Approval`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A proposal and what a person decided about it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/approvals.py`, lines 16 to 28:

```python
    id: str
    run_id: str
    step: int
    proposal: Proposal
    status: ApprovalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None


@dataclass(frozen=True, slots=True)
class AuditLine:
    """One write attempt: refused (no valid approval) or written (with the approval that allowed it)."""
```

- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `run_id` as text; it has no default, so a value must be given when the object is made.
- Declares `step` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `proposal` as the project type `Proposal`; it has no default, so a value must be given when the object is made.
- Declares `status` as the project type `ApprovalStatus`; it has no default, so a value must be given when the object is made.
- Declares `created_at` as a date and time; it has no default, so a value must be given when the object is made.
- Declares `decided_at` as a date and time, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `decided_by` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the class `AuditLine`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One write attempt: refused (no valid approval) or written (with the approval that allowed it)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/approvals.py`, lines 30 to 41:

```python
    at: datetime
    run_id: str
    step: int
    action: str
    outcome: str
    approval_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class BookingResult:
    """What the calendar answered to a write: the event and whether the answer was a replay of an earlier key."""
```

- Declares `at` as a date and time; it has no default, so a value must be given when the object is made.
- Declares `run_id` as text; it has no default, so a value must be given when the object is made.
- Declares `step` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `action` as text; it has no default, so a value must be given when the object is made.
- Declares `outcome` as text; it has no default, so a value must be given when the object is made.
- Declares `approval_id` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `detail` as text; it has no default, so a value must be given when the object is made.
- Defines the class `BookingResult`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What the calendar answered to a write: the event and whether the answer was a replay of an earlier key."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/approvals.py`, lines 43 to 44:

```python
    event: Event
    replayed: bool
```

- Declares `event` as the project type `Event`; it has no default, so a value must be given when the object is made.
- Declares `replayed` as true or false; it has no default, so a value must be given when the object is made.

### `src/scheduling_agent/domain/budget.py`

In its own words: "Budgets around the agent loop: steps, tokens and wall-clock time, each checked on its own."

25 non-blank lines; it defines `Budget`.

`src/scheduling_agent/domain/budget.py`, lines 1 to 14:

```python
"""Budgets around the agent loop: steps, tokens and wall-clock time, each checked on its own."""

from __future__ import annotations

from dataclasses import dataclass

from scheduling_agent.domain.errors import BudgetExceeded


@dataclass(slots=True)
class Budget:
    """Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired."""

    max_steps: int
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `BudgetExceeded` (A run hit one of its caps: steps, tokens or wall-clock time.) from the project module `scheduling_agent.domain.errors`.
- Defines the class `Budget`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `max_steps` as a whole number; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/domain/budget.py`, lines 15 to 28:

```python
    max_tokens: int
    max_seconds: float
    started_at: float
    steps: int = 0
    tokens: int = 0

    def check(self, now: float) -> None:
        """Called before every action: a long tool call between checks can blow the time cap on its own."""
        if self.steps >= self.max_steps:
            raise BudgetExceeded("steps", f"step cap reached: {self.steps}/{self.max_steps}")
        if self.tokens >= self.max_tokens:
            raise BudgetExceeded("tokens", f"token cap reached: {self.tokens}/{self.max_tokens}")
        if now - self.started_at >= self.max_seconds:
            raise BudgetExceeded("seconds", f"time cap reached: {now - self.started_at:.1f}s/{self.max_seconds:g}s")
```

- Declares `max_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `max_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `started_at` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `steps` as a whole number and sets it to the number `0`.
- Declares `tokens` as a whole number and sets it to the number `0`.
- Defines the method `check`. It returns nothing (None). The author's own description: "Called before every action: a long tool call between checks can blow the time cap on its own."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `now` holds a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `self.steps >= self.max_steps` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `BudgetExceeded`. Execution jumps out to the nearest matching `except`.
  - `BudgetExceeded` from the project's `scheduling_agent.domain.errors` (A run hit one of its caps: steps, tokens or wall-clock time.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `self.tokens >= self.max_tokens` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `BudgetExceeded`. Execution jumps out to the nearest matching `except`.
  - `BudgetExceeded` from the project's `scheduling_agent.domain.errors` (A run hit one of its caps: steps, tokens or wall-clock time.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `now - self.started_at >= self.max_seconds` is true.
  - `>=` means greater than or equal.
  - `-` is subtract.
- Raises an error: the result of calling `BudgetExceeded`. Execution jumps out to the nearest matching `except`.
  - `BudgetExceeded` from the project's `scheduling_agent.domain.errors` (A run hit one of its caps: steps, tokens or wall-clock time.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `-` is subtract.

`src/scheduling_agent/domain/budget.py`, lines 30 to 33:

```python
    def spend(self, tokens: int) -> None:
        """Record one step and the tokens it used."""
        self.steps += 1
        self.tokens += tokens
```

- Defines the method `spend`. It returns nothing (None). The author's own description: "Record one step and the tokens it used."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `tokens` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Updates `self.steps` in place: `+=` applies `+` with the number `1` and stores the result back.
- Updates `self.tokens` in place: `+=` applies `+` with the value named `tokens` and stores the result back.

### `src/scheduling_agent/domain/calendar.py`

In its own words: "Calendar rules: working hours, the half-hour grid, overlaps and the search for free slots."

71 non-blank lines; it defines `Event`, `validate_slot`, `overlaps`, `free_slots`.

`src/scheduling_agent/domain/calendar.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Collection`, `Mapping`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `date`, `datetime`, `time`, `timedelta` from the standard library module `datetime`.
- Brings in `InvalidSlot` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.) from the project module `scheduling_agent.domain.errors`.
- Stores the result of calling `time` under the name `WORK_START`.
  - `time` from the standard library module `datetime`.
- Stores the result of calling `time` under the name `WORK_END`.
  - `time` from the standard library module `datetime`.
- Stores the number `30` under the name `GRID_MINUTES`.
- Stores the number `240` under the name `MAX_MINUTES`.

`src/scheduling_agent/domain/calendar.py`, lines 16 to 27:

```python
Interval = tuple[datetime, datetime]


@dataclass(frozen=True, slots=True)
class Event:
    """A meeting: who, when and for how long. `cancelled` events no longer block anyone's time."""

    id: str
    people: tuple[str, ...]
    start: datetime
    minutes: int
    cancelled: bool = False
```

- Stores the part of `tuple` picked by `(datetime, datetime)` under the name `Interval`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `Event`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A meeting: who, when and for how long. `cancelled` events no longer block anyone's time."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `people` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `start` as a date and time; it has no default, so a value must be given when the object is made.
- Declares `minutes` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `cancelled` as true or false and sets it to the value `False`.

`src/scheduling_agent/domain/calendar.py`, lines 29 to 40:

```python
    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.minutes)

    def key(self) -> tuple[tuple[str, ...], str, int]:
        """What the end-state check compares: the people, the start and the length (not the generated id)."""
        return (tuple(sorted(self.people)), self.start.isoformat(timespec="minutes"), self.minutes)


def validate_slot(start: datetime, minutes: int) -> None:
    """Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours."""
    if minutes < GRID_MINUTES or minutes > MAX_MINUTES or minutes % GRID_MINUTES:
```

- Defines the method `end`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of `self.start + timedelta(minutes=self.minutes)` to the caller.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Defines the method `key`. It returns a fixed list of a fixed list of text (any length), text, a whole number. The author's own description: "What the end-state check compares: the people, the start and the length (not the generated id)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a tuple of 3 item(s) to the caller.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `isoformat` on the stored object `self.start`: it writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `sorted` returns a new list with the items in order.
- Defines the function `validate_slot`. It returns nothing (None). The author's own description: "Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours."
- Its parameters:
    - `start` holds a date and time.
    - `minutes` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `minutes < GRID_MINUTES or minutes > MAX_MINUTES or minutes % GRID_M...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `>` means greater than.
  - `%` is remainder.

`src/scheduling_agent/domain/calendar.py`, lines 41 to 53:

```python
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
```

- Raises an error: the result of calling `InvalidSlot`. Execution jumps out to the nearest matching `except`.
  - `InvalidSlot` from the project's `scheduling_agent.domain.errors` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `start.weekday() >= 5` is true.
  - `>=` means greater than or equal.
  - The method `weekday` of `start`.
- Raises an error: the result of calling `InvalidSlot`. Execution jumps out to the nearest matching `except`.
  - `InvalidSlot` from the project's `scheduling_agent.domain.errors` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `date` of `start`.
- Decision: the indented lines below run only when `start.minute % GRID_MINUTES or start.second or start.microsecond` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `%` is remainder.
- Raises an error: the result of calling `InvalidSlot`. Execution jumps out to the nearest matching `except`.
  - `InvalidSlot` from the project's `scheduling_agent.domain.errors` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.).
- Decision: the indented lines below run only when `start.time() < WORK_START or (start + timedelta(minutes=minutes)).t...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `>` means greater than.
  - `!=` means not equal.
  - The method `time` of `start`.
  - The method `time` of `start + timedelta(minutes=minutes)`.
  - The method `date` of `start`.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Raises an error: the result of calling `InvalidSlot`. Execution jumps out to the nearest matching `except`.
  - `InvalidSlot` from the project's `scheduling_agent.domain.errors` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/domain/calendar.py`, lines 56 to 58:

```python
def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """True when two half-open intervals share any time."""
    return a_start < b_end and b_start < a_end
```

- Defines the function `overlaps`. It returns true or false. The author's own description: "True when two half-open intervals share any time."
- Its parameters:
    - `a_start` holds a date and time.
    - `a_end` holds a date and time.
    - `b_start` holds a date and time.
    - `b_end` holds a date and time.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of combining conditions: `a_start < b_end and b_start < a_end` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.

`src/scheduling_agent/domain/calendar.py`, lines 61 to 70:

```python
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
```

- Defines the function `free_slots`. It returns a list of a date and time. The author's own description: "Start times, earliest first, at which every listed person is free for `minutes`."
- Its parameters:
    - `busy` holds anything that behaves like a dictionary from text to anything that behaves like a list of `Interval`.
    - `people` holds anything that behaves like a list of text.
    - `first_day` holds a calendar date.
    - `last_day` holds a calendar date.
    - `minutes` holds a whole number.
    - `not_before` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `not_after` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `avoid_weekdays` holds a collection with a size of a whole number; if the caller leaves it out it is a tuple of 0 item(s).

`src/scheduling_agent/domain/calendar.py`, lines 71 to 84:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `slots` as a list of a date and time and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the value named `first_day` under the name `day`.
- Loop: the indented lines below repeat as long as `day <= last_day` is true.
  - `<=` means less than or equal.
- Decision: the indented lines below run only when `day.weekday() < 5 and day.weekday() not in avoid_weekdays` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `not in` means is not contained in.
  - The method `weekday` of `day`.
- Stores the result of calling `datetime.combine` under the name `start`.
  - `datetime.combine` from the standard library module `datetime`.
  - `max` picks the largest value.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Stores the result of calling `datetime.combine` under the name `limit`.
  - `datetime.combine` from the standard library module `datetime`.
  - `min` picks the smallest value.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Loop: the indented lines below repeat as long as `start + timedelta(minutes=minutes) <= limit` is true.
  - `<=` means less than or equal.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Stores the result of `start + timedelta(minutes=minutes)` under the name `end`.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Decision: the indented lines below run only when `not any((overlaps(start, end, b0, b1) for person in people for b0, ...` is true.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `overlaps`, a function of this file (True when two half-open intervals share any time.).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/scheduling_agent/domain/calendar.py`, lines 85 to 88:

```python
                    slots.append(start)
                start += timedelta(minutes=GRID_MINUTES)
        day += timedelta(days=1)
    return slots
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Updates `start` in place: `+=` applies `+` with the result of calling `timedelta` and stores the result back.
  - `timedelta` from the standard library module `datetime`.
- Updates `day` in place: `+=` applies `+` with the result of calling `timedelta` and stores the result back.
  - `timedelta` from the standard library module `datetime`.
- Ends the function and gives back the value named `slots` to the caller.

### `src/scheduling_agent/domain/errors.py`

In its own words: "Named errors. Callers catch these, never a vendor SDK's exception types."

37 non-blank lines; it defines `DomainError`, `ModelError`, `TransientModelError`, `PermanentModelError`, `RecordingMissing`, `UnsupportedParameter`, `BudgetExceeded`, `CalendarError`, `UnknownPerson`, `UnknownEvent`, `SlotUnavailable`, `InvalidSlot`, ....

`src/scheduling_agent/domain/errors.py`, lines 1 to 14:

```python
"""Named errors. Callers catch these, never a vendor SDK's exception types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error this package raises on purpose."""


class ModelError(DomainError):
    """A model call failed."""


class TransientModelError(ModelError):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Defines the class `DomainError`. It builds on `Exception` (the base of ordinary errors). The author's own description: "Base class for every error this package raises on purpose."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `ModelError`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "A model call failed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `TransientModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."

`src/scheduling_agent/domain/errors.py`, lines 15 to 27:

```python
    """The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."""


class PermanentModelError(ModelError):
    """Repeating the call cannot help: a bad request, a bad key, a refusal to parse."""


class RecordingMissing(PermanentModelError):
    """The recorded adapter has no response for this request. Re-record with `make record`."""


class UnsupportedParameter(PermanentModelError):
    """The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `PermanentModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "Repeating the call cannot help: a bad request, a bad key, a refusal to parse."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `RecordingMissing`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The recorded adapter has no response for this request. Re-record with `make record`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `UnsupportedParameter`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/errors.py`, lines 30 to 39:

```python
class BudgetExceeded(DomainError):
    """A run hit one of its caps: steps, tokens or wall-clock time."""

    def __init__(self, cap: str, message: str) -> None:
        super().__init__(message)
        self.cap = cap


class CalendarError(DomainError):
    """The calendar refused or could not do what was asked."""
```

- Defines the class `BudgetExceeded`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "A run hit one of its caps: steps, tokens or wall-clock time."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `cap` holds text.
    - `message` holds text.
- Calls the method `__init__` of `super()` with 1 argument(s); the result is not kept.
  - The method `__init__` of `super()`.
  - `super` refers to the parent class.
- Stores the value named `cap` under the name `self.cap` (as an attribute of this object, so other methods can use it).
- Defines the class `CalendarError`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The calendar refused or could not do what was asked."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/errors.py`, lines 42 to 51:

```python
class UnknownPerson(CalendarError):
    """A name that is not one of the calendar's people."""


class UnknownEvent(CalendarError):
    """No event with that id."""


class SlotUnavailable(CalendarError):
    """A person is already busy at that time."""
```

- Defines the class `UnknownPerson`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "A name that is not one of the calendar's people."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `UnknownEvent`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "No event with that id."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `SlotUnavailable`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "A person is already busy at that time."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/errors.py`, lines 54 to 63:

```python
class InvalidSlot(CalendarError):
    """The time is outside working hours, off the half-hour grid, on a weekend or has a bad length."""


class ApprovalError(DomainError):
    """An approval is missing, not approved, or was granted for a different proposal."""


class AlreadyCancelled(CalendarError):
    """The event is already cancelled."""
```

- Defines the class `InvalidSlot`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "The time is outside working hours, off the half-hour grid, on a weekend or has a bad length."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `ApprovalError`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "An approval is missing, not approved, or was granted for a different proposal."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `AlreadyCancelled`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "The event is already cancelled."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/errors.py`, lines 66 to 71:

```python
class IdempotencyConflict(CalendarError):
    """An Idempotency-Key was reused for a different request."""


class CalendarUnavailable(CalendarError):
    """The calendar service did not answer (timeout, connection refused, 5xx)."""
```

- Defines the class `IdempotencyConflict`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "An Idempotency-Key was reused for a different request."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `CalendarUnavailable`. It builds on the project's `CalendarError` (The calendar refused or could not do what was asked.). The author's own description: "The calendar service did not answer (timeout, connection refused, 5xx)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/scheduling_agent/domain/llm.py`

In its own words: "Vendor-neutral value objects for one chat-model call. No SDK is imported here."

114 non-blank lines; it defines `Role`, `StopReason`, `ToolSpec`, `ToolCall`, `ChatMessage`, `Usage`, `ChatRequest`, `ChatResponse`.

`src/scheduling_agent/domain/llm.py`, lines 1 to 14:

```python
"""Vendor-neutral value objects for one chat-model call. No SDK is imported here."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Who wrote a message."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass`, `field` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Defines the class `Role`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Who wrote a message."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/llm.py`, lines 16 to 28:

```python
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StopReason(StrEnum):
    """Why the model stopped writing."""

    END = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    REFUSAL = "refusal"
    OTHER = "other"
```

- Stores the text `user` under the name `USER`.
- Stores the text `assistant` under the name `ASSISTANT`.
- Stores the text `tool` under the name `TOOL`.
- Defines the class `StopReason`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Why the model stopped writing."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `stop` under the name `END`.
- Stores the text `length` under the name `LENGTH`.
- Stores the text `tool_calls` under the name `TOOL_CALLS`.
- Stores the text `refusal` under the name `REFUSAL`.
- Stores the text `other` under the name `OTHER`.

`src/scheduling_agent/domain/llm.py`, lines 31 to 42:

```python
@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool the model may call: a name, a description and a JSON Schema for the arguments."""

    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call the model asked for."""
```

- Defines the class `ToolSpec`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool the model may call: a name, a description and a JSON Schema for the arguments."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `description` as text; it has no default, so a value must be given when the object is made.
- Declares `parameters` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ToolCall`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool call the model asked for."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/llm.py`, lines 44 to 56:

```python
    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One message of a conversation. A tool result carries the id of the call it answers."""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
```

- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `arguments` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ChatMessage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One message of a conversation. A tool result carries the id of the call it answers."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `role` as the project type `Role`; it has no default, so a value must be given when the object is made.
- Declares `content` as text and sets it to empty text.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tool_call_id` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/scheduling_agent/domain/llm.py`, lines 58 to 68:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)


@dataclass(frozen=True, slots=True)
class Usage:
    """Tokens the provider billed for one call, read from its usage block, never recomputed."""

    input_tokens: int
    output_tokens: int
```

- Defines the method `user`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatMessage`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `content` holds text.
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
- Defines the class `Usage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Tokens the provider billed for one call, read from its usage block, never recomputed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/domain/llm.py`, lines 71 to 82:

```python
@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Everything that defines one call.

    `tag` names the call for recordings and logs (for example `p01/t07/2`); it is never sent to a vendor.
    `model` overrides the adapter's default model and is not part of the recording key.
    """

    messages: tuple[ChatMessage, ...]
    system: str | None = None
    max_output_tokens: int = 1024
    temperature: float | None = None
```

- Defines the class `ChatRequest`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything that defines one call."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a fixed list of the project type `ChatMessage` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `system` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `max_output_tokens` as a whole number and sets it to the number `1024`.
- Declares `temperature` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/scheduling_agent/domain/llm.py`, lines 83 to 90:

```python
    top_p: float | None = None
    response_schema: Mapping[str, Any] | None = None
    tools: tuple[ToolSpec, ...] = ()
    tag: str = ""
    model: str | None = None

    def fingerprint(self) -> str:
        """A stable hash of the request, used to find its recording. The model name is excluded."""
```

- Declares `top_p` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `response_schema` as anything that behaves like a dictionary from text to any value, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tools` as a fixed list of the project type `ToolSpec` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tag` as text and sets it to empty text.
- Declares `model` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the method `fingerprint`. It returns text. The author's own description: "A stable hash of the request, used to find its recording. The model name is excluded."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/llm.py`, lines 91 to 108:

```python
        body = {
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_calls": [[c.id, c.name, dict(c.arguments)] for c in m.tool_calls],
                    "tool_call_id": m.tool_call_id,
                }
                for m in self.messages
            ],
            "system": self.system,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_schema": self.response_schema,
            "tools": [[t.name, t.description, dict(t.parameters)] for t in self.tools],
            "tag": self.tag,
        }
```

- Stores a dictionary with 8 entries under the name `body`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).

`src/scheduling_agent/domain/llm.py`, lines 109 to 122:

```python
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """What came back: the text or the tool calls, why it stopped, the billed usage and the latency."""

    text: str
    stop_reason: StopReason
    usage: Usage
    latency_seconds: float
    model: str
    tool_calls: tuple[ToolCall, ...] = field(default=())
```

- Stores the result of calling `json.dumps` under the name `canonical`.
  - `json.dumps` turns Python data into JSON text.
- Ends the function and gives back the result of calling `hashlib.sha256(canonical.encode('utf-8')).hexdi...` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Defines the class `ChatResponse`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What came back: the text or the tool calls, why it stopped, the billed usage and the latency."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `stop_reason` as the project type `StopReason`; it has no default, so a value must be given when the object is made.
- Declares `usage` as the project type `Usage`; it has no default, so a value must be given when the object is made.
- Declares `latency_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to the result of calling `field`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `field` from the standard library module `dataclasses`.

`src/scheduling_agent/domain/llm.py`, lines 124 to 135:

```python
    def to_json(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "stop_reason": self.stop_reason.value,
            "usage": {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens},
            "latency_seconds": self.latency_seconds,
            "model": self.model,
            "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in self.tool_calls],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ChatResponse:
```

- Defines the method `to_json`. It returns a dictionary from text to any value.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a dictionary with 6 entries to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `from_json`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatResponse`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `data` holds anything that behaves like a dictionary from text to any value.

`src/scheduling_agent/domain/llm.py`, lines 136 to 145:

```python
        return cls(
            text=str(data["text"]),
            stop_reason=StopReason(data["stop_reason"]),
            usage=Usage(int(data["usage"]["input_tokens"]), int(data["usage"]["output_tokens"])),
            latency_seconds=float(data["latency_seconds"]),
            model=str(data["model"]),
            tool_calls=tuple(
                ToolCall(str(c["id"]), str(c["name"]), dict(c["arguments"])) for c in data.get("tool_calls", [])
            ),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `str` turns a value into text.
  - `StopReason`, a class of this project (Why the model stopped writing.).
  - `Usage`, a class of this project (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `float` turns a value into a decimal number.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `int` turns a value into a whole number.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall`, a class of this project (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/scheduling_agent/domain/memory.py`

In its own words: "Long-term memory: facts a person states, a write policy that keeps one fact per topic, and recall by score."

108 non-blank lines; it defines `FactKind`, `Fact`, `_clock`, `parse_statement`, `_weekday`, `compact`, `recall_score`, `rank_facts`, `Constraints`.

`src/scheduling_agent/domain/memory.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `date`, `time`, `timedelta` from the standard library module `datetime`.
- Brings in `StrEnum` from the standard library module `enum`.
- Stores a list of 7 item(s) under the name `_WEEKDAYS`.
- Stores the result of `'(' + '|'.join(_WEEKDAYS) + ')s?'` under the name `_DAY`.
  - `+` is add.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Stores the text `(\d{1,2})(?::(\d{2}))?\s*(am|pm)?` under the name `_TIME`.

`src/scheduling_agent/domain/memory.py`, lines 15 to 27:

```python
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
```

- Stores the result of calling `re.compile` under the name `_EARLIEST`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `re.compile` under the name `_LATEST`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `re.compile` under the name `_AVOID`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `re.compile` under the name `_ALLOW`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the class `FactKind`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "What a fact constrains."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `earliest_start` under the name `EARLIEST_START`.
- Stores the text `latest_end` under the name `LATEST_END`.
- Stores the text `avoid_day` under the name `AVOID_DAY`.
- Stores the text `allow_day` under the name `ALLOW_DAY`.

`src/scheduling_agent/domain/memory.py`, lines 30 to 41:

```python
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
```

- Defines the class `Fact`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Something a person said about their own calendar, with where and when they said it and when it lapses."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `person` as text; it has no default, so a value must be given when the object is made.
- Declares `kind` as the project type `FactKind`; it has no default, so a value must be given when the object is made.
- Declares `value` as text; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `session` as text; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/domain/memory.py`, lines 42 to 55:

```python
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
```

- Declares `stated_on` as a calendar date; it has no default, so a value must be given when the object is made.
- Declares `expires_on` as a calendar date, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the method `topic`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a fixed list of text, text, text. The author's own description: "Facts with the same topic contradict or repeat each other: one per person, kind and (for days) weekday."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `day`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `in` means is contained in.
- Ends the function and gives back a tuple of 3 item(s) to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Defines the method `alive`. It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `today` holds a calendar date.
- Ends the function and gives back the result of combining conditions: `self.expires_on is None or self.expires_on >= today` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `>=` means greater than or equal.
- Defines the function `_clock`. It returns a time of day.
- Its parameters:
    - `hour` holds text.
    - `minute` holds text, or nothing (None).
    - `meridiem` holds text, or nothing (None).
    - `assume_afternoon_below` holds a whole number.

`src/scheduling_agent/domain/memory.py`, lines 56 to 69:

```python
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
```

- Stores a tuple of 2 item(s) under the name `(h, m)`.
  - `int` turns a value into a whole number.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Decision: the indented lines below run only when `meridiem` is true.
- Stores the result of `h % 12 + (12 if meridiem.lower() == 'pm' else 0)` under the name `h`.
  - `+` is add.
  - `%` is remainder.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
  - `.lower(...)` turns text into lower case.
- Decision: the indented lines below run only when `h < assume_afternoon_below` is true.
  - `<` means less than.
- Updates `h` in place: `+=` applies `+` with the number `12` and stores the result back.
- Ends the function and gives back the result of calling `time` to the caller.
  - `time` from the standard library module `datetime`.
- Defines the function `parse_statement`. It returns the project type `Fact`, or nothing (None). The author's own description: "Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep."
- Its parameters:
    - `person` holds text.
    - `text` holds text.
    - `session` holds text.
    - `stated_on` holds a calendar date.
    - `ttl_days` holds a whole number, or nothing (None); if the caller leaves it out it is the number `365`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `expires`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Decision: the indented lines below run only when `(match := _EARLIEST.search(text))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.
- Stores the result of calling `_clock` under the name `when`.
  - `_clock`, a function of this file.
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back the result of calling `Fact` to the caller.
  - `Fact`, a class of this project (Something a person said about their own calendar, with where and when they said it and when it lapses.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.

`src/scheduling_agent/domain/memory.py`, lines 70 to 83:

```python
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
```

- Decision: the indented lines below run only when `(match := _LATEST.search(text))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.
- Stores the result of calling `_clock` under the name `when`.
  - `_clock`, a function of this file.
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back the result of calling `Fact` to the caller.
  - `Fact`, a class of this project (Something a person said about their own calendar, with where and when they said it and when it lapses.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Decision: the indented lines below run only when `(match := _ALLOW.search(text))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.
- Ends the function and gives back the result of calling `Fact` to the caller.
  - `Fact`, a class of this project (Something a person said about their own calendar, with where and when they said it and when it lapses.).
  - `str` turns a value into text.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `_weekday`, a function of this file.
  - `.group(...)` reads a captured part of a regular-expression match.
- Decision: the indented lines below run only when `(match := _AVOID.search(text))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.
- Stores the result of combining conditions: `match.group(1) or match.group(2)` under the name `day`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back the result of calling `Fact` to the caller.
  - `Fact`, a class of this project (Something a person said about their own calendar, with where and when they said it and when it lapses.).
  - `str` turns a value into text.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `_weekday`, a function of this file.
- Ends the function and gives back nothing (`None`) to the caller.
- Defines the function `_weekday`. It returns a whole number.
- Its parameters:
    - `name` holds text.

`src/scheduling_agent/domain/memory.py`, lines 84 to 96:

```python
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
```

- Ends the function and gives back the result of calling `_WEEKDAYS.index` to the caller.
  - `.index(...)` finds the position of an item.
  - `.rstrip(...)` removes spaces from the end of text.
  - `.lower(...)` turns text into lower case.
- Defines the function `compact`. It returns a list of the project type `Fact`. The author's own description: "The facts to keep after writing `new`."
- Its parameters:
    - `existing` holds anything that behaves like a list of the project type `Fact`.
    - `new` holds the project type `Fact`.
    - `today` holds a calendar date.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list built by looping under the name `kept`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - The method `alive` of `f`.
  - `!=` means not equal.
- Decision: the indented lines below run only when `new.kind is FactKind.ALLOW_DAY` is true.
  - `is` means the very same object.
- Ends the function and gives back the value named `kept` to the caller.
- Ends the function and gives back a list of 2 item(s) to the caller.

`src/scheduling_agent/domain/memory.py`, lines 99 to 110:

```python
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
```

- Defines the function `recall_score`. It returns a decimal number. The author's own description: "Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`."
- Its parameters:
    - `similarity` holds a decimal number.
    - `stated_on` holds a calendar date.
    - `today` holds a calendar date.
    - `half_life_days` holds a decimal number; if the caller leaves it out it is the number `180.0`.
    - `weight` holds a decimal number; if the caller leaves it out it is the number `0.7`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `max` under the name `age`.
  - `max` picks the largest value.
  - `-` is subtract.
- Stores the result of calling `math.exp` under the name `recency`.
  - `math.exp` from the standard library module `math`.
  - `/` is divide.
  - `*` is multiply.
  - `math.log` from the standard library module `math`.
- Ends the function and gives back the result of `weight * similarity + (1 - weight) * recency` to the caller.
  - `+` is add.
  - `*` is multiply.
  - `-` is subtract.
- Defines the function `rank_facts`. It returns a list of the project type `Fact`. The author's own description: "The `top` live facts with the best blended score, best first (ties broken by newer first, then text)."
- Its parameters:
    - `scored` holds anything that behaves like a list of a fixed list of the project type `Fact`, a decimal number.
    - `today` holds a calendar date.
    - `top` holds a whole number; if the caller leaves it out it is the number `3`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list built by looping under the name `live`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `alive` of `fact`.

`src/scheduling_agent/domain/memory.py`, lines 111 to 124:

```python
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
```

- Stores the result of calling `sorted` under the name `ranked`.
  - `sorted` returns a new list with the items in order.
  - `lambda args: expression` is a small unnamed function written inline.
  - `recall_score`, a function of this file (Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`.).
  - The method `toordinal` of `item[0].stated_on`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Defines the class `Constraints`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What recalled facts mean for a search: earliest start, latest end and weekdays to avoid."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/memory.py`, lines 126 to 137:

```python
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
```

- Declares `not_before` as a time of day, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `not_after` as a time of day, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `avoid_weekdays` as an unchangeable set of a whole number and sets it to the result of calling `frozenset`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `frozenset` makes a set that cannot be changed.
- Defines the method `from_facts`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `Constraints`. The author's own description: "The strictest constraint of each kind among the facts of the people in the meeting."
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `facts` holds anything that behaves like a list of the project type `Fact`.
    - `people` holds anything that behaves like a list of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list built by looping under the name `mine`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.
- Stores a list built by looping under the name `starts`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `time.fromisoformat` from the standard library module `datetime`.
  - `is` means the very same object.
- Stores a list built by looping under the name `ends`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `time.fromisoformat` from the standard library module `datetime`.
  - `is` means the very same object.
- Stores the result of calling `frozenset` under the name `days`.
  - `frozenset` makes a set that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `int` turns a value into a whole number.
  - `is` means the very same object.
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `max` picks the largest value.
  - `min` picks the smallest value.

### `src/scheduling_agent/domain/prompts.py`

In its own words: "A prompt file: its name, its version line and its text."

12 non-blank lines; it defines `PromptNotFound`, `Prompt`.

`src/scheduling_agent/domain/prompts.py`, lines 1 to 11:

```python
"""A prompt file: its name, its version line and its text."""

from __future__ import annotations

from dataclasses import dataclass

from scheduling_agent.domain.errors import DomainError


class PromptNotFound(DomainError):
    """No prompt file for that name and version, or the file's version line does not match."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `scheduling_agent.domain.errors`.
- Defines the class `PromptNotFound`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "No prompt file for that name and version, or the file's version line does not match."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/prompts.py`, lines 14 to 20:

```python
@dataclass(frozen=True, slots=True)
class Prompt:
    """A prompt as sent to the model, with the version that produced a given result."""

    name: str
    version: str
    text: str
```

- Defines the class `Prompt`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A prompt as sent to the model, with the version that produced a given result."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `version` as text; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.

### `src/scheduling_agent/domain/proposals.py`

In its own words: "Write proposals, approvals and the idempotency key that makes a replayed write harmless."

35 non-blank lines; it defines `Action`, `ApprovalStatus`, `Proposal`, `write_key`.

`src/scheduling_agent/domain/proposals.py`, lines 1 to 14:

```python
"""Write proposals, approvals and the idempotency key that makes a replayed write harmless."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Action(StrEnum):
    """The three writes."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Defines the class `Action`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "The three writes."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/domain/proposals.py`, lines 16 to 26:

```python
    BOOK = "book"
    MOVE = "move"
    CANCEL = "cancel"


class ApprovalStatus(StrEnum):
    """Where an approval is: waiting for a person, approved or rejected."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

- Stores the text `book` under the name `BOOK`.
- Stores the text `move` under the name `MOVE`.
- Stores the text `cancel` under the name `CANCEL`.
- Defines the class `ApprovalStatus`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Where an approval is: waiting for a person, approved or rejected."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `pending` under the name `PENDING`.
- Stores the text `approved` under the name `APPROVED`.
- Stores the text `rejected` under the name `REJECTED`.

`src/scheduling_agent/domain/proposals.py`, lines 29 to 40:

```python
@dataclass(frozen=True, slots=True)
class Proposal:
    """A write the agent wants to make. An approval is for exactly this content, not for a tool name."""

    action: Action
    args: Mapping[str, Any]

    def canonical(self) -> str:
        """Stable JSON: sorted keys, no spaces. The same proposal always gives the same text."""
        return json.dumps({"action": self.action.value, "args": dict(self.args)}, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
```

- Defines the class `Proposal`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A write the agent wants to make. An approval is for exactly this content, not for a tool name."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `action` as the project type `Action`; it has no default, so a value must be given when the object is made.
- Declares `args` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `canonical`. It returns text. The author's own description: "Stable JSON: sorted keys, no spaces. The same proposal always gives the same text."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `json.dumps` to the caller.
  - `json.dumps` turns Python data into JSON text.
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `digest`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/scheduling_agent/domain/proposals.py`, lines 41 to 51:

```python
        return hashlib.sha256(self.canonical().encode()).hexdigest()


def write_key(run_id: str, step: int, part: str = "") -> str:
    """The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.

    The same step gets the same key before and after a crash. A move is two writes (cancel, then book), so each part
    gets its own suffix.
    """
    material = f"{run_id}:{step}" + (f":{part}" if part else "")
    return hashlib.sha256(material.encode()).hexdigest()
```

- Ends the function and gives back the result of calling `hashlib.sha256(self.canonical().encode()).hexdi...` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
  - The method `canonical` of this object (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
- Defines the function `write_key`. It returns text. The author's own description: "The idempotency key of a write: built from the run id and the step number, never from a clock or a random value."
- Its parameters:
    - `run_id` holds text.
    - `step` holds a whole number.
    - `part` holds text; if the caller leaves it out it is empty text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of `f'{run_id}:{step}' + (f':{part}' if part else '')` under the name `material`.
  - `+` is add.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Ends the function and gives back the result of calling `hashlib.sha256(material.encode()).hexdigest` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.

### `src/scheduling_agent/domain/retrieval.py`

In its own words: "Vector similarity for memory recall."

9 non-blank lines; it defines `cosine`.

`src/scheduling_agent/domain/retrieval.py`, lines 1 to 13:

```python
"""Vector similarity for memory recall."""

from __future__ import annotations

import math
from collections.abc import Sequence


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors (0.0 if either is all zeros)."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Defines the function `cosine`. It returns a decimal number. The author's own description: "Cosine similarity of two vectors (0.0 if either is all zeros)."
- Its parameters:
    - `a` holds anything that behaves like a list of a decimal number.
    - `b` holds anything that behaves like a list of a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `sum` under the name `dot`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `*` is multiply.
  - `zip` walks several collections side by side, item by item.
- Stores the result of `math.sqrt(sum((x * x for x in a))) * math.sqrt(sum((y * y...` under the name `norm`.
  - `*` is multiply.
  - `math.sqrt` square root.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.

### `src/scheduling_agent/domain/run.py`

In its own words: "A run of the agent: its status, its saved messages and the write it may be waiting on."

43 non-blank lines; it defines `RunStatus`, `PendingWrite`, `RunState`.

`src/scheduling_agent/domain/run.py`, lines 1 to 14:

```python
"""A run of the agent: its status, its saved messages and the write it may be waiting on."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from scheduling_agent.domain.llm import ChatMessage
from scheduling_agent.domain.proposals import Proposal


class RunStatus(StrEnum):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass`, `field`, `replace` from the standard library module `dataclasses`.
- Brings in `datetime` from the standard library module `datetime`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Defines the class `RunStatus`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Where a run is."

`src/scheduling_agent/domain/run.py`, lines 15 to 28:

```python
    """Where a run is."""

    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PendingWrite:
    """The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch."""

    step: int
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `running` under the name `RUNNING`.
- Stores the text `awaiting_approval` under the name `AWAITING_APPROVAL`.
- Stores the text `done` under the name `DONE`.
- Stores the text `stopped` under the name `STOPPED`.
- Stores the text `failed` under the name `FAILED`.
- Defines the class `PendingWrite`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `step` as a whole number; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/domain/run.py`, lines 29 to 42:

```python
    tool_call_id: str
    tool_name: str
    proposal: Proposal
    approval_id: str
    skipped_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RunState:
    """Everything needed to continue a run after a crash: it is saved after every step, in one transaction."""

    run_id: str
    task: str
    session: str
```

- Declares `tool_call_id` as text; it has no default, so a value must be given when the object is made.
- Declares `tool_name` as text; it has no default, so a value must be given when the object is made.
- Declares `proposal` as the project type `Proposal`; it has no default, so a value must be given when the object is made.
- Declares `approval_id` as text; it has no default, so a value must be given when the object is made.
- Declares `skipped_ids` as a fixed list of text (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `RunState`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything needed to continue a run after a crash: it is saved after every step, in one transaction."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `run_id` as text; it has no default, so a value must be given when the object is made.
- Declares `task` as text; it has no default, so a value must be given when the object is made.
- Declares `session` as text; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/domain/run.py`, lines 43 to 56:

```python
    status: RunStatus
    steps: int
    tokens: int
    messages: tuple[ChatMessage, ...]
    pending: PendingWrite | None = None
    final_text: str = ""
    stop_reason: str = ""
    writes_done: tuple[str, ...] = ()
    created_at: datetime | None = None
    notes: dict[str, Any] = field(default_factory=dict)

    def with_(self, **changes: Any) -> RunState:
        """A copy with some fields changed (the dataclass is frozen)."""
        return replace(self, **changes)
```

- Declares `status` as the project type `RunStatus`; it has no default, so a value must be given when the object is made.
- Declares `steps` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `messages` as a fixed list of the project type `ChatMessage` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `pending` as the project type `PendingWrite`, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `final_text` as text and sets it to empty text.
- Declares `stop_reason` as text and sets it to empty text.
- Declares `writes_done` as a fixed list of text (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `created_at` as a date and time, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `notes` as a dictionary from text to any value and sets it to the result of calling `field`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `field` from the standard library module `dataclasses`.
- Defines the method `with_`. It returns the project type `RunState`. The author's own description: "A copy with some fields changed (the dataclass is frozen)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `**changes` collects any extra named arguments into a dictionary.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `replace` to the caller.
  - `replace` from the standard library module `dataclasses`, which makes a copy of a frozen object with some fields changed.
  - `**name` inside a call passes every entry of a dictionary as a named argument.

### `src/scheduling_agent/domain/tasks.py`

In its own words: "A task for the agent and the calendar end state it must reach."

66 non-blank lines; it defines `InvalidTasks`, `TaskKind`, `TaskSpec`, `validate_tasks`, `expected_end_state`, `end_state`.

`src/scheduling_agent/domain/tasks.py`, lines 1 to 13:

```python
"""A task for the agent and the calendar end state it must reach."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.errors import DomainError

EventKey = tuple[tuple[str, ...], str, int]
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Collection`, `Mapping`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `scheduling_agent.domain.errors`.
- Stores the part of `tuple` picked by `(tuple[str, ...], str, int)` under the name `EventKey`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/domain/tasks.py`, lines 16 to 27:

```python
class InvalidTasks(DomainError):
    """The task file breaks a rule of the lesson."""


class TaskKind(StrEnum):
    """The five kinds of task in the set."""

    BOOK = "book"
    RESCHEDULE = "reschedule"
    FIND_SLOT = "find_slot"
    CANCEL = "cancel"
    IMPOSSIBLE = "impossible"
```

- Defines the class `InvalidTasks`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The task file breaks a rule of the lesson."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `TaskKind`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "The five kinds of task in the set."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `book` under the name `BOOK`.
- Stores the text `reschedule` under the name `RESCHEDULE`.
- Stores the text `find_slot` under the name `FIND_SLOT`.
- Stores the text `cancel` under the name `CANCEL`.
- Stores the text `impossible` under the name `IMPOSSIBLE`.

`src/scheduling_agent/domain/tasks.py`, lines 30 to 41:

```python
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
```

- Defines the class `TaskSpec`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A task in words, what people told the agent earlier, and the changes to the calendar it should end with."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `kind` as the project type `TaskKind`; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `facts` as a fixed list of a fixed list of text, text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/domain/tasks.py`, lines 42 to 54:

```python
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
```

- Declares `add` as a fixed list of `EventKey` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `remove` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `from_json`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `TaskSpec`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `row` holds anything that behaves like a dictionary from text to any value.
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `str` turns a value into text.
  - `TaskKind`, a class of this project (The five kinds of task in the set.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `int` turns a value into a whole number.

`src/scheduling_agent/domain/tasks.py`, lines 57 to 68:

```python
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
```

- Defines the function `validate_tasks`. It returns nothing (None). The author's own description: "The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete."
- Its parameters:
    - `tasks` holds anything that behaves like a list of the project type `TaskSpec`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Decision: the indented lines below run only when `len(set(ids)) != len(ids)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
  - `set` makes a set: a collection with no repeated items.
- Raises an error: the result of calling `InvalidTasks`. Execution jumps out to the nearest matching `except`.
  - `InvalidTasks`, a class of this project (The task file breaks a rule of the lesson.).
- Stores a dictionary with 5 entries under the name `want`.

`src/scheduling_agent/domain/tasks.py`, lines 69 to 81:

```python
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
```

- Stores a dictionary built by looping under the name `have`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `sum` adds up all the numbers.
  - `is` means the very same object.
- Decision: the indented lines below run only when `have != want` is true.
  - `!=` means not equal.
- Raises an error: the result of calling `InvalidTasks`. Execution jumps out to the nearest matching `except`.
  - `InvalidTasks`, a class of this project (The task file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `dict` makes a dictionary (a copy when given one).
- Loop: the indented lines below run once for each item of `tasks`; `task` names the current item.
- Decision: the indented lines below run only when `task.kind is TaskKind.IMPOSSIBLE and (task.add or task.remove)` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
- Raises an error: the result of calling `InvalidTasks`. Execution jumps out to the nearest matching `except`.
  - `InvalidTasks`, a class of this project (The task file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `expected_end_state`. It returns a set of `EventKey`. The author's own description: "The seeded calendar with the task's removals and additions applied, as comparable keys."
- Its parameters:
    - `seed` holds a collection with a size of the project type `Event`.
    - `task` holds the project type `TaskSpec`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `set` under the name `removed`.
  - `set` makes a set: a collection with no repeated items.
- Stores a set built by looping under the name `kept`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not in` means is not contained in.
  - `not` flips true and false.
- Ends the function and gives back the result of `kept | set(task.add)` to the caller.
  - `|` is or; in a type, "either".
  - `set` makes a set: a collection with no repeated items.

`src/scheduling_agent/domain/tasks.py`, lines 84 to 86:

```python
def end_state(active: Collection[Event]) -> set[EventKey]:
    """The calendar's real state as comparable keys."""
    return {e.key() for e in active}
```

- Defines the function `end_state`. It returns a set of `EventKey`. The author's own description: "The calendar's real state as comparable keys."
- Its parameters:
    - `active` holds a collection with a size of the project type `Event`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a set built by looping to the caller.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import scheduling_agent.__init__; print(scheduling_agent.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
A scheduling agent: approval for every write, budgets, crash-safe resumption and long-term memory.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/scheduling_agent/domain').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
approvals.py 3
budget.py 1
calendar.py 4
errors.py 16
llm.py 8
memory.py 9
prompts.py 2
proposals.py 4
retrieval.py 1
run.py 3
tasks.py 6
```

3. The rule that keeps this layer in its place: both contracts must be KEPT.

```bash
.venv/bin/lint-imports --no-logo 2>&1 | grep -E 'KEPT|BROKEN'
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT
```

## Mistakes people make

- **Common mistakes with this layer.** Importing a vendor library "just for a type" into the domain (the build fails: see `import-linter.md`), putting input/output (files, network) in a domain function, or letting a domain function read an environment variable. Here the domain takes everything it needs as arguments and returns values.

## Check yourself

1. What is the job of `src/scheduling_agent/__init__.py`?

   *Answer:* A scheduling agent: approval for every write, budgets, crash-safe resumption and long-term memory.

2. What is the job of `src/scheduling_agent/domain/__init__.py`?

   *Answer:* Pure domain logic. Depends on nothing outside the standard library.

3. What is the job of `src/scheduling_agent/domain/approvals.py`?

   *Answer:* Value objects for approvals, audit lines and the result of a calendar write.

4. What is the job of `src/scheduling_agent/domain/budget.py`?

   *Answer:* Budgets around the agent loop: steps, tokens and wall-clock time, each checked on its own.

5. What is the job of `src/scheduling_agent/domain/calendar.py`?

   *Answer:* Calendar rules: working hours, the half-hour grid, overlaps and the search for free slots.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
