# Python source, shared test helpers and the process, end-to-end and live tests

## What it is

These tests are the larger ones: `conftest.py` (shared builders and fakes used by many tests), the **integration** tests (the program or a service as a real process, with real signals), the **end-to-end** tests (the lesson's scenario from input to report on recorded answers) and the **live** tests (opt-in, call a real model).

This note walks through every file, line by line: 6 files with 9 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/conftest.py` | 125 non-blank lines |
| `tests/e2e/conftest.py` | 3 non-blank lines |
| `tests/e2e/test_lesson_scenario.py` | 20 non-blank lines |
| `tests/integration/conftest.py` | 73 non-blank lines |
| `tests/integration/test_processes.py` | 109 non-blank lines |
| `tests/live/test_live_models.py` | 35 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/conftest.py`

In its own words: "Shared builders for tests: a fixed clock, a hashing embedder and a ready agent kit on in-memory databases."

125 non-blank lines; it defines `FixedClock`, `HashingEmbedder`, `ScriptedModel`, `Crash`, `RaiseAt`, `new_calendar`, `build_kit`, `approve_all`, `clock`.

`tests/conftest.py`, lines 1 to 14:

```python
"""Shared builders for tests: a fixed clock, a hashing embedder and a ready agent kit on in-memory databases."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from scheduling_agent.application.agent import AgentConfig, SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Brings in `AgentConfig` (The caps of a run and the size of one model answer.), `SchedulingAgent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.) from the project module `scheduling_agent.application.agent`.
- Brings in `MemoryService` (Remember what people say, recall the three most relevant facts for a task, forget on request.) from the project module `scheduling_agent.application.memory_service`.

`tests/conftest.py`, lines 15 to 26:

```python
from scheduling_agent.application.ports import CalendarPort, ChatModel
from scheduling_agent.application.task_runner import AgentKit
from scheduling_agent.application.tools import ToolBox
from scheduling_agent.domain.llm import ChatRequest, ChatResponse, StopReason, Usage
from scheduling_agent.domain.prompts import Prompt
from scheduling_agent.infrastructure.agent_db import AgentDb
from scheduling_agent.infrastructure.calendar_db import SqliteCalendar
from scheduling_agent.infrastructure.failpoints import NoFailPoints
from scheduling_agent.infrastructure.scripted_policy import ScriptedPolicyModel
from scheduling_agent.infrastructure.sqlite import apply_sql, connect

REPO = Path(__file__).resolve().parents[1]
```

- Brings in `CalendarPort` (The calendar service. Writes take an idempotency key; a repeated key returns the first result.), `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `scheduling_agent.application.ports`.
- Brings in `AgentKit` (One agent with the stores it was built on, so a runner can read what it did.) from the project module `scheduling_agent.application.task_runner`.
- Brings in `ToolBox` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.) from the project module `scheduling_agent.application.tools`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `scheduling_agent.domain.prompts`.
- Brings in `AgentDb` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.) from the project module `scheduling_agent.infrastructure.agent_db`.
- Brings in `SqliteCalendar` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.) from the project module `scheduling_agent.infrastructure.calendar_db`.
- Brings in `NoFailPoints` (The production default: nothing ever fails on purpose.) from the project module `scheduling_agent.infrastructure.failpoints`.
- Brings in `ScriptedPolicyModel` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.) from the project module `scheduling_agent.infrastructure.scripted_policy`.
- Brings in `apply_sql` (Run SQL script files in the order given (the numbered files under sql/).), `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `1` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.

`tests/conftest.py`, lines 29 to 39:

```python
class FixedClock:
    """A clock that only moves when a test says so; `monotonic` advances by `tick` on every call."""

    def __init__(self, today: date = date(2026, 10, 27), tick: float = 0.25) -> None:
        self._today = today
        self._ticks = 0.0
        self._tick = tick

    def monotonic(self) -> float:
        self._ticks += self._tick
        return self._ticks
```

- Defines the class `FixedClock`. The author's own description: "A clock that only moves when a test says so; `monotonic` advances by `tick` on every call."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `today` holds a calendar date; if the caller leaves it out it is the result of calling `date`.
    - `tick` holds a decimal number; if the caller leaves it out it is the number `0.25`.
- Stores the value named `today` under the name `self._today` (as an attribute of this object, so other methods can use it).
- Stores the number `0.0` under the name `self._ticks` (as an attribute of this object, so other methods can use it).
- Stores the value named `tick` under the name `self._tick` (as an attribute of this object, so other methods can use it).
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Updates `self._ticks` in place: `+=` applies `+` with the attribute `_tick` of this object and stores the result back.
- Ends the function and gives back the attribute `_ticks` of this object to the caller.

`tests/conftest.py`, lines 41 to 53:

```python
    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class HashingEmbedder:
    """A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."""

    name = "hashing"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
```

- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_today` of this object to the caller.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime` to the caller.
  - `datetime` from the standard library module `datetime`.
- Defines the class `HashingEmbedder`. The author's own description: "A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `hashing` under the name `name`.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.

`tests/conftest.py`, lines 54 to 64:

```python
        out = []
        for text in texts:
            vector = [0.0] * 64
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            out.append(vector)
        return out


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""
```

- Stores an empty list under the name `out`.
- Loop: the indented lines below run once for each item of `texts`; `text` names the current item.
- Stores the result of `[0.0] * 64` under the name `vector`.
  - `*` is multiply.
- Loop: the indented lines below run once for each item of `re.findall('[a-z0-9]+', text.lower())`; `word` names the current item.
  - `re.findall` lists all matches.
  - `.lower(...)` turns text into lower case.
- Updates `vector[int(hashlib.md5(word.encode())...` in place: `+=` applies `+` with the number `1.0` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `%` is remainder.
  - `int` turns a value into a whole number.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.md5` from the standard library module `hashlib`.
  - `.encode(...)` turns text into bytes.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `ScriptedModel`. The author's own description: "Answers every request from a function, and remembers the requests it saw."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`tests/conftest.py`, lines 66 to 78:

```python
    def __init__(
        self, answer: Callable[[ChatRequest], str | tuple[str, int, int]] | None = None, sampling: bool = True
    ) -> None:
        self.requests: list[ChatRequest] = []
        self._answer = answer or (lambda request: ("ok", 10, 3))
        self._sampling = sampling

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def supports_sampling(self) -> bool:
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `answer` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `sampling` holds true or false; if the caller leaves it out it is the value `True`.
- Declares `self.requests` as a list of the project type `ChatRequest` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of combining conditions: `answer or (lambda request: ('ok', 10, 3))` under the name `self._answer` (as an attribute of this object, so other methods can use it).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the value named `sampling` under the name `self._sampling` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `scripted` to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`tests/conftest.py`, lines 79 to 92:

```python
        return self._sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        result = self._answer(request)
        text, tokens_in, tokens_out = (result, 30, 8) if isinstance(result, str) else result
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class Crash(BaseException):
    """Raised by a test failpoint to stand in for the process dying at that point (nothing catches BaseException)."""


class RaiseAt:
```

- Ends the function and gives back the attribute `_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Calls `append` on the stored object `self.requests`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self.requests`: it adds one item at the end of a list.
- Stores the result of calling `self._answer` under the name `result`.
  - The method `_answer` of `self`.
- Stores one of two values, chosen by a condition under the name `(text, tokens_in, tokens_out)`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the class `Crash`. It builds on `BaseException`. The author's own description: "Raised by a test failpoint to stand in for the process dying at that point (nothing catches BaseException)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `RaiseAt`. The author's own description: "A failpoint that raises `Crash` the first time execution reaches the named point."

`tests/conftest.py`, lines 93 to 106:

```python
    """A failpoint that raises `Crash` the first time execution reaches the named point."""

    def __init__(self, name: str) -> None:
        self._name = name
        self.fired = False

    def hit(self, name: str) -> None:
        if name == self._name and not self.fired:
            self.fired = True
            raise Crash(name)


def new_calendar() -> SqliteCalendar:
    db = connect(":memory:")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- Stores the value named `name` under the name `self._name` (as an attribute of this object, so other methods can use it).
- Stores the value `False` under the name `self.fired` (as an attribute of this object, so other methods can use it).
- Defines the method `hit`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- Decision: the indented lines below run only when `name == self._name and (not self.fired)` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `not` flips true and false.
- Stores the value `True` under the name `self.fired` (as an attribute of this object, so other methods can use it).
- Raises an error: the result of calling `Crash`. Execution jumps out to the nearest matching `except`.
  - `Crash`, a class of this project (Raised by a test failpoint to stand in for the process dying at that point (nothing catches BaseException).).
- Defines the function `new_calendar`. It returns the project type `SqliteCalendar`.
- It takes no parameters.
- Stores the result of calling `connect` under the name `db`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).

`tests/conftest.py`, lines 107 to 112:

```python
    apply_sql(db, REPO / "sql/calendar/001_schema.sql", REPO / "sql/calendar/002_seed.sql")
    return SqliteCalendar(db)


PROMPT = Prompt("agent", "v1", "You schedule meetings.")
PEOPLE = ("alice", "bob", "carol", "dave", "erin")
```

- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 3 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Ends the function and gives back the result of calling `SqliteCalendar` to the caller.
  - `SqliteCalendar` from the project's `scheduling_agent.infrastructure.calendar_db` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.).
- Stores the result of calling `Prompt` under the name `PROMPT`.
  - `Prompt` from the project's `scheduling_agent.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
- Stores a tuple of 5 item(s) under the name `PEOPLE`.

`tests/conftest.py`, lines 115 to 126:

```python
def build_kit(
    calendar: CalendarPort | None = None,
    model: ChatModel | None = None,
    store: AgentDb | None = None,
    points=None,
    config: AgentConfig | None = None,
    clock: FixedClock | None = None,
) -> AgentKit:
    clock = clock or FixedClock()
    cal = calendar or new_calendar()
    if store is None:
        db = connect(":memory:")
```

- Defines the function `build_kit`. It returns the project type `AgentKit`.
- Its parameters:
    - `calendar` holds the project type `CalendarPort`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `model` holds the project type `ChatModel`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `store` holds the project type `AgentDb`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `points`; if the caller leaves it out it is nothing (`None`).
    - `config` holds the project type `AgentConfig`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `clock` holds the project type `FixedClock`, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the result of combining conditions: `clock or FixedClock()` under the name `clock`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `FixedClock`, a class of this project (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of combining conditions: `calendar or new_calendar()` under the name `cal`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `new_calendar`, a function of this file.
- Decision: the indented lines below run only when `store is None` is true.
  - `is` means the very same object.
- Stores the result of calling `connect` under the name `db`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).

`tests/conftest.py`, lines 127 to 132:

```python
        apply_sql(db, REPO / "sql/agent/001_schema.sql")
        store = AgentDb(db)
    marks = points or NoFailPoints()
    tools = ToolBox(cal, store, store, clock, marks)
    memory = MemoryService(store, HashingEmbedder(), clock, PEOPLE)
    counter = iter(range(1, 10_000))
```

- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Stores the result of calling `AgentDb` under the name `store`.
  - `AgentDb` from the project's `scheduling_agent.infrastructure.agent_db` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.).
- Stores the result of combining conditions: `points or NoFailPoints()` under the name `marks`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `NoFailPoints` from the project's `scheduling_agent.infrastructure.failpoints` (The production default: nothing ever fails on purpose.).
- Stores the result of calling `ToolBox` under the name `tools`.
  - `ToolBox` from the project's `scheduling_agent.application.tools` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.).
- Stores the result of calling `MemoryService` under the name `memory`.
  - `MemoryService` from the project's `scheduling_agent.application.memory_service` (Remember what people say, recall the three most relevant facts for a task, forget on request.).
  - `HashingEmbedder`, a class of this project (A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only.).
- Stores the result of calling `iter` under the name `counter`.
  - `iter` makes an iterator over a collection.
  - `range` makes the numbers from 0 up to (not including) the given one.

`tests/conftest.py`, lines 133 to 146:

```python
    agent = SchedulingAgent(
        model or ScriptedPolicyModel(),
        tools,
        store,
        store,
        store,
        memory,
        clock,
        PROMPT,
        config or AgentConfig(),
        marks,
        new_run_id=lambda: f"run-{next(counter)}",
    )
    return AgentKit(agent, store, store, store, memory, cal)
```

- Stores the result of calling `SchedulingAgent` under the name `agent`.
  - `SchedulingAgent` from the project's `scheduling_agent.application.agent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `ScriptedPolicyModel` from the project's `scheduling_agent.infrastructure.scripted_policy` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.).
  - `AgentConfig` from the project's `scheduling_agent.application.agent` (The caps of a run and the size of one model answer.).
  - `lambda args: expression` is a small unnamed function written inline.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `next` takes the next item from an iterator.
- Ends the function and gives back the result of calling `AgentKit` to the caller.
  - `AgentKit` from the project's `scheduling_agent.application.task_runner` (One agent with the stores it was built on, so a runner can read what it did.).

`tests/conftest.py`, lines 149 to 158:

```python
def approve_all(kit: AgentKit, state, decide: Callable[[object], bool] | None = None):
    """Play the person: approve every pending proposal of the run, resuming until the run stops waiting."""
    from scheduling_agent.domain.run import RunStatus

    clock = FixedClock()
    while state.status is RunStatus.AWAITING_APPROVAL:
        for approval in kit.approvals.pending():
            kit.approvals.decide(approval.id, True, "test", clock.now())
        state = kit.agent.resume(state.run_id)
    return state
```

- Defines the function `approve_all`. The author's own description: "Play the person: approve every pending proposal of the run, resuming until the run stops waiting."
- Its parameters:
    - `kit` holds the project type `AgentKit`.
    - `state`.
    - `decide` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Brings in `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Stores the result of calling `FixedClock` under the name `clock`.
  - `FixedClock`, a class of this project (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Loop: the indented lines below repeat as long as `state.status is RunStatus.AWAITING_APPROVAL` is true.
  - `is` means the very same object.
- Loop: the indented lines below run once for each item of `kit.approvals.pending()`; `approval` names the current item.
  - The method `pending` of `kit.approvals`.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `clock`.
- Stores the result of calling `kit.agent.resume` under the name `state`.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Ends the function and gives back the value named `state` to the caller.

`tests/conftest.py`, lines 161 to 163:

```python
@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()
```

- Defines the function `clock`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter. It returns the project type `FixedClock`.
- It takes no parameters.
- Ends the function and gives back the result of calling `FixedClock` to the caller.
  - `FixedClock`, a class of this project (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).

### `tests/e2e/conftest.py`

In its own words: "The e2e tests reuse the fixture that starts the calendar service as a real process."

3 non-blank lines.

`tests/e2e/conftest.py`, lines 1 to 5:

```python
"""The e2e tests reuse the fixture that starts the calendar service as a real process."""

from tests.integration.conftest import service

__all__ = ["service"]
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Brings in `service` from the project module `tests.integration.conftest`.
- Stores a list of 1 item(s) under the name `__all__`.

### `tests/e2e/test_lesson_scenario.py`

In its own words: "The lesson's step 6 through the real HTTP service: 30 tasks, three runs each, judged by the calendar's end state."

20 non-blank lines; it defines `test_the_thirty_tasks_three_times_each_through_the_real_http_service_all_reach_their_end_state`.

`tests/e2e/test_lesson_scenario.py`, lines 1 to 14:

```python
"""The lesson's step 6 through the real HTTP service: 30 tasks, three runs each, judged by the calendar's end state."""

import httpx
import pytest

from scheduling_agent.application.task_runner import ExpectedWritesApprover, TaskRunner
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.files import load_tasks
from tests.conftest import REPO, build_kit
from tests.integration.conftest import Service
from tests.integration.test_processes import double_bookings

pytestmark = pytest.mark.e2e
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `ExpectedWritesApprover` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.), `TaskRunner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.) from the project module `scheduling_agent.application.task_runner`.
- Brings in `HttpCalendar` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.) from the project module `scheduling_agent.infrastructure.calendar_client`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `scheduling_agent.infrastructure.clock`.
- Brings in `load_tasks` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.) from the project module `scheduling_agent.infrastructure.files`.
- Brings in `REPO`, `build_kit` from the project module `tests.conftest`.
- Brings in `Service` from the project module `tests.integration.conftest`.
- Brings in `double_bookings` (The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time.) from the project module `tests.integration.test_processes`.
- Stores the `e2e` of `pytest.mark` under the name `pytestmark`.

`tests/e2e/test_lesson_scenario.py`, lines 17 to 25:

```python
def test_the_thirty_tasks_three_times_each_through_the_real_http_service_all_reach_their_end_state(service: Service):
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")
    calendar = HttpCalendar(httpx.Client(timeout=10), service.url)
    runner = TaskRunner(calendar, lambda: build_kit(calendar=calendar), ExpectedWritesApprover(), SystemClock())
    results = runner.run_all(tasks, repeats=3)
    assert len(results) == 90
    assert [r.task_id for r in results if not r.passed] == []
    assert sum(r.writes_without_approval for r in results) == 0
    assert double_bookings(service) == 0
```

- Defines the function `test_the_thirty_tasks_three_times_each_through_the_real_http_service_all_reach_their_end_state`.
- Its parameters:
    - `service` holds the project type `Service`.
- Stores the result of calling `load_tasks` under the name `tasks`.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.
- Stores the result of calling `HttpCalendar` under the name `calendar`.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
  - `httpx.Client` makes an HTTP client.
- Stores the result of calling `TaskRunner` under the name `runner`.
  - `TaskRunner` from the project's `scheduling_agent.application.task_runner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.).
  - `lambda args: expression` is a small unnamed function written inline.
  - `ExpectedWritesApprover` from the project's `scheduling_agent.application.task_runner` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `runner.run_all` under the name `results`.
  - The method `run_all` of the project's `TaskRunner` (Every task `repeats` times, in order.).
- Checks that `len(results) == 90` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `[r.task_id for r in results if not r.passed] == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not` flips true and false.
- Checks that `sum((r.writes_without_approval for r in results)) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `double_bookings(service) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `double_bookings` from the project's `tests.integration.test_processes` (The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time.).

### `tests/integration/conftest.py`

In its own words: "Fixtures that start the calendar service as a real process on a free port."

73 non-blank lines; it defines `Service`, `free_port`, `base_env`, `service`, `agent`, `events`.

`tests/integration/conftest.py`, lines 1 to 13:

```python
"""Fixtures that start the calendar service as a real process on a free port."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `socket` (standard library) available.
- Makes the module `subprocess` (standard library) available.
- Makes the module `sys` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Iterator` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.

`tests/integration/conftest.py`, lines 15 to 25:

```python
import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Service:
    url: str
    db: Path
    process: subprocess.Popen[str]
```

- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Stores the part of `Path(__file__).resolve().pa...` picked by `2` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Defines the class `Service`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly.
- Declares `url` as text; it has no default, so a value must be given when the object is made.
- Declares `db` as a file path; it has no default, so a value must be given when the object is made.
- Declares `process` as Popen of text; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/integration/conftest.py`, lines 28 to 37:

```python
def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def base_env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "FAILPOINT"}}
    env.update(MODEL_PROVIDER="scripted", EMBEDDER_PROVIDER="recorded", LOG_LEVEL="WARNING", **extra)
    return env
```

- Defines the function `free_port`. It returns a whole number.
- It takes no parameters.
- A `with` block: it sets up `socket.socket()` as `sock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `socket.socket` makes a network socket.
- Calls the method `bind` of `sock` with 1 argument(s); the result is not kept.
  - The method `bind` of `sock`.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `getsockname` of `sock`.
- Defines the function `base_env`. It returns a dictionary from text to text.
- Its parameters:
    - `**extra` collects any extra named arguments into a dictionary.
- Stores a dictionary built by looping under the name `env`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `os.environ.items` from the standard library module `os`.
  - `not in` means is not contained in.
- Calls `.update(...)` merges another collection into this one with 4 argument(s); the result is not kept.
  - `.update(...)` merges another collection into this one.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- Ends the function and gives back the value named `env` to the caller.

`tests/integration/conftest.py`, lines 40 to 44:

```python
@pytest.fixture
def service(tmp_path: Path) -> Iterator[Service]:
    port = free_port()
    db = tmp_path / "calendar.db"
    env = base_env(HTTP_PORT=str(port), CALENDAR_DB=str(db), CALENDAR_ALLOW_RESET="on")
```

- Defines the function `service`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter. It returns something that gives items one at a time of the project type `Service`.
- Its parameters:
    - `tmp_path` holds a file path.
- Stores the result of calling `free_port` under the name `port`.
  - `free_port`, a function of this file.
- Stores the result of `tmp_path / 'calendar.db'` under the name `db`.
  - `/` is divide.
- Stores the result of calling `base_env` under the name `env`.
  - `base_env`, a function of this file.
  - `str` turns a value into text.

`tests/integration/conftest.py`, lines 45 to 58:

```python
    process = subprocess.Popen(
        [sys.executable, "-m", "scheduling_agent.interfaces.calendar_server", "serve"],
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{url}/health", timeout=1).status_code == 200:
                break
```

- Stores the result of calling `subprocess.Popen` under the name `process`.
  - `subprocess.Popen` starts another program and returns a handle.
- Stores a text built from pieces (an f-string) under the name `url`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of `time.monotonic() + 60` under the name `deadline`.
  - `+` is add.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
- Loop: the indented lines below repeat as long as `time.monotonic() < deadline` is true.
  - `<` means less than.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Decision: the indented lines below run only when `httpx.get(f'{url}/health', timeout=1).status_code == 200` is true.
  - `==` means equal.
  - `httpx.get` sends an HTTP GET request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Leaves the loop at once.

`tests/integration/conftest.py`, lines 59 to 72:

```python
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("the calendar service did not start")
    yield Service(url, db, process)
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=30)


def agent(
    service: Service, tmp_path: Path, *args: str, failpoint: str | None = None
) -> subprocess.CompletedProcess[str]:
```

- `except` handler: it runs when the `try` block raised `httpx.HTTPError`.
- Calls `time.sleep` pauses the program with 1 argument(s); the result is not kept.
  - `time.sleep` pauses the program.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.kill(...)` ends a process at once; the result is not kept.
  - `.kill(...)` ends a process at once.
- Raises an error: the result of calling `RuntimeError`. Execution jumps out to the nearest matching `except`.
  - `RuntimeError` a general error raised while running.
- Hands a value to the caller and pauses until the next one is asked for.
  - `yield` hands a value to the caller and pauses the function until the next value is asked for.
  - `Service`, a class of this project.
- Decision: the indented lines below run only when `process.poll() is None` is true.
  - `is` means the very same object.
  - `.poll(...)` asks whether a process has finished (None if still running).
- Calls `.send_signal(...)` sends an operating-system signal to a process with 1 argument(s); the result is not kept.
  - `.send_signal(...)` sends an operating-system signal to a process.
- Calls `.wait(...)` waits until something happens with 1 argument(s); the result is not kept.
  - `.wait(...)` waits until something happens.
- Defines the function `agent`. It returns CompletedProcess of text. The author's own description: "Run the `agent` command as a process against the service, with its own database file."
- Its parameters:
    - `service` holds the project type `Service`.
    - `tmp_path` holds a file path.
    - `*args` collects any extra positional arguments into a tuple.
    - `failpoint` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.

`tests/integration/conftest.py`, lines 73 to 84:

```python
    """Run the `agent` command as a process against the service, with its own database file."""
    extra = {"FAILPOINT": failpoint} if failpoint else {}
    env = base_env(CALENDAR_URL=service.url, AGENT_DB=str(tmp_path / "agent.db"), **extra)
    return subprocess.run(
        [sys.executable, "-m", "scheduling_agent.interfaces.cli", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `extra`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Stores the result of calling `base_env` under the name `env`.
  - `base_env`, a function of this file.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
  - `str` turns a value into text.
  - `/` is divide.
- Ends the function and gives back the result of calling `subprocess.run` to the caller.
  - `subprocess.run` runs another program and waits for it.

`tests/integration/conftest.py`, lines 87 to 89:

```python
def events(service: Service) -> list[dict[str, object]]:
    body: list[dict[str, object]] = httpx.get(f"{service.url}/events", timeout=10).json()
    return body
```

- Defines the function `events`. It returns a list of a dictionary from text to any object.
- Its parameters:
    - `service` holds the project type `Service`.
- Declares `body` as a list of a dictionary from text to any object and sets it to the result of calling `httpx.get(f'{service.url}/events', timeout=10)....`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `httpx.get` sends an HTTP GET request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `body` to the caller.

### `tests/integration/test_processes.py`

In its own words: "The calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes."

109 non-blank lines; it defines `reset`, `double_bookings`, `test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice`, `test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume`, `test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person`, `test_a_rejected_proposal_over_the_command_line_writes_nothing`, `test_parallel_requests_with_one_key_over_http_create_one_event_and_other_keys_conflict`, `test_sigterm_lets_the_service_finish_and_exit_cleanly`.

`tests/integration/test_processes.py`, lines 1 to 13:

```python
"""The calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes."""

import signal
import sqlite3
import threading

import httpx
import pytest

from tests.conftest import REPO
from tests.integration.conftest import Service, agent, events

pytestmark = pytest.mark.integration
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `signal` (standard library) available.
- Makes the module `sqlite3` (standard library) available.
- Makes the module `threading` (standard library) available.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `REPO` from the project module `tests.conftest`.
- Brings in `Service`, `agent` (Run the `agent` command as a process against the service, with its own database file.), `events` from the project module `tests.integration.conftest`.
- Stores the `integration` of `pytest.mark` under the name `pytestmark`.

`tests/integration/test_processes.py`, lines 15 to 26:

```python
# five booking tasks, one per crash point plus one clean run, all on different days so they never collide
CRASH_CASES = [
    ("run_created", "Book a 30-minute meeting with alice and bob on 2026-11-02."),
    ("after_step", "Book a 30-minute meeting with carol and dave on 2026-11-03."),
    ("after_proposal", "Book a 30-minute meeting with erin and alice on 2026-11-04."),
    ("after_write_before_checkpoint", "Book a 30-minute meeting with bob and carol on 2026-11-05."),
    (None, "Book a 30-minute meeting with dave and erin on 2026-11-06."),
]


def reset(service: Service) -> None:
    assert httpx.post(f"{service.url}/admin/reset", timeout=10).status_code == 200
```

- Stores a list of 5 item(s) under the name `CRASH_CASES`.
- Defines the function `reset`. It returns nothing (None).
- Its parameters:
    - `service` holds the project type `Service`.
- Checks that `httpx.post(f'{service.url}/admin/reset', timeout=10).status_code == 200` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `httpx.post` sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`tests/integration/test_processes.py`, lines 29 to 40:

```python
def double_bookings(service: Service) -> int:
    """The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time."""
    sql = (REPO / "sql/calendar/003_queries.sql").read_text().split(";")[1] + ";"
    with sqlite3.connect(service.db) as db:
        return len(db.execute(sql).fetchall())


def test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice(service, tmp_path):
    reset(service)
    baseline = len(events(service))
    for index, (point, task) in enumerate(CRASH_CASES, start=1):
        run_id = f"crash-{index}"
```

- Defines the function `double_bookings`. It returns a whole number. The author's own description: "The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time."
- Its parameters:
    - `service` holds the project type `Service`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of `(REPO / 'sql/calendar/003_queries.sql').read_text().split...` under the name `sql`.
  - `+` is add.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `/` is divide.
- A `with` block: it sets up `sqlite3.connect(service.db)` as `db`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `sqlite3.connect` opens a SQLite database file.
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
  - `.fetchall(...)` reads all rows of a query result.
  - `.execute(...)` runs one SQL statement.
- Defines the function `test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice`.
- Its parameters:
    - `service`.
    - `tmp_path`.
- Calls `reset`, a function of this file with 1 argument(s); the result is not kept.
  - `reset`, a function of this file.
- Stores the result of calling `len` under the name `baseline`.
  - `len` counts the items in a collection (or the characters in text).
  - `events` from the project's `tests.integration.conftest`.
- Loop: the indented lines below run once for each item of `enumerate(CRASH_CASES, start=1)`; `(index, (point, task))` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Stores a text built from pieces (an f-string) under the name `run_id`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`tests/integration/test_processes.py`, lines 41 to 54:

```python
        killed = agent(service, tmp_path, "run", task, "--run-id", run_id, "--auto-approve", failpoint=point)
        if point is None:
            assert killed.returncode == 0, killed.stderr
        else:
            assert killed.returncode == -signal.SIGKILL, (point, killed.returncode, killed.stderr)
            resumed = agent(service, tmp_path, "resume", run_id, "--auto-approve")
            assert resumed.returncode == 0, resumed.stderr
            assert "done after" in resumed.stdout
            assert "Booked event" in resumed.stdout
        written = agent(service, tmp_path, "audit", "--run", run_id).stdout.count(" written ")
        assert written == 1, (point, written)
    after = events(service)
    assert len(after) == baseline + 5
    keys = [(tuple(e["people"]), e["start"], e["minutes"]) for e in after]  # type: ignore[arg-type,var-annotated]
```

- Stores the result of calling `agent` under the name `killed`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Decision: the indented lines below run only when `point is None` is true.
  - `is` means the very same object.
- Checks that `killed.returncode == 0` is true; if it is not, the test fails with an `AssertionError` and the message `killed.stderr`.
  - `==` means equal.
- `else:` — the indented lines below run when none of the conditions above were true.
- Checks that `killed.returncode == -signal.SIGKILL` is true; if it is not, the test fails with an `AssertionError` and the message `(point, killed.returncode, killed.std...`.
  - `==` means equal.
- Stores the result of calling `agent` under the name `resumed`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `resumed.returncode == 0` is true; if it is not, the test fails with an `AssertionError` and the message `resumed.stderr`.
  - `==` means equal.
- Checks that `'done after' in resumed.stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'Booked event' in resumed.stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Stores the result of calling `agent(service, tmp_path, 'audit', '--run', run_...` under the name `written`.
  - `.count(...)` counts how often an item appears.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `written == 1` is true; if it is not, the test fails with an `AssertionError` and the message `(point, written)`.
  - `==` means equal.
- Stores the result of calling `events` under the name `after`.
  - `events` from the project's `tests.integration.conftest`.
- Checks that `len(after) == baseline + 5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
- Stores a list built by looping under the name `keys`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/integration/test_processes.py`, lines 55 to 68:

```python
    assert len(keys) == len(set(keys))
    assert double_bookings(service) == 0


def test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume(service, tmp_path):
    reset(service)
    before = events(service)
    victim = before[3]
    task = f"Move event {victim['id']} to the earliest free slot between 2026-11-09 and 2026-11-10."
    killed = agent(
        service, tmp_path, "run", task, "--run-id", "move-1", "--auto-approve", failpoint="between_move_cancel_and_book"
    )
    assert killed.returncode == -signal.SIGKILL
    assert victim["id"] not in {e["id"] for e in events(service)}
```

- Checks that `len(keys) == len(set(keys))` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `set` makes a set: a collection with no repeated items.
- Checks that `double_bookings(service) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `double_bookings`, a function of this file (The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time.).
- Defines the function `test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume`.
- Its parameters:
    - `service`.
    - `tmp_path`.
- Calls `reset`, a function of this file with 1 argument(s); the result is not kept.
  - `reset`, a function of this file.
- Stores the result of calling `events` under the name `before`.
  - `events` from the project's `tests.integration.conftest`.
- Stores the part of `before` picked by `3` under the name `victim`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a text built from pieces (an f-string) under the name `task`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `agent` under the name `killed`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `killed.returncode == -signal.SIGKILL` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `victim['id'] not in {e['id'] for e in events(service)}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `events` from the project's `tests.integration.conftest`.

`tests/integration/test_processes.py`, lines 69 to 82:

```python
    resumed = agent(service, tmp_path, "resume", "move-1", "--auto-approve")
    assert resumed.returncode == 0, resumed.stderr
    after = events(service)
    assert len(after) == len(before)
    assert double_bookings(service) == 0


def test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person(service, tmp_path):
    reset(service)
    task = "Book a 30-minute meeting with alice and bob on 2026-11-09."
    first = agent(service, tmp_path, "run", task, "--run-id", "wait-1")
    assert first.returncode == 5
    assert "waiting for approval" in first.stdout
    assert "wait-1" in agent(service, tmp_path, "unfinished").stdout
```

- Stores the result of calling `agent` under the name `resumed`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `resumed.returncode == 0` is true; if it is not, the test fails with an `AssertionError` and the message `resumed.stderr`.
  - `==` means equal.
- Stores the result of calling `events` under the name `after`.
  - `events` from the project's `tests.integration.conftest`.
- Checks that `len(after) == len(before)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `double_bookings(service) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `double_bookings`, a function of this file (The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time.).
- Defines the function `test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person`.
- Its parameters:
    - `service`.
    - `tmp_path`.
- Calls `reset`, a function of this file with 1 argument(s); the result is not kept.
  - `reset`, a function of this file.
- Stores the text `Book a 30-minute meeting with alice and bob on ...` under the name `task`.
- Stores the result of calling `agent` under the name `first`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `first.returncode == 5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'waiting for approval' in first.stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'wait-1' in agent(service, tmp_path, 'unfinished').stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).

`tests/integration/test_processes.py`, lines 83 to 96:

```python
    pending = agent(service, tmp_path, "pending").stdout
    approval_id = pending.split()[0]
    assert approval_id.startswith("ap-")
    before = len(events(service))
    decided = agent(service, tmp_path, "approve", approval_id, "--resume")
    assert decided.returncode == 0, decided.stderr
    assert len(events(service)) == before + 1


def test_a_rejected_proposal_over_the_command_line_writes_nothing(service, tmp_path):
    reset(service)
    before = len(events(service))
    task = "Book a 30-minute meeting with alice and bob on 2026-11-10."
    agent(service, tmp_path, "run", task, "--run-id", "no-1")
```

- Stores the `stdout` of `agent(service, tmp_path, 'pending')` under the name `pending`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Stores the part of `pending.split()` picked by `0` under the name `approval_id`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Checks that `approval_id.startswith('ap-')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
- Stores the result of calling `len` under the name `before`.
  - `len` counts the items in a collection (or the characters in text).
  - `events` from the project's `tests.integration.conftest`.
- Stores the result of calling `agent` under the name `decided`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `decided.returncode == 0` is true; if it is not, the test fails with an `AssertionError` and the message `decided.stderr`.
  - `==` means equal.
- Checks that `len(events(service)) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - `events` from the project's `tests.integration.conftest`.
- Defines the function `test_a_rejected_proposal_over_the_command_line_writes_nothing`.
- Its parameters:
    - `service`.
    - `tmp_path`.
- Calls `reset`, a function of this file with 1 argument(s); the result is not kept.
  - `reset`, a function of this file.
- Stores the result of calling `len` under the name `before`.
  - `len` counts the items in a collection (or the characters in text).
  - `events` from the project's `tests.integration.conftest`.
- Stores the text `Book a 30-minute meeting with alice and bob on ...` under the name `task`.
- Calls `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.) with 6 argument(s); the result is not kept.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).

`tests/integration/test_processes.py`, lines 97 to 109:

```python
    approval_id = agent(service, tmp_path, "pending").stdout.split()[0]
    done = agent(service, tmp_path, "reject", approval_id, "--resume")
    assert done.returncode == 0
    assert "rejected" in done.stdout
    assert len(events(service)) == before
    assert " written " not in agent(service, tmp_path, "audit", "--run", "no-1").stdout


def test_parallel_requests_with_one_key_over_http_create_one_event_and_other_keys_conflict(service):
    reset(service)
    before = len(events(service))
    body = {"people": ["alice", "bob"], "start": "2026-11-02T16:00", "minutes": 30}
    statuses: list[int] = []
```

- Stores the part of `agent(service, tmp_path, 'p...` picked by `0` under the name `approval_id`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Stores the result of calling `agent` under the name `done`.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Checks that `done.returncode == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'rejected' in done.stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `len(events(service)) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `events` from the project's `tests.integration.conftest`.
- Checks that `' written ' not in agent(service, tmp_path, 'audit', '--run', 'no-1').stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `agent` from the project's `tests.integration.conftest` (Run the `agent` command as a process against the service, with its own database file.).
- Defines the function `test_parallel_requests_with_one_key_over_http_create_one_event_and_other_keys_conflict`.
- Its parameters:
    - `service`.
- Calls `reset`, a function of this file with 1 argument(s); the result is not kept.
  - `reset`, a function of this file.
- Stores the result of calling `len` under the name `before`.
  - `len` counts the items in a collection (or the characters in text).
  - `events` from the project's `tests.integration.conftest`.
- Stores a dictionary with 3 entries under the name `body`.
- Declares `statuses` as a list of a whole number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/integration/test_processes.py`, lines 111 to 123:

```python
    def post(key: str) -> None:
        statuses.append(
            httpx.post(f"{service.url}/events", json=body, headers={"Idempotency-Key": key}, timeout=10).status_code
        )

    threads = [threading.Thread(target=post, args=("parallel-key-1",)) for _ in range(8)]
    threads += [threading.Thread(target=post, args=("parallel-key-2",)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert statuses.count(409) == 2
    assert sorted(set(statuses) - {409}) == [200, 201]
```

- Defines the function `post`. It returns nothing (None).
- Its parameters:
    - `key` holds text.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `httpx.post` sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores a list built by looping under the name `threads`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `threading.Thread` makes a thread.
  - `range` makes the numbers from 0 up to (not including) the given one.
- Updates `threads` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `threading.Thread` makes a thread.
  - `range` makes the numbers from 0 up to (not including) the given one.
- Loop: the indented lines below run once for each item of `threads`; `thread` names the current item.
- Calls `.start(...)` starts a thread or process; the result is not kept.
  - `.start(...)` starts a thread or process.
- Loop: the indented lines below run once for each item of `threads`; `thread` names the current item.
- Calls `.join(...)` glues the pieces of a collection into one text, with the given text between them; the result is not kept.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Checks that `statuses.count(409) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.count(...)` counts how often an item appears.
- Checks that `sorted(set(statuses) - {409}) == [200, 201]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sorted` returns a new list with the items in order.
  - `-` is subtract.
  - `set` makes a set: a collection with no repeated items.

`tests/integration/test_processes.py`, lines 124 to 132:

```python
    assert len(events(service)) == before + 1
    assert double_bookings(service) == 0


def test_sigterm_lets_the_service_finish_and_exit_cleanly(service):
    assert httpx.get(f"{service.url}/health", timeout=5).status_code == 200
    service.process.send_signal(signal.SIGTERM)
    # uvicorn finishes in-flight requests, closes, then re-raises the signal so the exit status says why it stopped
    assert service.process.wait(timeout=30) in (0, -signal.SIGTERM)
```

- Checks that `len(events(service)) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - `events` from the project's `tests.integration.conftest`.
- Checks that `double_bookings(service) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `double_bookings`, a function of this file (The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time.).
- Defines the function `test_sigterm_lets_the_service_finish_and_exit_cleanly`.
- Its parameters:
    - `service`.
- Checks that `httpx.get(f'{service.url}/health', timeout=5).status_code == 200` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `httpx.get` sends an HTTP GET request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.send_signal(...)` sends an operating-system signal to a process with 1 argument(s); the result is not kept.
  - `.send_signal(...)` sends an operating-system signal to a process.
- Checks that `service.process.wait(timeout=30) in (0, -signal.SIGTERM)` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.wait(...)` waits until something happens.

### `tests/live/test_live_models.py`

In its own words: "Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."

35 non-blank lines; it defines `local_server_up`, `first_step`, `test_claude_starts_by_reading_the_calendar_not_by_writing`, `test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects`.

`tests/live/test_live_models.py`, lines 1 to 14:

```python
"""Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from scheduling_agent.application.tools import tool_specs
from scheduling_agent.domain.llm import ChatMessage, ChatRequest
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from tests.conftest import REPO

pytestmark = pytest.mark.live
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `os` (standard library) available.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `tool_specs` (The tool definitions as the model sees them.) from the project module `scheduling_agent.application.tools`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `scheduling_agent.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `scheduling_agent.infrastructure.clock`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `scheduling_agent.infrastructure.model_factory`.
- Brings in `REPO` from the project module `tests.conftest`.
- Stores the `live` of `pytest.mark` under the name `pytestmark`.

`tests/live/test_live_models.py`, lines 16 to 28:

```python
SYSTEM = (REPO / "prompts" / "agent" / "v1.md").read_text().split("---\n", 2)[2].strip()
TASK = "Book a 30-minute meeting with alice and bob on 2026-11-03."


def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def first_step(provider: str):
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": provider}), SystemClock())
```

- Stores the result of calling `(REPO / 'prompts' / 'agent' / 'v1.md').read_tex...` under the name `SYSTEM`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `/` is divide.
- Stores the text `Book a 30-minute meeting with alice and bob on ...` under the name `TASK`.
- Defines the function `local_server_up`. It returns true or false.
- It takes no parameters.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back whether `httpx.get('http://localhost:11434/api/tags', timeout=2).s...` holds to the caller.
  - `==` means equal.
  - `httpx.get` sends an HTTP GET request.
- `except` handler: it runs when the `try` block raised `httpx.HTTPError`.
- Ends the function and gives back the value `False` to the caller.
- Defines the function `first_step`.
- Its parameters:
    - `provider` holds text.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/live/test_live_models.py`, lines 29 to 37:

```python
    request = ChatRequest((ChatMessage.user(TASK),), system=SYSTEM, max_output_tokens=300, tools=tool_specs())
    return model.complete(request)


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_starts_by_reading_the_calendar_not_by_writing():
    response = first_step("anthropic")
    assert response.tool_calls
    assert response.tool_calls[0].name == "find_free_slots"
```

- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
  - `tool_specs` from the project's `scheduling_agent.application.tools` (The tool definitions as the model sees them.).
- Ends the function and gives back the result of calling `model.complete` to the caller.
  - The method `complete` of `model`.
- Defines the function `test_claude_starts_by_reading_the_calendar_not_by_writing`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Stores the result of calling `first_step` under the name `response`.
  - `first_step`, a function of this file.
- Checks that `response.tool_calls` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `response.tool_calls[0].name == 'find_free_slots'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/live/test_live_models.py`, lines 40 to 48:

```python
@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects():
    response = first_step("openai-compatible")
    assert response.tool_calls or response.text
    for call in response.tool_calls:
        assert call.name in {t.name for t in tool_specs()}
        assert isinstance(call.arguments, dict)
```

- Defines the function `test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Stores the result of calling `first_step` under the name `response`.
  - `first_step`, a function of this file.
- Checks that `response.tool_calls or response.text` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Loop: the indented lines below run once for each item of `response.tool_calls`; `call` names the current item.
- Checks that `call.name in {t.name for t in tool_specs()}` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `tool_specs` from the project's `scheduling_agent.application.tools` (The tool definitions as the model sees them.).
- Checks that `isinstance(call.arguments, dict)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/integration --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/integration/test_processes.py::test_sigterm_lets_the_service_finish_and_exit_cleanly

6 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/integration -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
......                                                                   [100%]
6 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/integration -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/integration/test_processes.py::test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice
tests/integration/test_processes.py::test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume
tests/integration/test_processes.py::test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person
tests/integration/test_processes.py::test_a_rejected_proposal_over_the_command_line_writes_nothing
tests/integration/test_processes.py::test_parallel_requests_with_one_key_over_http_create_one_event_and_other_keys_conflict
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/conftest.py` test?

   *Answer:* Shared builders for tests: a fixed clock, a hashing embedder and a ready agent kit on in-memory databases.

2. What does `tests/e2e/conftest.py` test?

   *Answer:* The e2e tests reuse the fixture that starts the calendar service as a real process.

3. What does `tests/e2e/test_lesson_scenario.py` test?

   *Answer:* The lesson's step 6 through the real HTTP service: 30 tasks, three runs each, judged by the calendar's end state.

4. What does `tests/integration/conftest.py` test?

   *Answer:* Fixtures that start the calendar service as a real process on a free port.

5. What does `tests/integration/test_processes.py` test?

   *Answer:* The calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
