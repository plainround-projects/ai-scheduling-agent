# Python source, the interfaces layer

## What it is

This note walks through every Python file of the `interfaces` layer of `scheduling_agent`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **interfaces** layer is the outermost: the command-line program and, where present, the HTTP service. It reads the command line or a request, builds the adapters, calls a use case and turns the result into output and an exit code.

## Why this repository uses it

It is the only layer allowed to know about everything below it, and nothing depends on it. That keeps start-up wiring in one place.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/interfaces/__init__.py` | 1 non-blank lines |
| `src/scheduling_agent/interfaces/calendar_api.py` | 103 non-blank lines |
| `src/scheduling_agent/interfaces/calendar_server.py` | 36 non-blank lines |
| `src/scheduling_agent/interfaces/cli.py` | 180 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/scheduling_agent/interfaces/__init__.py`

In its own words: "Command-line programs. They wire adapters into use cases and own exit codes."

1 non-blank lines.

`src/scheduling_agent/interfaces/__init__.py`, lines 1 to 1:

```python
"""Command-line programs. They wire adapters into use cases and own exit codes."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/scheduling_agent/interfaces/calendar_api.py`

In its own words: "The calendar service over HTTP: free slots, one event, book and cancel with an Idempotency-Key header."

103 non-blank lines; it defines `BookRequest`, `event_json`, `create_app`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 1 to 13:

```python
"""The calendar service over HTTP: free slots, one event, book and cancel with an Idempotency-Key header."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, time
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from scheduling_agent.domain.calendar import Event
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `date`, `datetime`, `time` from the standard library module `datetime`.
- Brings in `Annotated`, `Any` from the standard library module `typing`.
- Brings in `FastAPI`, `Header`, `HTTPException`, `Query`, `Response` from the installed package module `fastapi`.
- Brings in `BaseModel`, `ConfigDict`, `Field` from the installed package module `pydantic`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 14 to 25:

```python
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
```

- Brings in `AlreadyCancelled` (The event is already cancelled.), `CalendarError` (The calendar refused or could not do what was asked.), `IdempotencyConflict` (An Idempotency-Key was reused for a different request.), `InvalidSlot` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.), `SlotUnavailable` (A person is already busy at that time.), `UnknownEvent` (No event with that id.), `UnknownPerson` (A name that is not one of the calendar's people.) from the project module `scheduling_agent.domain.errors`.
- Brings in `SqliteCalendar` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.) from the project module `scheduling_agent.infrastructure.calendar_db`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 26 to 39:

```python
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
```

- Declares `_STATUS` as a dictionary from type of the project type `CalendarError` to a whole number and sets it to a dictionary with 6 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `BookRequest`. It builds on pydantic's `BaseModel` (a class whose fields are validated). The author's own description: "The body of POST /events."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `ConfigDict` under the name `model_config`.
  - `ConfigDict` from the installed package module `pydantic`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 40 to 53:

```python
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
```

- Declares `people` as a list of text with extra rules.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `Field` from the installed package module `pydantic`.
- Declares `start` as a date and time.
- Declares `minutes` as a whole number with extra rules.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `Field` from the installed package module `pydantic`.
- Defines the function `event_json`. It returns a dictionary from text to any value. The author's own description: "An event as the API returns it."
- Its parameters:
    - `event` holds the project type `Event`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a dictionary with 5 entries to the caller.
  - `list` makes a list (a copy when given a collection).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).

`src/scheduling_agent/interfaces/calendar_api.py`, lines 56 to 66:

```python
def create_app(calendar: SqliteCalendar, reset: Callable[[], None] | None = None) -> FastAPI:
    """Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data."""
    app = FastAPI(title="calendar-service", version="0.1.0")

    def fail(error: CalendarError) -> HTTPException:
        status = _STATUS.get(type(error), 400)
        return HTTPException(status_code=status, detail={"error": type(error).__name__, "message": str(error)})

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "people": len(calendar.people())}
```

- Defines the function `create_app`. It returns `FastAPI`. The author's own description: "Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data."
- Its parameters:
    - `calendar` holds the project type `SqliteCalendar`.
    - `reset` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `FastAPI` under the name `app`.
  - `FastAPI` from the installed package module `fastapi`.
- Defines the function `fail`. It returns `HTTPException`.
- Its parameters:
    - `error` holds the project type `CalendarError`.
- Stores the result of calling `_STATUS.get` under the name `status`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `type` gives the type (class) of a value.
- Ends the function and gives back the result of calling `HTTPException` to the caller.
  - `HTTPException` from the installed package module `fastapi`.
  - `str` turns a value into text.
  - `type` gives the type (class) of a value.
- Defines the function `health`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a dictionary from text to any object.
- It takes no parameters.
- Ends the function and gives back a dictionary with 2 entries to the caller.
  - `len` counts the items in a collection (or the characters in text).
  - The method `people` of `calendar`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 68 to 80:

```python
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
```

- Defines the function `people`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a list of text.
- It takes no parameters.
- Ends the function and gives back the result of calling `calendar.people` to the caller.
  - The method `people` of `calendar`.
- Defines the function `free_slots`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a dictionary from text to a list of text.
- Its parameters:
    - `people` holds a list of text with extra rules.
    - `first_day` holds a calendar date.
    - `last_day` holds a calendar date.
    - `minutes` holds a whole number with extra rules.
    - `not_before` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `not_after` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).

`src/scheduling_agent/interfaces/calendar_api.py`, lines 81 to 94:

```python
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
```

- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `calendar.free_slots` under the name `slots`.
  - The method `free_slots` of `calendar`.
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Raises an error: the result of calling `fail`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `fail`, a function defined in this file or passed in.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Defines the function `events`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a list of a dictionary from text to any value.
- It takes no parameters.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `event_json`, a function of this file (An event as the API returns it.).
  - The method `active_events` of `calendar`.
- Defines the function `get_event`. `@app.get(...)` registers the function as the handler of HTTP GET requests for that path. It returns a dictionary from text to any value.
- Its parameters:
    - `event_id` holds text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `event_json` to the caller.
  - `event_json`, a function of this file (An event as the API returns it.).
  - The method `get_event` of `calendar`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 95 to 108:

```python
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
```

- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Raises an error: the result of calling `fail`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `fail`, a function defined in this file or passed in.
- Defines the function `book`. `@app.post(...)` registers the function as the handler of HTTP POST requests for that path. It returns a dictionary from text to any value.
- Its parameters:
    - `body` holds the project type `BookRequest`.
    - `response` holds `Response`.
    - `idempotency_key` holds text with extra rules.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `calendar.book` under the name `result`.
  - The method `book` of `calendar`.
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Raises an error: the result of calling `fail`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `fail`, a function defined in this file or passed in.
- Stores one of two values, chosen by a condition under the name `response.status_code`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back a dictionary with 2 entries to the caller.
  - `event_json`, a function of this file (An event as the API returns it.).

`src/scheduling_agent/interfaces/calendar_api.py`, lines 110 to 122:

```python
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
```

- Defines the function `cancel`. `@app.post(...)` registers the function as the handler of HTTP POST requests for that path. It returns a dictionary from text to any value.
- Its parameters:
    - `event_id` holds text.
    - `idempotency_key` holds text with extra rules.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `calendar.cancel` under the name `result`.
  - The method `cancel` of `calendar`.
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Raises an error: the result of calling `fail`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `fail`, a function defined in this file or passed in.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back a dictionary with 2 entries to the caller.
  - `event_json`, a function of this file (An event as the API returns it.).
- Decision: the indented lines below run only when `reset is not None` is true.
  - `is not` means not the same object.
- Defines the function `admin_reset`. `@app.post(...)` registers the function as the handler of HTTP POST requests for that path. It returns a dictionary from text to text.
- It takes no parameters.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 123 to 126:

```python
            reset()
            return {"status": "reseeded"}

    return app
```

- Calls `reset`, a function defined in this file or passed in; the result is not kept.
  - `reset`, a function defined in this file or passed in.
- Ends the function and gives back a dictionary with 1 entry to the caller.
- Ends the function and gives back the value named `app` to the caller.

### `src/scheduling_agent/interfaces/calendar_server.py`

In its own words: "The `calendar-service` command: create the database and serve the calendar over HTTP."

36 non-blank lines; it defines `main`.

`src/scheduling_agent/interfaces/calendar_server.py`, lines 1 to 14:

```python
"""The `calendar-service` command: create the database and serve the calendar over HTTP."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import uvicorn

from scheduling_agent.infrastructure.calendar_db import SqliteCalendar
from scheduling_agent.infrastructure.calendar_seed import init_calendar, reset_calendar
from scheduling_agent.infrastructure.env import ConfigurationError
from scheduling_agent.infrastructure.logging import configure_logging
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `argparse` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Makes the module `uvicorn` (installed package) available.
- Brings in `SqliteCalendar` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.) from the project module `scheduling_agent.infrastructure.calendar_db`.
- Brings in `init_calendar` (Create the tables and load the seed if the database has no people yet.), `reset_calendar` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).) from the project module `scheduling_agent.infrastructure.calendar_seed`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) from the project module `scheduling_agent.infrastructure.logging`.

`src/scheduling_agent/interfaces/calendar_server.py`, lines 15 to 28:

```python
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.sqlite import connect
from scheduling_agent.interfaces.calendar_api import create_app


def main(argv: Sequence[str] | None = None) -> int:
    """`calendar-service init-db` creates and seeds the database; `calendar-service serve` runs the HTTP service."""
    parser = argparse.ArgumentParser(prog="calendar-service", description="The sample calendar service.")
    parser.add_argument("command", choices=["init-db", "serve"])
    args = parser.parse_args(argv)
    try:
        settings = AgentSettings.from_env()
    except ConfigurationError as error:
        print(f"calendar-service: {error}", file=sys.stderr)
```

- Brings in `AgentSettings` (Where things live and how a run is capped. See env.example for each variable.) from the project module `scheduling_agent.infrastructure.settings`.
- Brings in `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Brings in `create_app` (Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data.) from the project module `scheduling_agent.interfaces.calendar_api`.
- Defines the function `main`. It returns a whole number. The author's own description: "`calendar-service init-db` creates and seeds the database; `calendar-service serve` runs the HTTP service."
- Its parameters:
    - `argv` holds anything that behaves like a list of text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `argparse.ArgumentParser` under the name `parser`.
  - `argparse.ArgumentParser` from the standard library module `argparse`.
- Calls the method `add_argument` of `parser` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `parser`.
- Stores the result of calling `parser.parse_args` under the name `args`.
  - The method `parse_args` of `parser`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `AgentSettings.from_env` under the name `settings`.
  - The method `from_env` of `AgentSettings`.
- `except` handler: it runs when the `try` block raised the project type `ConfigurationError`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/interfaces/calendar_server.py`, lines 29 to 40:

```python
        return 2
    configure_logging(settings.log_level)
    connection = connect(settings.calendar_db)
    init_calendar(connection, settings.sql_dir)
    if args.command == "init-db":
        print(f"calendar database ready at {settings.calendar_db}")
        return 0
    reset = (lambda: reset_calendar(connection, settings.sql_dir)) if settings.allow_reset else None
    app = create_app(SqliteCalendar(connection), reset)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, timeout_graceful_shutdown=10)
    connection.close()
    return 0
```

- Ends the function and gives back the number `2` to the caller.
- Calls `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 1 argument(s); the result is not kept.
  - `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Stores the result of calling `connect` under the name `connection`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).
- Calls `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.) with 2 argument(s); the result is not kept.
  - `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.).
- Decision: the indented lines below run only when `args.command == 'init-db'` is true.
  - `==` means equal.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the number `0` to the caller.
- Stores one of two values, chosen by a condition under the name `reset`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `lambda args: expression` is a small unnamed function written inline.
  - `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).).
- Stores the result of calling `create_app` under the name `app`.
  - `create_app` from the project's `scheduling_agent.interfaces.calendar_api` (Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data.).
  - `SqliteCalendar` from the project's `scheduling_agent.infrastructure.calendar_db` (Reads and idempotent writes. Every write and its idempotency key are committed in one transaction.).
- Calls `uvicorn.run` starts the web server and keeps running with 5 argument(s); the result is not kept.
  - `uvicorn.run` starts the web server and keeps running.
- Calls `.close(...)` closes a file, connection or resource; the result is not kept.
  - `.close(...)` closes a file, connection or resource.
- Ends the function and gives back the number `0` to the caller.

`src/scheduling_agent/interfaces/calendar_server.py`, lines 43 to 44:

```python
if __name__ == "__main__":
    sys.exit(main())
```

- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `sys.exit` from the standard library module `sys` with 1 argument(s); the result is not kept.
  - `sys.exit` from the standard library module `sys`.
  - `main`, a function of this file (`calendar-service init-db` creates and seeds the database; `calendar-service serve` runs the HTTP service.).

### `src/scheduling_agent/interfaces/cli.py`

In its own words: "The `agent` command: run a task, approve or reject a write, resume a run, tell it a preference, run the task set."

180 non-blank lines; it defines `build_parser`, `_kit`, `_show`, `_drive_with_approval`, `_exit`, `_tasks`, `render_task_report`, `_decide`, `_inspect`, `_run`, `main`.

`src/scheduling_agent/interfaces/cli.py`, lines 1 to 14:

```python
"""The `agent` command: run a task, approve or reject a write, resume a run, tell it a preference, run the task set."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from collections.abc import Sequence

from scheduling_agent.application.agent import UnknownRun
from scheduling_agent.application.task_runner import AgentKit, ExpectedWritesApprover, TaskResult, TaskRunner
from scheduling_agent.domain.errors import ApprovalError, DomainError
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `argparse` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `defaultdict` from the standard library module `collections`.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `UnknownRun` (No saved run with that id.) from the project module `scheduling_agent.application.agent`.
- Brings in `AgentKit` (One agent with the stores it was built on, so a runner can read what it did.), `ExpectedWritesApprover` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.), `TaskResult` (One attempt at one task.), `TaskRunner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.) from the project module `scheduling_agent.application.task_runner`.
- Brings in `ApprovalError` (An approval is missing, not approved, or was granted for a different proposal.), `DomainError` (Base class for every error this package raises on purpose.) from the project module `scheduling_agent.domain.errors`.

`src/scheduling_agent/interfaces/cli.py`, lines 15 to 28:

```python
from scheduling_agent.domain.prompts import PromptNotFound
from scheduling_agent.domain.run import RunState, RunStatus
from scheduling_agent.domain.tasks import InvalidTasks
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.env import ConfigurationError
from scheduling_agent.infrastructure.files import load_tasks
from scheduling_agent.infrastructure.logging import configure_logging
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.shutdown import ShutdownSignal
from scheduling_agent.infrastructure.sqlite import connect
from scheduling_agent.infrastructure.wiring import build_calendar, build_embedder, build_kit

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_AWAITING, EXIT_STOPPED = 0, 1, 2, 5, 6
```

- Brings in `PromptNotFound` (No prompt file for that name and version, or the file's version line does not match.) from the project module `scheduling_agent.domain.prompts`.
- Brings in `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.), `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Brings in `InvalidTasks` (The task file breaks a rule of the lesson.) from the project module `scheduling_agent.domain.tasks`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `scheduling_agent.infrastructure.clock`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `load_tasks` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.) from the project module `scheduling_agent.infrastructure.files`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) from the project module `scheduling_agent.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `scheduling_agent.infrastructure.model_factory`.
- Brings in `AgentSettings` (Where things live and how a run is capped. See env.example for each variable.) from the project module `scheduling_agent.infrastructure.settings`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `scheduling_agent.infrastructure.shutdown`.
- Brings in `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Brings in `build_calendar` (The HTTP client for the calendar service named in the settings.), `build_embedder` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).), `build_kit` (One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither.) from the project module `scheduling_agent.infrastructure.wiring`.
- Stores a tuple of 5 item(s) under the name `(EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EX...`.

`src/scheduling_agent/interfaces/cli.py`, lines 29 to 42:

```python
_log = logging.getLogger("agent")


def build_parser() -> argparse.ArgumentParser:
    """The `agent` argument parser."""
    parser = argparse.ArgumentParser(prog="agent", description="A scheduling agent that asks before it writes.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one task")
    run.add_argument("task")
    run.add_argument("--session", default="cli")
    run.add_argument("--run-id")
    run.add_argument(
        "--auto-approve", action="store_true", help="approve every proposal without asking (demos and tests)"
    )
```

- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the function `build_parser`. It returns `argparse.ArgumentParser`. The author's own description: "The `agent` argument parser."
- It takes no parameters.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `argparse.ArgumentParser` under the name `parser`.
  - `argparse.ArgumentParser` from the standard library module `argparse`.
- Stores the result of calling `parser.add_subparsers` under the name `sub`.
  - The method `add_subparsers` of `parser`.
- Stores the result of calling `sub.add_parser` under the name `run`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `run` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `run`.
- Calls the method `add_argument` of `run` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `run`.
- Calls the method `add_argument` of `run` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `run`.
- Calls the method `add_argument` of `run` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `run`.

`src/scheduling_agent/interfaces/cli.py`, lines 43 to 56:

```python
    resume = sub.add_parser("resume", help="continue a saved run from its last checkpoint")
    resume.add_argument("run_id")
    resume.add_argument("--auto-approve", action="store_true")
    for name in ("approve", "reject"):
        decide = sub.add_parser(name, help=f"{name} a pending proposal")
        decide.add_argument("approval_id")
        decide.add_argument("--resume", action="store_true", help="resume the run right away")
    sub.add_parser("pending", help="list proposals waiting for a decision")
    sub.add_parser("unfinished", help="list runs that a crash left unfinished")
    audit = sub.add_parser("audit", help="print the audit log")
    audit.add_argument("--run")
    tell = sub.add_parser("tell", help="tell the agent something about a person's calendar")
    tell.add_argument("person")
    tell.add_argument("statement")
```

- Stores the result of calling `sub.add_parser` under the name `resume`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `resume` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `resume`.
- Calls the method `add_argument` of `resume` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `resume`.
- Loop: the indented lines below run once for each item of `('approve', 'reject')`; `name` names the current item.
- Stores the result of calling `sub.add_parser` under the name `decide`.
  - The method `add_parser` of `sub`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls the method `add_argument` of `decide` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `decide`.
- Calls the method `add_argument` of `decide` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `decide`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Stores the result of calling `sub.add_parser` under the name `audit`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `audit` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `audit`.
- Stores the result of calling `sub.add_parser` under the name `tell`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `tell` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `tell`.
- Calls the method `add_argument` of `tell` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `tell`.

`src/scheduling_agent/interfaces/cli.py`, lines 57 to 70:

```python
    tell.add_argument("--session", default="cli")
    sub.add_parser("memory", help="print what the agent remembers")
    forget = sub.add_parser("forget", help="delete everything the agent remembers about a person")
    forget.add_argument("person")
    tasks = sub.add_parser("tasks", help="run the task set against the calendar service and judge by end state")
    tasks.add_argument("--runs", type=int, default=3)
    tasks.add_argument("--only", help="a single task id")
    return parser


def _kit(settings: AgentSettings) -> AgentKit:
    clock = SystemClock()
    model = build_chat_model(ModelSettings.from_env(), clock)
    return build_kit(settings, model, clock, build_embedder(settings))
```

- Calls the method `add_argument` of `tell` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `tell`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Stores the result of calling `sub.add_parser` under the name `forget`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `forget` with 1 argument(s); the result is not kept.
  - The method `add_argument` of `forget`.
- Stores the result of calling `sub.add_parser` under the name `tasks`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `tasks` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `tasks`.
- Calls the method `add_argument` of `tasks` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `tasks`.
- Ends the function and gives back the value named `parser` to the caller.
- Defines the function `_kit`. It returns the project type `AgentKit`.
- Its parameters:
    - `settings` holds the project type `AgentSettings`.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
- Ends the function and gives back the result of calling `build_kit` to the caller.
  - `build_kit` from the project's `scheduling_agent.infrastructure.wiring` (One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither.).
  - `build_embedder` from the project's `scheduling_agent.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).

`src/scheduling_agent/interfaces/cli.py`, lines 73 to 84:

```python
def _show(state: RunState) -> None:
    print(f"run {state.run_id}: {state.status.value} after {state.steps} step(s), {state.tokens} tokens")
    if state.status is RunStatus.AWAITING_APPROVAL and state.pending is not None:
        print(f"  waiting for approval {state.pending.approval_id}: {state.pending.proposal.canonical()}")
        print(f"  decide with: agent approve {state.pending.approval_id} --resume   (or: agent reject ...)")
    if state.final_text:
        print(f"  {state.final_text}")


def _drive_with_approval(kit: AgentKit, state: RunState, auto: bool) -> RunState:
    clock = SystemClock()
    while auto and state.status is RunStatus.AWAITING_APPROVAL and state.pending is not None:
```

- Defines the function `_show`. It returns nothing (None).
- Its parameters:
    - `state` holds the project type `RunState`.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `state.status is RunStatus.AWAITING_APPROVAL and state.pending is no...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `is not` means not the same object.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `canonical` of the project's `Proposal` (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `state.final_text` is true.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_drive_with_approval`. It returns the project type `RunState`.
- Its parameters:
    - `kit` holds the project type `AgentKit`.
    - `state` holds the project type `RunState`.
    - `auto` holds true or false.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Loop: the indented lines below repeat as long as `auto and state.status is RunStatus.AWAITING_APPROVAL and ...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `is not` means not the same object.

`src/scheduling_agent/interfaces/cli.py`, lines 85 to 98:

```python
        kit.approvals.decide(state.pending.approval_id, True, "auto-approve", clock.now())
        state = kit.agent.resume(state.run_id)
    return state


def _exit(state: RunState) -> int:
    return {RunStatus.AWAITING_APPROVAL: EXIT_AWAITING, RunStatus.STOPPED: EXIT_STOPPED}.get(state.status, EXIT_OK)


def _tasks(args: argparse.Namespace, settings: AgentSettings, shutdown: ShutdownSignal) -> int:
    tasks = load_tasks(settings.tasks_path)
    if args.only:
        tasks = [t for t in tasks if t.id == args.only]
    clock = SystemClock()
```

- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `clock`.
- Stores the result of calling `kit.agent.resume` under the name `state`.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Ends the function and gives back the value named `state` to the caller.
- Defines the function `_exit`. It returns a whole number.
- Its parameters:
    - `state` holds the project type `RunState`.
- Ends the function and gives back the result of calling `{RunStatus.AWAITING_APPROVAL: EXIT_AWAITING, Ru...` to the caller.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Defines the function `_tasks`. It returns a whole number.
- Its parameters:
    - `args` holds `argparse.Namespace`.
    - `settings` holds the project type `AgentSettings`.
    - `shutdown` holds the project type `ShutdownSignal`.
- Stores the result of calling `load_tasks` under the name `tasks`.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
- Decision: the indented lines below run only when `args.only` is true.
- Stores a list built by looping under the name `tasks`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`src/scheduling_agent/interfaces/cli.py`, lines 99 to 111:

```python
    calendar = build_calendar(settings)
    model_settings = ModelSettings.from_env()
    embedder = build_embedder(settings)

    def build() -> AgentKit:
        return build_kit(
            settings, build_chat_model(model_settings, clock), clock, embedder, calendar, connect(":memory:")
        )

    runner = TaskRunner(calendar, build, ExpectedWritesApprover(), clock)
    results = runner.run_all(tasks, args.runs, lambda: shutdown.requested)
    print(render_task_report(results, args.runs))
    return EXIT_OK if results and all(r.passed for r in results) else EXIT_ERROR
```

- Stores the result of calling `build_calendar` under the name `calendar`.
  - `build_calendar` from the project's `scheduling_agent.infrastructure.wiring` (The HTTP client for the calendar service named in the settings.).
- Stores the result of calling `ModelSettings.from_env` under the name `model_settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_embedder` under the name `embedder`.
  - `build_embedder` from the project's `scheduling_agent.infrastructure.wiring` (`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on).).
- Defines the function `build`. It returns the project type `AgentKit`.
- It takes no parameters.
- Ends the function and gives back the result of calling `build_kit` to the caller.
  - `build_kit` from the project's `scheduling_agent.infrastructure.wiring` (One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither.).
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).
- Stores the result of calling `TaskRunner` under the name `runner`.
  - `TaskRunner` from the project's `scheduling_agent.application.task_runner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.).
  - `ExpectedWritesApprover` from the project's `scheduling_agent.application.task_runner` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.).
- Stores the result of calling `runner.run_all` under the name `results`.
  - The method `run_all` of the project's `TaskRunner` (Every task `repeats` times, in order.).
  - `lambda args: expression` is a small unnamed function written inline.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `render_task_report`, a function of this file (Pass rate per task across the runs, and the totals the lesson asks for.).
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`src/scheduling_agent/interfaces/cli.py`, lines 114 to 125:

```python
def render_task_report(results: list[TaskResult], runs: int) -> str:
    """Pass rate per task across the runs, and the totals the lesson asks for."""
    by_task: dict[str, list[TaskResult]] = defaultdict(list)
    for result in results:
        by_task[result.task_id].append(result)
    lines = ["task                 passed  steps  tokens  writes without approval  ended"]
    for task_id, items in by_task.items():
        passed = sum(r.passed for r in items)
        steps = round(sum(r.steps for r in items) / len(items))
        tokens = round(sum(r.tokens for r in items) / len(items))
        bad = sum(r.writes_without_approval for r in items)
        ended = ",".join(sorted({f"{r.status.value}{':' + r.stop_reason if r.stop_reason else ''}" for r in items}))
```

- Defines the function `render_task_report`. It returns text. The author's own description: "Pass rate per task across the runs, and the totals the lesson asks for."
- Its parameters:
    - `results` holds a list of the project type `TaskResult`.
    - `runs` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `by_task` as a dictionary from text to a list of the project type `TaskResult` and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
- Loop: the indented lines below run once for each item of `results`; `result` names the current item.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a list of 1 item(s) under the name `lines`.
- Loop: the indented lines below run once for each item of `by_task.items()`; `(task_id, items)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Stores the result of calling `sum` under the name `passed`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `round` under the name `steps`.
  - `round` rounds a number.
  - `/` is divide.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `round` under the name `tokens`.
  - `round` rounds a number.
  - `/` is divide.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `sum` under the name `bad`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `','.join` under the name `ended`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `+` is add.

`src/scheduling_agent/interfaces/cli.py`, lines 126 to 139:

```python
        lines.append(f"{task_id:<20} {passed}/{len(items):<5} {steps:>5} {tokens:>7} {bad:>24}  {ended}")
    total = sum(r.passed for r in results)
    lines.append(f"\ntasks passed: {total}/{len(results)} attempts ({len(by_task)} tasks x {runs} runs)")
    lines.append(f"writes without an approval: {sum(r.writes_without_approval for r in results)}")
    granted = sum(r.approvals_granted for r in results)
    lines.append(f"approvals granted: {granted}, rejected: {sum(r.approvals_rejected for r in results)}")
    return "\n".join(lines)


def _decide(kit: AgentKit, args: argparse.Namespace) -> int:
    approval = kit.approvals.decide(args.approval_id, args.command == "approve", "cli", SystemClock().now())
    print(f"{approval.id}: {approval.status.value} ({approval.proposal.canonical()})")
    if args.resume:
        state = kit.agent.resume(approval.run_id)
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of calling `sum` under the name `total`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `sum` under the name `granted`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Ends the function and gives back the result of calling `'\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `_decide`. It returns a whole number.
- Its parameters:
    - `kit` holds the project type `AgentKit`.
    - `args` holds `argparse.Namespace`.
- Stores the result of calling `kit.approvals.decide` under the name `approval`.
  - The method `decide` of `kit.approvals`.
  - `==` means equal.
  - The method `now` of `SystemClock()`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `canonical` of the project's `Proposal` (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
- Decision: the indented lines below run only when `args.resume` is true.
- Stores the result of calling `kit.agent.resume` under the name `state`.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).

`src/scheduling_agent/interfaces/cli.py`, lines 140 to 153:

```python
        _show(state)
        return _exit(state)
    return EXIT_OK


def _inspect(kit: AgentKit, args: argparse.Namespace) -> int:
    if args.command == "pending":
        for approval in kit.approvals.pending():
            print(f"{approval.id}  run {approval.run_id}  step {approval.step}  {approval.proposal.canonical()}")
    elif args.command == "unfinished":
        for run_id in kit.checkpoints.unfinished():
            print(run_id)
    elif args.command == "audit":
        for line in kit.audit.lines(args.run):
```

- Calls `_show`, a function of this file with 1 argument(s); the result is not kept.
  - `_show`, a function of this file.
- Ends the function and gives back the result of calling `_exit` to the caller.
  - `_exit`, a function of this file.
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Defines the function `_inspect`. It returns a whole number.
- Its parameters:
    - `kit` holds the project type `AgentKit`.
    - `args` holds `argparse.Namespace`.
- Decision: the indented lines below run only when `args.command == 'pending'` is true.
  - `==` means equal.
- Loop: the indented lines below run once for each item of `kit.approvals.pending()`; `approval` names the current item.
  - The method `pending` of `kit.approvals`.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `canonical` of the project's `Proposal` (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
- Decision: the indented lines below run only when `args.command == 'unfinished'` is true.
  - `==` means equal.
- Loop: the indented lines below run once for each item of `kit.checkpoints.unfinished()`; `run_id` names the current item.
  - The method `unfinished` of `kit.checkpoints`.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
- Decision: the indented lines below run only when `args.command == 'audit'` is true.
  - `==` means equal.
- Loop: the indented lines below run once for each item of `kit.audit.lines(args.run)`; `line` names the current item.
  - The method `lines` of `kit.audit`.

`src/scheduling_agent/interfaces/cli.py`, lines 154 to 167:

```python
            stamp = f"{line.at:%Y-%m-%dT%H:%M:%S}"
            print(f"{stamp} run {line.run_id} step {line.step} {line.action} {line.outcome} {line.detail}")
    else:
        facts = [
            {"person": f.person, "kind": f.kind.value, "value": f.value, "text": f.text, "stated_on": str(f.stated_on)}
            for f in kit.memory.facts()
        ]
        print(json.dumps(facts, indent=2))
    return EXIT_OK


def _run(args: argparse.Namespace, settings: AgentSettings, shutdown: ShutdownSignal) -> int:
    if args.command == "tasks":
        return _tasks(args, settings, shutdown)
```

- Stores a text built from pieces (an f-string) under the name `stamp`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores a list built by looping under the name `facts`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - The method `facts` of `kit.memory`.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `json.dumps` turns Python data into JSON text.
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Defines the function `_run`. It returns a whole number.
- Its parameters:
    - `args` holds `argparse.Namespace`.
    - `settings` holds the project type `AgentSettings`.
    - `shutdown` holds the project type `ShutdownSignal`.
- Decision: the indented lines below run only when `args.command == 'tasks'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `_tasks` to the caller.
  - `_tasks`, a function of this file.

`src/scheduling_agent/interfaces/cli.py`, lines 168 to 181:

```python
    kit = _kit(settings)
    if args.command == "run":
        state = _drive_with_approval(kit, kit.agent.start(args.task, args.session, args.run_id), args.auto_approve)
        _show(state)
        return _exit(state)
    if args.command == "resume":
        state = _drive_with_approval(kit, kit.agent.resume(args.run_id), args.auto_approve)
        _show(state)
        return _exit(state)
    if args.command in ("approve", "reject"):
        return _decide(kit, args)
    if args.command == "tell":
        fact = kit.memory.remember(args.person.lower(), args.statement, args.session)
        print(f"remembered: {fact.text}" if fact else "that states nothing about their calendar that I keep")
```

- Stores the result of calling `_kit` under the name `kit`.
  - `_kit`, a function of this file.
- Decision: the indented lines below run only when `args.command == 'run'` is true.
  - `==` means equal.
- Stores the result of calling `_drive_with_approval` under the name `state`.
  - `_drive_with_approval`, a function of this file.
  - `.start(...)` starts a thread or process.
- Calls `_show`, a function of this file with 1 argument(s); the result is not kept.
  - `_show`, a function of this file.
- Ends the function and gives back the result of calling `_exit` to the caller.
  - `_exit`, a function of this file.
- Decision: the indented lines below run only when `args.command == 'resume'` is true.
  - `==` means equal.
- Stores the result of calling `_drive_with_approval` under the name `state`.
  - `_drive_with_approval`, a function of this file.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Calls `_show`, a function of this file with 1 argument(s); the result is not kept.
  - `_show`, a function of this file.
- Ends the function and gives back the result of calling `_exit` to the caller.
  - `_exit`, a function of this file.
- Decision: the indented lines below run only when `args.command in ('approve', 'reject')` is true.
  - `in` means is contained in.
- Ends the function and gives back the result of calling `_decide` to the caller.
  - `_decide`, a function of this file.
- Decision: the indented lines below run only when `args.command == 'tell'` is true.
  - `==` means equal.
- Stores the result of calling `kit.memory.remember` under the name `fact`.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
  - `.lower(...)` turns text into lower case.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/interfaces/cli.py`, lines 182 to 195:

```python
        return EXIT_OK
    if args.command == "forget":
        print(f"forgot {kit.memory.forget(args.person.lower())} fact(s) about {args.person}")
        return EXIT_OK
    return _inspect(kit, args)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 5 waiting for approval, 6 stopped by a budget)."""
    args = build_parser().parse_args(argv)
    try:
        settings = AgentSettings.from_env()
        configure_logging(settings.log_level)
        shutdown = ShutdownSignal()
```

- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Decision: the indented lines below run only when `args.command == 'forget'` is true.
  - `==` means equal.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `forget` of the project's `MemoryService` (Delete every fact about a person from storage; returns how many were removed.).
  - `.lower(...)` turns text into lower case.
- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Ends the function and gives back the result of calling `_inspect` to the caller.
  - `_inspect`, a function of this file.
- Defines the function `main`. It returns a whole number. The author's own description: "Entry point: returns the exit code (0 ok, 2 configuration, 5 waiting for approval, 6 stopped by a budget)."
- Its parameters:
    - `argv` holds anything that behaves like a list of text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `build_parser().parse_args` under the name `args`.
  - The method `parse_args` of `build_parser()`.
  - `build_parser`, a function of this file (The `agent` argument parser.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `AgentSettings.from_env` under the name `settings`.
  - The method `from_env` of `AgentSettings`.
- Calls `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 1 argument(s); the result is not kept.
  - `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `scheduling_agent.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).

`src/scheduling_agent/interfaces/cli.py`, lines 196 to 209:

```python
        shutdown.install()
        return _run(args, settings, shutdown)
    except (ConfigurationError, PromptNotFound, InvalidTasks) as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except (UnknownRun, ApprovalError) as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_ERROR
    except DomainError as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
```

- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Ends the function and gives back the result of calling `_run` to the caller.
  - `_run`, a function of this file.
- `except` handler: it runs when the `try` block raised `(ConfigurationError, PromptNotFound, InvalidTasks)`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_CONFIG` to the caller.
- `except` handler: it runs when the `try` block raised `(UnknownRun, ApprovalError)`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_ERROR` to the caller.
- `except` handler: it runs when the `try` block raised the project type `DomainError`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_ERROR` to the caller.
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.

`src/scheduling_agent/interfaces/cli.py`, lines 210 to 210:

```python
    sys.exit(main())
```

- Calls `sys.exit` from the standard library module `sys` with 1 argument(s); the result is not kept.
  - `sys.exit` from the standard library module `sys`.
  - `main`, a function of this file (Entry point: returns the exit code (0 ok, 2 configuration, 5 waiting for approval, 6 stopped by a budget).).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import scheduling_agent.interfaces.__init__; print(scheduling_agent.interfaces.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Command-line programs. They wire adapters into use cases and own exit codes.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/scheduling_agent/interfaces').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
calendar_api.py 3
calendar_server.py 1
cli.py 11
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

- **Common mistakes with this layer.** Putting rules in the command-line code, forgetting to return the right exit code, or printing instead of returning values so tests cannot check them. Here each command returns an exit code and prints through small render helpers.

## Check yourself

1. What is the job of `src/scheduling_agent/interfaces/__init__.py`?

   *Answer:* Command-line programs. They wire adapters into use cases and own exit codes.

2. What is the job of `src/scheduling_agent/interfaces/calendar_api.py`?

   *Answer:* The calendar service over HTTP: free slots, one event, book and cancel with an Idempotency-Key header.

3. What is the job of `src/scheduling_agent/interfaces/calendar_server.py`?

   *Answer:* The `calendar-service` command: create the database and serve the calendar over HTTP.

4. What is the job of `src/scheduling_agent/interfaces/cli.py`?

   *Answer:* The `agent` command: run a task, approve or reject a write, resume a run, tell it a preference, run the task set.

5. Which layer is `src/scheduling_agent/interfaces/`, and what may it import?

   *Answer:* The outermost layer; it may import everything below it.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
