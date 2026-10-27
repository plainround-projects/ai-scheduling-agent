# Python source, the infrastructure layer (part 2 of 2)

## What it is

This note walks through every Python file of the `infrastructure` layer of `scheduling_agent`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **infrastructure** layer is the adapters: the code that touches the world. Files, databases, HTTP calls to a model server, the Claude SDK, the clock, signals, logging and settings all live here. Each adapter implements a port from the application layer.

## Why this repository uses it

Keeping every contact with the outside in one layer makes it easy to swap (recorded answers instead of a live model) and to test (a fake HTTP transport instead of a network).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/infrastructure/recording.py` | 79 non-blank lines |
| `src/scheduling_agent/infrastructure/resilient.py` | 48 non-blank lines |
| `src/scheduling_agent/infrastructure/retry.py` | 33 non-blank lines |
| `src/scheduling_agent/infrastructure/scripted_policy.py` | 200 non-blank lines |
| `src/scheduling_agent/infrastructure/settings.py` | 57 non-blank lines |
| `src/scheduling_agent/infrastructure/shutdown.py` | 20 non-blank lines |
| `src/scheduling_agent/infrastructure/sqlite.py` | 30 non-blank lines |
| `src/scheduling_agent/infrastructure/state_codec.py` | 80 non-blank lines |
| `src/scheduling_agent/infrastructure/wiring.py` | 69 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/scheduling_agent/infrastructure/recording.py`

In its own words: "Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures."

79 non-blank lines; it defines `RecordingStore`, `RecordedChatModel`, `RecordingChatModel`.

`src/scheduling_agent/infrastructure/recording.py`, lines 1 to 13:

```python
"""Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

A recording is a JSON Lines file. Each line holds the request fingerprint, the call's tag, a note about what
produced it and the response. Fixtures hold synthetic data only (no credentials, no personal data).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `Any` from the standard library module `typing`.

`src/scheduling_agent/infrastructure/recording.py`, lines 15 to 27:

```python
from scheduling_agent.application.ports import ChatModel
from scheduling_agent.domain.errors import RecordingMissing
from scheduling_agent.domain.llm import ChatRequest, ChatResponse


class RecordingStore:
    """An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
```

- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `scheduling_agent.application.ports`.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `scheduling_agent.domain.llm`.
- Defines the class `RecordingStore`. The author's own description: "An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.Lock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.Lock` makes a lock.
- Declares `self._entries` as a dictionary from text to a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `files`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `.exists(...)` asks whether the path exists.

`src/scheduling_agent/infrastructure/recording.py`, lines 28 to 41:

```python
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._entries[entry["key"]] = entry
        self._append_to = path / "recorded.jsonl" if path.is_dir() else path

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: str) -> ChatResponse | None:
        with self._lock:
            entry = self._entries.get(key)
```

- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- A `with` block: it sets up `file.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `file`.
- Loop: the indented lines below run once for each item of `handle`; `line` names the current item.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
- Stores the value named `entry` under the name `self._entries[entry['key']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `self._append_to` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `/` is divide.
- Defines the method `__len__`. It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `get`. It returns the project type `ChatResponse`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._entries.get` under the name `entry`.
  - `get` on the stored object `self._entries`: it reads a dictionary entry, giving a default when the key is missing.

`src/scheduling_agent/infrastructure/recording.py`, lines 42 to 55:

```python
        return ChatResponse.from_json(entry["response"]) if entry else None

    def put(self, key: str, tag: str, response: ChatResponse, recorded_with: Mapping[str, Any]) -> None:
        entry = {"key": key, "tag": tag, "recorded_with": dict(recorded_with), "response": response.to_json()}
        with self._lock:
            self._entries[key] = entry
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()


class RecordedChatModel:
    """Replays recorded responses. A request nobody recorded raises `RecordingMissing`."""
```

- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - The method `from_json` of `ChatResponse`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `put`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `tag` holds text.
    - `response` holds the project type `ChatResponse`.
    - `recorded_with` holds anything that behaves like a dictionary from text to any value.
- Stores a dictionary with 4 entries under the name `entry`.
  - `dict` makes a dictionary (a copy when given one).
  - The method `to_json` of `response`.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the value named `entry` under the name `self._entries[key]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `mkdir` on the stored object `self._append_to.parent`: it creates a folder with 2 argument(s); the result is not kept.
  - `mkdir` on the stored object `self._append_to.parent`: it creates a folder.
- A `with` block: it sets up `self._append_to.open('a', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._append_to`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.
- Defines the class `RecordedChatModel`. The author's own description: "Replays recorded responses. A request nobody recorded raises `RecordingMissing`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/recording.py`, lines 57 to 69:

```python
    def __init__(self, store: RecordingStore) -> None:
        self._store = store

    @property
    def name(self) -> str:
        return "recorded"

    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        response = self._store.get(request.fingerprint())
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `RecordingStore`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `recorded` to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._store.get` under the name `response`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).

`src/scheduling_agent/infrastructure/recording.py`, lines 70 to 83:

```python
        if response is None:
            raise RecordingMissing(
                f"no recording for request tag={request.tag!r} fingerprint={request.fingerprint()[:12]}; "
                "run `make record` against a live model to refresh the fixtures"
            )
        return response


class RecordingChatModel:
    """Wraps a live model and writes each answer into a recording. A request already recorded is replayed."""

    def __init__(self, inner: ChatModel, store: RecordingStore, note: Mapping[str, Any]) -> None:
        self._inner = inner
        self._store = store
```

- Decision: the indented lines below run only when `response is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `RecordingMissing`. Execution jumps out to the nearest matching `except`.
  - `RecordingMissing` from the project's `scheduling_agent.domain.errors` (The recorded adapter has no response for this request. Re-record with `make record`.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Ends the function and gives back the value named `response` to the caller.
- Defines the class `RecordingChatModel`. The author's own description: "Wraps a live model and writes each answer into a recording. A request already recorded is replayed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `store` holds the project type `RecordingStore`.
    - `note` holds anything that behaves like a dictionary from text to any value.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/recording.py`, lines 84 to 97:

```python
        self._note = dict(note)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        key = request.fingerprint()
        cached = self._store.get(key)
        if cached is not None:
```

- Stores the result of calling `dict` under the name `self._note` (as an attribute of this object, so other methods can use it).
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `request.fingerprint` under the name `key`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Stores the result of calling `self._store.get` under the name `cached`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `cached is not None` is true.
  - `is not` means not the same object.

`src/scheduling_agent/infrastructure/recording.py`, lines 98 to 101:

```python
            return cached
        response = self._inner.complete(request)
        self._store.put(key, request.tag, response, {**self._note, "model": response.model})
        return response
```

- Ends the function and gives back the value named `cached` to the caller.
- Stores the result of calling `self._inner.complete` under the name `response`.
  - The method `complete` of `self._inner`.
- Calls `put` on the stored object `self._store`: it sends an HTTP PUT request with 4 argument(s); the result is not kept.
  - `put` on the stored object `self._store`: it sends an HTTP PUT request.
- Ends the function and gives back the value named `response` to the caller.

### `src/scheduling_agent/infrastructure/resilient.py`

In its own words: "A decorator that retries transient model failures with backoff and jitter."

48 non-blank lines; it defines `RetryingChatModel`.

`src/scheduling_agent/infrastructure/resilient.py`, lines 1 to 14:

```python
"""A decorator that retries transient model failures with backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from scheduling_agent.application.ports import ChatModel
from scheduling_agent.domain.errors import TransientModelError
from scheduling_agent.domain.llm import ChatRequest, ChatResponse
from scheduling_agent.infrastructure.logging import fields
from scheduling_agent.infrastructure.retry import retry
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `scheduling_agent.application.ports`.
- Brings in `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `scheduling_agent.domain.llm`.
- Brings in `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `scheduling_agent.infrastructure.logging`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `scheduling_agent.infrastructure.retry`.

`src/scheduling_agent/infrastructure/resilient.py`, lines 16 to 20:

```python
_log = logging.getLogger(__name__)


class RetryingChatModel:
    """Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."""
```

- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `RetryingChatModel`. The author's own description: "Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/resilient.py`, lines 22 to 34:

```python
    def __init__(
        self,
        inner: ChatModel,
        *,
        attempts: int = 3,
        base_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._base_delay = base_delay_seconds
        self._sleep = sleep
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `attempts` holds a whole number; if the caller leaves it out it is the number `3`; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `0.5`; it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `attempts` under the name `self._attempts` (as an attribute of this object, so other methods can use it).
- Stores the value named `base_delay_seconds` under the name `self._base_delay` (as an attribute of this object, so other methods can use it).
- Stores the value named `sleep` under the name `self._sleep` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/resilient.py`, lines 35 to 46:

```python
        self._rng = rng

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        def log_retry(attempt: int, error: BaseException) -> None:
```

- Stores the value named `rng` under the name `self._rng` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Defines the function `log_retry`. It returns nothing (None).
- Its parameters:
    - `attempt` holds a whole number.
    - `error` holds `BaseException`.

`src/scheduling_agent/infrastructure/resilient.py`, lines 47 to 59:

```python
            _log.warning(
                "model call failed, retrying", extra=fields(tag=request.tag, attempt=attempt, error=str(error))
            )

        return retry(
            lambda: self._inner.complete(request),
            attempts=self._attempts,
            base_delay_seconds=self._base_delay,
            retry_on=(TransientModelError,),
            sleep=self._sleep,
            rng=self._rng,
            on_retry=log_retry,
        )
```

- Calls the method `warning` of `_log` with 2 argument(s); the result is not kept.
  - The method `warning` of `_log`.
  - `fields` from the project's `scheduling_agent.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
  - `str` turns a value into text.
- Ends the function and gives back the result of calling `retry` to the caller.
  - `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `complete` of `self._inner`.

### `src/scheduling_agent/infrastructure/retry.py`

In its own words: "Retry with exponential backoff and jitter for calls that cross the network."

33 non-blank lines; it defines `retry`.

`src/scheduling_agent/infrastructure/retry.py`, lines 1 to 7:

```python
"""Retry with exponential backoff and jitter for calls that cross the network."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.

`src/scheduling_agent/infrastructure/retry.py`, lines 10 to 20:

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
```

- Defines the function `retry`. It returns `T`. The author's own description: "Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`."
- Its parameters:
    - `operation` holds a function.
    - `attempts` holds a whole number; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; it must be passed by name.
    - `retry_on` holds a fixed list of type of `BaseException` (any length); it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
    - `max_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `10.0`; it must be passed by name.
    - `on_retry` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.

`src/scheduling_agent/infrastructure/retry.py`, lines 21 to 34:

```python
    """Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.

    The pause is `base * 2**(attempt - 1)` capped at `max_delay_seconds`, then scaled by a random
    factor in [0.5, 1.0] so many clients do not retry in step. The last failure is raised.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    jitter = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on as error:
            if attempt == attempts:
                raise
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `attempts < 1` is true.
  - `<` means less than.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Stores the result of combining conditions: `rng or random.Random()` under the name `jitter`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Loop: the indented lines below run once for each item of `range(1, attempts + 1)`; `attempt` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `+` is add.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `operation` to the caller.
  - `operation`, a function defined in this file or passed in.
- `except` handler: it runs when the `try` block raised `retry_on`; `error` names the error object.
- Decision: the indented lines below run only when `attempt == attempts` is true.
  - `==` means equal.
- Raises an error again (the one being handled). Execution jumps out to the nearest matching `except`.

`src/scheduling_agent/infrastructure/retry.py`, lines 35 to 38:

```python
            if on_retry:
                on_retry(attempt, error)
            sleep(min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1)) * jitter.uniform(0.5, 1.0))
    raise AssertionError("unreachable")  # pragma: no cover
```

- Decision: the indented lines below run only when `on_retry` is true.
- Calls `on_retry`, a function defined in this file or passed in with 2 argument(s); the result is not kept.
  - `on_retry`, a function defined in this file or passed in.
- Calls `sleep`, a function defined in this file or passed in with 1 argument(s); the result is not kept.
  - `sleep`, a function defined in this file or passed in.
  - `*` is multiply.
  - `min` picks the smallest value.
  - The method `uniform` of `jitter`.
  - `**` is power.
  - `-` is subtract.
- Raises an error: the result of calling `AssertionError`. Execution jumps out to the nearest matching `except`.
  - `AssertionError` the error an `assert` raises.

### `src/scheduling_agent/infrastructure/scripted_policy.py`

In its own words: "A deterministic stand-in for the model: a rule-based planner that speaks the same tool-calling protocol."

200 non-blank lines; it defines `_names`, `_constraints`, `ScriptedPolicyModel`.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 1 to 13:

```python
"""A deterministic stand-in for the model: a rule-based planner that speaks the same tool-calling protocol.

It is not a language model. It exists so the whole agent (loop, approvals, budgets, checkpoints, crash recovery,
memory) can be run and tested offline with exact, repeatable behavior, and so the 30 tasks can be judged by calendar
end state without a model key. A real model replaces it by changing `MODEL_PROVIDER`.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta
from typing import Any
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `date`, `datetime`, `time`, `timedelta` from the standard library module `datetime`.
- Brings in `Any` from the standard library module `typing`.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 15 to 25:

```python
from scheduling_agent.domain.llm import ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage
from scheduling_agent.domain.memory import Constraints, parse_statement

_DAY = r"(\d{4}-\d{2}-\d{2})"
_BOOK = re.compile(
    rf"book an? (\d+)-minute meeting with (.+?) on {_DAY}(?: after (\d{{2}}:\d{{2}}))?(?: before (\d{{2}}:\d{{2}}))?",
    re.I,
)
_FIND = re.compile(
    rf"find the earliest (\d+)-minute slot for (.+?) between {_DAY} and {_DAY}(?: after (\d{{2}}:\d{{2}}))?", re.I
)
```

- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Constraints` (What recalled facts mean for a search: earliest start, latest end and weekdays to avoid.), `parse_statement` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.) from the project module `scheduling_agent.domain.memory`.
- Stores the text `(\d{4}-\d{2}-\d{2})` under the name `_DAY`.
- Stores the result of calling `re.compile` under the name `_BOOK`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `re.compile` under the name `_FIND`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 26 to 39:

```python
_MOVE = re.compile(
    rf"move event (ev-\d+) to the earliest free slot between {_DAY} and {_DAY}(?: after (\d{{2}}:\d{{2}}))?", re.I
)
_CANCEL = re.compile(r"cancel event (ev-\d+)", re.I)
Decision = tuple[tuple[str, dict[str, Any]] | None, str]
_MEMORY_LINE = re.compile(r"^- (\w+): (.+?) \(said (\d{4}-\d{2}-\d{2}), session (\S+)\)$", re.M)


def _names(text: str) -> list[str]:
    return [n.lower() for n in re.split(r",\s*|\s+and\s+", text.strip()) if n.strip()]


def _constraints(first_message: str, people: list[str]) -> Constraints:
    facts = []
```

- Stores the result of calling `re.compile` under the name `_MOVE`.
  - `re.compile` prepares a regular expression.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `re.compile` under the name `_CANCEL`.
  - `re.compile` prepares a regular expression.
- Stores the part of `tuple` picked by `(tuple[str, dict[str, Any]]...` under the name `Decision`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `|` is or; in a type, "either".
- Stores the result of calling `re.compile` under the name `_MEMORY_LINE`.
  - `re.compile` prepares a regular expression.
- Defines the function `_names`. It returns a list of text.
- Its parameters:
    - `text` holds text.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.lower(...)` turns text into lower case.
  - `re.split` cuts text at matches.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Defines the function `_constraints`. It returns the project type `Constraints`.
- Its parameters:
    - `first_message` holds text.
    - `people` holds a list of text.
- Stores an empty list under the name `facts`.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 40 to 53:

```python
    for match in _MEMORY_LINE.finditer(first_message):
        person, said, stated, session = match.groups()
        fact = parse_statement(person, said, session, date.fromisoformat(stated))
        if fact:
            facts.append(fact)
    return Constraints.from_facts(facts, people)


class ScriptedPolicyModel:
    """Reads the task and the tool results in the conversation and decides the next tool call or the final answer."""

    @property
    def name(self) -> str:
        return "scripted-policy"
```

- Loop: the indented lines below run once for each item of `_MEMORY_LINE.finditer(first_message)`; `match` names the current item.
  - `.finditer(...)` yields every match of a regular expression.
- Stores the result of calling `match.groups` under the name `(person, said, stated, session)`.
  - The method `groups` of `match`.
- Stores the result of calling `parse_statement` under the name `fact`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
  - `date.fromisoformat` reads a date from ISO text.
- Decision: the indented lines below run only when `fact` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the result of calling `Constraints.from_facts` to the caller.
  - The method `from_facts` of the project's `Constraints` (The strictest constraint of each kind among the facts of the people in the meeting.).
- Defines the class `ScriptedPolicyModel`. The author's own description: "Reads the task and the tool results in the conversation and decides the next tool call or the final answer."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `scripted-policy` to the caller.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 55 to 67:

```python
    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        messages = request.messages
        first = messages[0].content
        task = first.split("\n\nWhat people told you earlier")[0].strip()
        turns = sum(1 for m in messages if m.role is Role.ASSISTANT)
        results = [json.loads(m.content) for m in messages if m.role is Role.TOOL]
        call, text = self._decide(task, first, turns, results)
        calls = (ToolCall(f"call_{turns + 1}", call[0], call[1]),) if call else ()
        tokens_in = 30 + sum(len(m.content) for m in messages) // 4
```

- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the `messages` of `request` under the name `messages`.
- Stores the `content` of `messages[0]` under the name `first`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `first.split('\n\nWhat people told you earlier')...` under the name `task`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Stores the result of calling `sum` under the name `turns`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.
- Stores a list built by looping under the name `results`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `json.loads` turns JSON text into Python data.
  - `is` means the very same object.
- Stores the result of calling `self._decide` under the name `(call, text)`.
  - The method `_decide` of this object.
- Stores one of two values, chosen by a condition under the name `calls`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `+` is add.
- Stores the result of `30 + sum((len(m.content) for m in messages)) // 4` under the name `tokens_in`.
  - `+` is add.
  - `//` is divide and drop the fraction.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `len` counts the items in a collection (or the characters in text).

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 68 to 81:

```python
        tokens_out = 25 if calls else max(8, len(text) // 4)
        return ChatResponse(
            text,
            StopReason.TOOL_CALLS if calls else StopReason.END,
            Usage(tokens_in, tokens_out),
            0.001,
            self.name,
            calls,
        )

    def _decide(
        self, task: str, first: str, turns: int, results: list[dict[str, Any]]
    ) -> tuple[tuple[str, dict[str, Any]] | None, str]:
        if match := _BOOK.search(task):
```

- Stores one of two values, chosen by a condition under the name `tokens_out`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `max` picks the largest value.
  - `//` is divide and drop the fraction.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the method `_decide`. It returns a fixed list of a fixed list of text, a dictionary from text to any value, or nothing (None), text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds text.
    - `first` holds text.
    - `turns` holds a whole number.
    - `results` holds a list of a dictionary from text to any value.
- Decision: the indented lines below run only when `(match := _BOOK.search(task))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 82 to 95:

```python
            minutes, people_text, day, after, before = match.groups()
            return self._book(
                first,
                _names(people_text),
                int(minutes),
                day,
                day,
                after,
                before,
                turns,
                results,
                persistent="do not give up" in task.lower(),
            )
        if match := _FIND.search(task):
```

- Stores the result of calling `match.groups` under the name `(minutes, people_text, day, after, be...`.
  - The method `groups` of `match`.
- Ends the function and gives back the result of calling `self._book` to the caller.
  - The method `_book` of this object.
  - `_names`, a function defined in this file or passed in.
  - `int` turns a value into a whole number.
  - `in` means is contained in.
  - `.lower(...)` turns text into lower case.
- Decision: the indented lines below run only when `(match := _FIND.search(task))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 96 to 109:

```python
            minutes, people_text, first_day, last_day, after = match.groups()
            return self._book(
                first,
                _names(people_text),
                int(minutes),
                first_day,
                last_day,
                after,
                None,
                turns,
                results,
                persistent=False,
            )
        if match := _MOVE.search(task):
```

- Stores the result of calling `match.groups` under the name `(minutes, people_text, first_day, las...`.
  - The method `groups` of `match`.
- Ends the function and gives back the result of calling `self._book` to the caller.
  - The method `_book` of this object.
  - `_names`, a function defined in this file or passed in.
  - `int` turns a value into a whole number.
- Decision: the indented lines below run only when `(match := _MOVE.search(task))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 110 to 113:

```python
            return self._move(first, match.group(1), match.group(2), match.group(3), match.group(4), turns, results)
        if match := _CANCEL.search(task):
            return self._cancel(match.group(1), turns, results)
        return None, "I did not understand the task, so I changed nothing."
```

- Ends the function and gives back the result of calling `self._move` to the caller.
  - The method `_move` of this object.
  - `.group(...)` reads a captured part of a regular-expression match.
- Decision: the indented lines below run only when `(match := _CANCEL.search(task))` is true.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `.search(...)` looks for a regular expression anywhere in text.
- Ends the function and gives back the result of calling `self._cancel` to the caller.
  - The method `_cancel` of this object.
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back a tuple of 2 item(s) to the caller.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 115 to 127:

```python
    def _book(
        self,
        first: str,
        people: list[str],
        minutes: int,
        first_day: str,
        last_day: str,
        after: str | None,
        before: str | None,
        turns: int,
        results: list[dict[str, Any]],
        persistent: bool,
    ) -> Decision:
```

- Defines the method `_book`. It returns `Decision`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `first` holds text.
    - `people` holds a list of text.
    - `minutes` holds a whole number.
    - `first_day` holds text.
    - `last_day` holds text.
    - `after` holds text, or nothing (None).
    - `before` holds text, or nothing (None).
    - `turns` holds a whole number.
    - `results` holds a list of a dictionary from text to any value.
    - `persistent` holds true or false.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 128 to 138:

```python
        constraints = _constraints(first, people)
        floors = [t for t in (time.fromisoformat(after) if after else None, constraints.not_before) if t]
        ceilings = [t for t in (time.fromisoformat(before) if before else None, constraints.not_after) if t]
        start_day = date.fromisoformat(first_day)
        end_day = date.fromisoformat(last_day)
        while start_day <= end_day and start_day.weekday() in constraints.avoid_weekdays:
            start_day += timedelta(days=1)
        last = results[-1] if results else None
        searching = last is None or (persistent and ("error" in last or ("slots" in last and not last["slots"])))
        if searching:
            shift = timedelta(days=7 * turns) if persistent else timedelta(0)
```

- Stores the result of calling `_constraints` under the name `constraints`.
  - `_constraints`, a function defined in this file or passed in.
- Stores a list built by looping under the name `floors`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Stores a list built by looping under the name `ceilings`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Stores the result of calling `date.fromisoformat` under the name `start_day`.
  - `date.fromisoformat` reads a date from ISO text.
- Stores the result of calling `date.fromisoformat` under the name `end_day`.
  - `date.fromisoformat` reads a date from ISO text.
- Loop: the indented lines below repeat as long as `start_day <= end_day and start_day.weekday() in constrain...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<=` means less than or equal.
  - `in` means is contained in.
  - The method `weekday` of `start_day`.
- Updates `start_day` in place: `+=` applies `+` with the result of calling `timedelta` and stores the result back.
  - `timedelta` from the standard library module `datetime`.
- Stores one of two values, chosen by a condition under the name `last`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of combining conditions: `last is None or (persistent and ('error' in last or ('slo...` under the name `searching`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `in` means is contained in.
  - `not` flips true and false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `searching` is true.
- Stores one of two values, chosen by a condition under the name `shift`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `timedelta` from the standard library module `datetime`.
  - `*` is multiply.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 139 to 152:

```python
            args: dict[str, Any] = {
                "people": people,
                "first_day": (start_day + shift).isoformat(),
                "last_day": (max(start_day, end_day) + shift).isoformat(),
                "minutes": minutes,
            }
            if floors:
                args["not_before"] = f"{max(floors):%H:%M}"
            if ceilings:
                args["not_after"] = f"{min(ceilings):%H:%M}"
            return ("find_free_slots", args), ""
        assert last is not None
        if "error" in last:
            return None, f"I could not book it and changed nothing: {last['error']}"
```

- Declares `args` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `+` is add.
  - `max` picks the largest value.
- Decision: the indented lines below run only when `floors` is true.
- Stores a text built from pieces (an f-string) under the name `args['not_before']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `max` picks the largest value.
- Decision: the indented lines below run only when `ceilings` is true.
- Stores a text built from pieces (an f-string) under the name `args['not_after']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `min` picks the smallest value.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Checks that `last is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Decision: the indented lines below run only when `'error' in last` is true.
  - `in` means is contained in.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 153 to 162:

```python
        if "slots" in last:
            fitting = [
                x for x in last["slots"] if datetime.fromisoformat(x).weekday() not in constraints.avoid_weekdays
            ]
            if not fitting:
                return None, "There is no free slot that fits, so I changed nothing."
            return ("book_meeting", {"people": people, "start": fitting[0], "minutes": minutes}), ""
        if last.get("status") == "booked":
            return None, f"Booked event {last['event_id']}."
        return None, f"The booking did not happen ({last.get('status') or last.get('error')}), so nothing changed."
```

- Decision: the indented lines below run only when `'slots' in last` is true.
  - `in` means is contained in.
- Stores a list built by looping under the name `fitting`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `not in` means is not contained in.
  - The method `weekday` of `datetime.fromisoformat(x)`.
  - `datetime.fromisoformat` reads a date and time from ISO text.
- Decision: the indented lines below run only when `not fitting` is true.
  - `not` flips true and false.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `last.get('status') == 'booked'` is true.
  - `==` means equal.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 164 to 176:

```python
    def _move(
        self,
        first: str,
        event_id: str,
        first_day: str,
        last_day: str,
        after: str | None,
        turns: int,
        results: list[dict[str, Any]],
    ) -> Decision:
        if turns == 0:
            return ("get_event", {"event_id": event_id}), ""
        if "error" in results[0]:
```

- Defines the method `_move`. It returns `Decision`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `first` holds text.
    - `event_id` holds text.
    - `first_day` holds text.
    - `last_day` holds text.
    - `after` holds text, or nothing (None).
    - `turns` holds a whole number.
    - `results` holds a list of a dictionary from text to any value.
- Decision: the indented lines below run only when `turns == 0` is true.
  - `==` means equal.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Decision: the indented lines below run only when `'error' in results[0]` is true.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 177 to 190:

```python
            return None, f"I could not find that event and changed nothing: {results[0]['error']}"
        event = results[0]
        if turns == 1:
            constraints = _constraints(first, event["people"])
            floor = time.fromisoformat(after) if after else None
            if constraints.not_before and (floor is None or constraints.not_before > floor):
                floor = constraints.not_before
            args: dict[str, Any] = {
                "people": event["people"],
                "first_day": first_day,
                "last_day": last_day,
                "minutes": event["minutes"],
            }
            if floor:
```

- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `results` picked by `0` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `turns == 1` is true.
  - `==` means equal.
- Stores the result of calling `_constraints` under the name `constraints`.
  - `_constraints`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `floor`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Decision: the indented lines below run only when `constraints.not_before and (floor is None or constraints.not_before...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `>` means greater than.
- Stores the `not_before` of `constraints` under the name `floor`.
- Declares `args` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `floor` is true.

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 191 to 204:

```python
                args["not_before"] = f"{floor:%H:%M}"
            return ("find_free_slots", args), ""
        if turns == 2:
            avoid = _constraints(first, event["people"]).avoid_weekdays
            fitting = [x for x in results[1].get("slots", []) if datetime.fromisoformat(x).weekday() not in avoid]
            if not fitting:
                return None, "There is no free slot that fits, so I changed nothing."
            return ("move_meeting", {"event_id": event_id, "new_start": fitting[0]}), ""
        last = results[-1]
        return None, (
            f"Moved {event_id}; the new event is {last['event_id']}."
            if last.get("status") == "moved"
            else f"The move did not happen ({last.get('status') or last.get('error')})."
        )
```

- Stores a text built from pieces (an f-string) under the name `args['not_before']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Decision: the indented lines below run only when `turns == 2` is true.
  - `==` means equal.
- Stores the `avoid_weekdays` of `_constraints(first, event['people'])` under the name `avoid`.
  - `_constraints`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a list built by looping under the name `fitting`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `not in` means is not contained in.
  - The method `weekday` of `datetime.fromisoformat(x)`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `datetime.fromisoformat` reads a date and time from ISO text.
- Decision: the indented lines below run only when `not fitting` is true.
  - `not` flips true and false.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `results` picked by `-1` under the name `last`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/scheduling_agent/infrastructure/scripted_policy.py`, lines 206 to 218:

```python
    def _cancel(self, event_id: str, turns: int, results: list[dict[str, Any]]) -> Decision:
        if turns == 0:
            return ("get_event", {"event_id": event_id}), ""
        if "error" in results[0]:
            return None, f"I could not find that event and changed nothing: {results[0]['error']}"
        if turns == 1:
            return ("cancel_meeting", {"event_id": event_id}), ""
        last = results[-1]
        return None, (
            f"Cancelled {event_id}."
            if last.get("status") == "cancelled"
            else f"The cancellation did not happen ({last.get('status') or last.get('error')})."
        )
```

- Defines the method `_cancel`. It returns `Decision`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
    - `turns` holds a whole number.
    - `results` holds a list of a dictionary from text to any value.
- Decision: the indented lines below run only when `turns == 0` is true.
  - `==` means equal.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Decision: the indented lines below run only when `'error' in results[0]` is true.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `turns == 1` is true.
  - `==` means equal.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
- Stores the part of `results` picked by `-1` under the name `last`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

### `src/scheduling_agent/infrastructure/settings.py`

In its own words: "Configuration from the environment, validated once at startup (twelve-factor)."

57 non-blank lines; it defines `AgentSettings`.

`src/scheduling_agent/infrastructure/settings.py`, lines 1 to 12:

```python
"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scheduling_agent.infrastructure.env import ConfigurationError, choice, positive_float, positive_int, text

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `positive_float` (A number greater than zero.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `scheduling_agent.infrastructure.env`.
- Stores a tuple of 4 item(s) under the name `_LEVELS`.

`src/scheduling_agent/infrastructure/settings.py`, lines 15 to 26:

```python
@dataclass(frozen=True, slots=True)
class AgentSettings:
    """Where things live and how a run is capped. See env.example for each variable."""

    calendar_url: str
    calendar_db: Path
    agent_db: Path
    sql_dir: Path
    prompts_dir: Path
    prompt_version: str
    tasks_path: Path
    embeddings_path: Path
```

- Defines the class `AgentSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Where things live and how a run is capped. See env.example for each variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `calendar_url` as text; it has no default, so a value must be given when the object is made.
- Declares `calendar_db` as a file path; it has no default, so a value must be given when the object is made.
- Declares `agent_db` as a file path; it has no default, so a value must be given when the object is made.
- Declares `sql_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `prompts_dir` as a file path; it has no default, so a value must be given when the object is made.
- Declares `prompt_version` as text; it has no default, so a value must be given when the object is made.
- Declares `tasks_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `embeddings_path` as a file path; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/infrastructure/settings.py`, lines 27 to 40:

```python
    embedder_provider: str
    embed_model: str
    people: tuple[str, ...]
    max_steps: int
    max_tokens: int
    max_seconds: float
    host: str
    port: int
    allow_reset: bool
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AgentSettings:
        env = os.environ if environ is None else environ
```

- Declares `embedder_provider` as text; it has no default, so a value must be given when the object is made.
- Declares `embed_model` as text; it has no default, so a value must be given when the object is made.
- Declares `people` as a fixed list of text (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `max_steps` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `max_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `max_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `host` as text; it has no default, so a value must be given when the object is made.
- Declares `port` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `allow_reset` as true or false; it has no default, so a value must be given when the object is made.
- Declares `log_level` as text; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `AgentSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.

`src/scheduling_agent/infrastructure/settings.py`, lines 41 to 45:

```python
        people = tuple(
            p.strip().lower() for p in text(env, "PEOPLE", "alice,bob,carol,dave,erin").split(",") if p.strip()
        )
        if not people:
            raise ConfigurationError("PEOPLE must list at least one name")
```

- Stores the result of calling `tuple` under the name `people`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.lower(...)` turns text into lower case.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `text` from the project's `scheduling_agent.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
- Decision: the indented lines below run only when `not people` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `scheduling_agent.infrastructure.env` (An environment variable is missing or has an unusable value.).

`src/scheduling_agent/infrastructure/settings.py`, lines 46 to 65:

```python
        return cls(
            calendar_url=text(env, "CALENDAR_URL", "http://127.0.0.1:8090"),
            calendar_db=Path(text(env, "CALENDAR_DB", "out/calendar.db")),
            agent_db=Path(text(env, "AGENT_DB", "out/agent.db")),
            sql_dir=Path(text(env, "SQL_DIR", "sql")),
            prompts_dir=Path(text(env, "PROMPTS_DIR", "prompts")),
            prompt_version=text(env, "AGENT_PROMPT_VERSION", "v1"),
            tasks_path=Path(text(env, "TASKS_PATH", "data/tasks.jsonl")),
            embeddings_path=Path(text(env, "EMBEDDINGS_PATH", "tests/fixtures/embeddings")),
            embedder_provider=choice(env, "EMBEDDER_PROVIDER", "recorded", ("recorded", "openai-compatible")),
            embed_model=text(env, "EMBED_MODEL", "nomic-embed-text"),
            people=people,
            max_steps=positive_int(env, "MAX_STEPS", 12),
            max_tokens=positive_int(env, "MAX_TOKENS", 4000),
            max_seconds=positive_float(env, "MAX_SECONDS", 30.0),
            host=text(env, "HTTP_HOST", "127.0.0.1"),
            port=positive_int(env, "HTTP_PORT", 8090),
            allow_reset=choice(env, "CALENDAR_ALLOW_RESET", "off", ("on", "off")) == "on",
            log_level=choice({"LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `text` from the project's `scheduling_agent.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `choice` from the project's `scheduling_agent.infrastructure.env` (One of the `allowed` strings.).
  - `positive_int` from the project's `scheduling_agent.infrastructure.env` (An integer of 1 or more.).
  - `positive_float` from the project's `scheduling_agent.infrastructure.env` (A number greater than zero.).
  - `==` means equal.
  - `.upper(...)` turns text into upper case.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/scheduling_agent/infrastructure/shutdown.py`

In its own words: "Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."

20 non-blank lines; it defines `ShutdownSignal`.

`src/scheduling_agent/infrastructure/shutdown.py`, lines 1 to 14:

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `signal` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `FrameType` from the standard library module `types`.
- Defines the class `ShutdownSignal`. The author's own description: "A flag that SIGINT and SIGTERM set, which work loops check between units of work."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the result of calling `threading.Event` under the name `self._requested` (as an attribute of this object, so other methods can use it).
  - `threading.Event` makes a flag shared between threads.

`src/scheduling_agent/infrastructure/shutdown.py`, lines 16 to 28:

```python
    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        self._requested.set()

    @property
    def requested(self) -> bool:
```

- Defines the method `install`. It returns nothing (None). The author's own description: "Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `(signal.SIGINT, signal.SIGTERM)`; `number` names the current item.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Defines the method `_handle`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `_number` holds a whole number.
    - `_frame` holds a stack frame, or nothing (None).
- Calls the method `request` of this object; the result is not kept.
  - The method `request` of this object.
- Defines the method `request`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Calls `set` on the stored object `self._requested`: it raises a flag (an Event); the result is not kept.
  - `set` on the stored object `self._requested`: it raises a flag (an Event).
- Defines the method `requested`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/scheduling_agent/infrastructure/shutdown.py`, lines 29 to 29:

```python
        return self._requested.is_set()
```

- Ends the function and gives back the result of calling `self._requested.is_set` to the caller.
  - `is_set` on the stored object `self._requested`: it asks whether a flag is raised.

### `src/scheduling_agent/infrastructure/sqlite.py`

In its own words: "SQLite connections: autocommit off, foreign keys on, one writer at a time (`BEGIN IMMEDIATE`)."

30 non-blank lines; it defines `connect`, `transaction`, `apply_sql`.

`src/scheduling_agent/infrastructure/sqlite.py`, lines 1 to 14:

```python
"""SQLite connections: autocommit off, foreign keys on, one writer at a time (`BEGIN IMMEDIATE`)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a database with the settings every store here relies on."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `sqlite3` (standard library) available.
- Brings in `Iterator` from the standard library module `collections.abc`.
- Brings in `contextmanager` from the standard library module `contextlib`.
- Brings in `Path` from the standard library module `pathlib`.
- Defines the function `connect`. It returns `sqlite3.Connection`. The author's own description: "Open a database with the settings every store here relies on."
- Its parameters:
    - `path` holds text, or a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `str(path) != ':memory:'` is true.
  - `!=` means not equal.
  - `str` turns a value into text.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
  - `Path` from the standard library module `pathlib`, which a file or folder location.

`src/scheduling_agent/infrastructure/sqlite.py`, lines 15 to 28:

```python
    connection = sqlite3.connect(str(path), timeout=10, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if str(path) != ":memory:":
        connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block as one write transaction: commit on success, roll back on any error."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
```

- Stores the result of calling `sqlite3.connect` under the name `connection`.
  - `sqlite3.connect` opens a SQLite database file.
  - `str` turns a value into text.
- Stores the `Row` of `sqlite3` under the name `connection.row_factory`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Decision: the indented lines below run only when `str(path) != ':memory:'` is true.
  - `!=` means not equal.
  - `str` turns a value into text.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Ends the function and gives back the value named `connection` to the caller.
- Defines the function `transaction`. `@contextmanager` turns the function into something usable after `with`: the code before the `yield` is setup, the code after it is cleanup. It returns something that gives items one at a time of `sqlite3.Connection`. The author's own description: "Run a block as one write transaction: commit on success, roll back on any error."
- Its parameters:
    - `connection` holds `sqlite3.Connection`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Hands a value to the caller and pauses until the next one is asked for.
  - `yield` hands a value to the caller and pauses the function until the next value is asked for.

`src/scheduling_agent/infrastructure/sqlite.py`, lines 29 to 38:

```python
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def apply_sql(connection: sqlite3.Connection, *files: Path) -> None:
    """Run SQL script files in the order given (the numbered files under sql/)."""
    for file in files:
        connection.executescript(file.read_text(encoding="utf-8"))
```

- `except` handler: it runs when the `try` block raised `BaseException`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Raises an error again (the one being handled). Execution jumps out to the nearest matching `except`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Defines the function `apply_sql`. It returns nothing (None). The author's own description: "Run SQL script files in the order given (the numbered files under sql/)."
- Its parameters:
    - `connection` holds `sqlite3.Connection`.
    - `*files` collects any extra positional arguments into a tuple.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- Calls `.executescript(...)` runs a whole SQL script with 1 argument(s); the result is not kept.
  - `.executescript(...)` runs a whole SQL script.
  - `.read_text(...)` reads a whole file as text.

### `src/scheduling_agent/infrastructure/state_codec.py`

In its own words: "Run state to JSON and back, for the checkpoint table."

80 non-blank lines; it defines `encode`, `decode`.

`src/scheduling_agent/infrastructure/state_codec.py`, lines 1 to 14:

```python
"""Run state to JSON and back, for the checkpoint table."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from scheduling_agent.domain.llm import ChatMessage, Role, ToolCall
from scheduling_agent.domain.proposals import Action, Proposal
from scheduling_agent.domain.run import PendingWrite, RunState, RunStatus


def encode(state: RunState) -> str:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `datetime` from the standard library module `datetime`.
- Brings in `Any` from the standard library module `typing`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `Role` (Who wrote a message.), `ToolCall` (A tool call the model asked for.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Action` (The three writes.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `PendingWrite` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.), `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.), `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Defines the function `encode`. It returns text. The author's own description: "The whole run state as one JSON document."
- Its parameters:
    - `state` holds the project type `RunState`.

`src/scheduling_agent/infrastructure/state_codec.py`, lines 15 to 16:

```python
    """The whole run state as one JSON document."""
    pending = state.pending
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the `pending` of `state` under the name `pending`.

`src/scheduling_agent/infrastructure/state_codec.py`, lines 17 to 50:

```python
    return json.dumps(
        {
            "run_id": state.run_id,
            "task": state.task,
            "session": state.session,
            "status": state.status.value,
            "steps": state.steps,
            "tokens": state.tokens,
            "final_text": state.final_text,
            "stop_reason": state.stop_reason,
            "writes_done": list(state.writes_done),
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_call_id": m.tool_call_id,
                    "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in m.tool_calls],
                }
                for m in state.messages
            ],
            "pending": None
            if pending is None
            else {
                "step": pending.step,
                "tool_call_id": pending.tool_call_id,
                "tool_name": pending.tool_name,
                "proposal": {"action": pending.proposal.action.value, "args": dict(pending.proposal.args)},
                "approval_id": pending.approval_id,
                "skipped_ids": list(pending.skipped_ids),
            },
        },
        sort_keys=True,
    )
```

- Ends the function and gives back the result of calling `json.dumps` to the caller.
  - `json.dumps` turns Python data into JSON text.
  - `list` makes a list (a copy when given a collection).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `is` means the very same object.
  - `dict` makes a dictionary (a copy when given one).

`src/scheduling_agent/infrastructure/state_codec.py`, lines 53 to 56:

```python
def decode(text: str) -> RunState:
    """The inverse of `encode`."""
    data: dict[str, Any] = json.loads(text)
    pending = data["pending"]
```

- Defines the function `decode`. It returns the project type `RunState`. The author's own description: "The inverse of `encode`."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `data` as a dictionary from text to any value and sets it to the result of calling `json.loads`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Stores the part of `data` picked by `'pending'` under the name `pending`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/state_codec.py`, lines 57 to 87:

```python
    return RunState(
        run_id=data["run_id"],
        task=data["task"],
        session=data["session"],
        status=RunStatus(data["status"]),
        steps=data["steps"],
        tokens=data["tokens"],
        messages=tuple(
            ChatMessage(
                Role(m["role"]),
                m["content"],
                tuple(ToolCall(c["id"], c["name"], c["arguments"]) for c in m["tool_calls"]),
                m["tool_call_id"],
            )
            for m in data["messages"]
        ),
        pending=None
        if pending is None
        else PendingWrite(
            pending["step"],
            pending["tool_call_id"],
            pending["tool_name"],
            Proposal(Action(pending["proposal"]["action"]), pending["proposal"]["args"]),
            pending["approval_id"],
            tuple(pending["skipped_ids"]),
        ),
        final_text=data["final_text"],
        stop_reason=data["stop_reason"],
        writes_done=tuple(data["writes_done"]),
        created_at=datetime.fromisoformat(data["created_at"]) if data["created_at"] else None,
    )
```

- Ends the function and gives back the result of calling `RunState` to the caller.
  - `RunState` from the project's `scheduling_agent.domain.run` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `RunStatus` from the project's `scheduling_agent.domain.run` (Where a run is.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.
  - `PendingWrite` from the project's `scheduling_agent.domain.run` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.).
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
  - `Role` from the project's `scheduling_agent.domain.llm` (Who wrote a message.).
  - `Action` from the project's `scheduling_agent.domain.proposals` (The three writes.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).

### `src/scheduling_agent/infrastructure/wiring.py`

In its own words: "Build the agent and everything it stands on from the settings."

69 non-blank lines; it defines `build_embedder`, `build_calendar`, `build_kit`.

`src/scheduling_agent/infrastructure/wiring.py`, lines 1 to 14:

```python
"""Build the agent and everything it stands on from the settings."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Callable, Mapping

import httpx

from scheduling_agent.application.agent import AgentConfig, SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import CalendarPort, ChatModel, Clock, Embedder, FailPoints
from scheduling_agent.application.task_runner import AgentKit
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Makes the module `sqlite3` (standard library) available.
- Brings in `Callable`, `Mapping` from the standard library module `collections.abc`.
- Makes the module `httpx` (installed package) available.
- Brings in `AgentConfig` (The caps of a run and the size of one model answer.), `SchedulingAgent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.) from the project module `scheduling_agent.application.agent`.
- Brings in `MemoryService` (Remember what people say, recall the three most relevant facts for a task, forget on request.) from the project module `scheduling_agent.application.memory_service`.
- Brings in `CalendarPort` (The calendar service. Writes take an idempotency key; a repeated key returns the first result.), `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `Clock` (Time, injected so tests are deterministic.), `Embedder` (Turns texts into vectors.), `FailPoints` (Named places where a test can kill the process, to prove a crash there is survivable.) from the project module `scheduling_agent.application.ports`.
- Brings in `AgentKit` (One agent with the stores it was built on, so a runner can read what it did.) from the project module `scheduling_agent.application.task_runner`.

`src/scheduling_agent/infrastructure/wiring.py`, lines 15 to 28:

```python
from scheduling_agent.application.tools import ToolBox
from scheduling_agent.infrastructure import failpoints
from scheduling_agent.infrastructure.agent_db import AgentDb
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
)
from scheduling_agent.infrastructure.env import choice, optional_text, positive_float, text
from scheduling_agent.infrastructure.files import FilePromptStore
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.sqlite import apply_sql, connect
```

- Brings in `ToolBox` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.) from the project module `scheduling_agent.application.tools`.
- Brings in `failpoints` from the project module `scheduling_agent.infrastructure`.
- Brings in `AgentDb` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.) from the project module `scheduling_agent.infrastructure.agent_db`.
- Brings in `HttpCalendar` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.) from the project module `scheduling_agent.infrastructure.calendar_client`.
- Brings in `EmbeddingStore` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.), `OpenAICompatibleEmbedder` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.), `RecordedEmbedder` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.), `RecordingEmbedder` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.) from the project module `scheduling_agent.infrastructure.embeddings`.
- Brings in `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_float` (A number greater than zero.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `FilePromptStore` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.) from the project module `scheduling_agent.infrastructure.files`.
- Brings in `AgentSettings` (Where things live and how a run is capped. See env.example for each variable.) from the project module `scheduling_agent.infrastructure.settings`.
- Brings in `apply_sql` (Run SQL script files in the order given (the numbered files under sql/).), `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.

`src/scheduling_agent/infrastructure/wiring.py`, lines 31 to 42:

```python
def build_embedder(settings: AgentSettings, environ: Mapping[str, str] | None = None) -> Embedder:
    """`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."""
    env = os.environ if environ is None else environ
    if settings.embedder_provider == "recorded":
        return RecordedEmbedder(EmbeddingStore(settings.embeddings_path), settings.embed_model)
    http = httpx.Client(timeout=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0))
    live = OpenAICompatibleEmbedder(
        http,
        text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
        settings.embed_model,
        optional_text(env, "OPENAI_API_KEY"),
    )
```

- Defines the function `build_embedder`. It returns the project type `Embedder`. The author's own description: "`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."
- Its parameters:
    - `settings` holds the project type `AgentSettings`.
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Decision: the indented lines below run only when `settings.embedder_provider == 'recorded'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `RecordedEmbedder` to the caller.
  - `RecordedEmbedder` from the project's `scheduling_agent.infrastructure.embeddings` (Replays recorded vectors. A text nobody embedded raises `RecordingMissing`.).
  - `EmbeddingStore` from the project's `scheduling_agent.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
  - `positive_float` from the project's `scheduling_agent.infrastructure.env` (A number greater than zero.).
- Stores the result of calling `OpenAICompatibleEmbedder` under the name `live`.
  - `OpenAICompatibleEmbedder` from the project's `scheduling_agent.infrastructure.embeddings` (Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide.).
  - `text` from the project's `scheduling_agent.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `optional_text` from the project's `scheduling_agent.infrastructure.env` (The variable's text, or None when it is unset or blank.).

`src/scheduling_agent/infrastructure/wiring.py`, lines 43 to 50:

```python
    if choice(env, "RECORD", "off", ("on", "off")) == "on":
        return RecordingEmbedder(live, EmbeddingStore(settings.embeddings_path))
    return live


def build_calendar(settings: AgentSettings) -> HttpCalendar:
    """The HTTP client for the calendar service named in the settings."""
    return HttpCalendar(httpx.Client(timeout=10.0), settings.calendar_url)
```

- Decision: the indented lines below run only when `choice(env, 'RECORD', 'off', ('on', 'off')) == 'on'` is true.
  - `==` means equal.
  - `choice` from the project's `scheduling_agent.infrastructure.env` (One of the `allowed` strings.).
- Ends the function and gives back the result of calling `RecordingEmbedder` to the caller.
  - `RecordingEmbedder` from the project's `scheduling_agent.infrastructure.embeddings` (Wraps a live embedder and writes each new vector into the recording; known texts are replayed.).
  - `EmbeddingStore` from the project's `scheduling_agent.infrastructure.embeddings` (A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded.).
- Ends the function and gives back the value named `live` to the caller.
- Defines the function `build_calendar`. It returns the project type `HttpCalendar`. The author's own description: "The HTTP client for the calendar service named in the settings."
- Its parameters:
    - `settings` holds the project type `AgentSettings`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `HttpCalendar` to the caller.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
  - `httpx.Client` makes an HTTP client.

`src/scheduling_agent/infrastructure/wiring.py`, lines 53 to 64:

```python
def build_kit(
    settings: AgentSettings,
    model: ChatModel,
    clock: Clock,
    embedder: Embedder,
    calendar: CalendarPort | None = None,
    connection: sqlite3.Connection | None = None,
    points: FailPoints | None = None,
    new_run_id: Callable[[], str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> AgentKit:
    """One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither."""
```

- Defines the function `build_kit`. It returns the project type `AgentKit`. The author's own description: "One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither."
- Its parameters:
    - `settings` holds the project type `AgentSettings`.
    - `model` holds the project type `ChatModel`.
    - `clock` holds the project type `Clock`.
    - `embedder` holds the project type `Embedder`.
    - `calendar` holds the project type `CalendarPort`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `connection` holds `sqlite3.Connection`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `points` holds the project type `FailPoints`, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `new_run_id` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/wiring.py`, lines 65 to 78:

```python
    env = os.environ if environ is None else environ
    db_connection = connection or connect(settings.agent_db)
    apply_sql(db_connection, settings.sql_dir / "agent" / "001_schema.sql")
    store = AgentDb(db_connection)
    cal = calendar or build_calendar(settings)
    marks = points or failpoints.from_env(env)
    tools = ToolBox(cal, store, store, clock, marks)
    memory = MemoryService(store, embedder, clock, settings.people)
    prompt = FilePromptStore(settings.prompts_dir).load("agent", settings.prompt_version)
    config = AgentConfig(settings.max_steps, settings.max_tokens, settings.max_seconds)
    if new_run_id is None:
        agent = SchedulingAgent(model, tools, store, store, store, memory, clock, prompt, config, marks)
    else:
        agent = SchedulingAgent(model, tools, store, store, store, memory, clock, prompt, config, marks, new_run_id)
```

- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of combining conditions: `connection or connect(settings.agent_db)` under the name `db_connection`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).
- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Stores the result of calling `AgentDb` under the name `store`.
  - `AgentDb` from the project's `scheduling_agent.infrastructure.agent_db` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.).
- Stores the result of combining conditions: `calendar or build_calendar(settings)` under the name `cal`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `build_calendar`, a function of this file (The HTTP client for the calendar service named in the settings.).
- Stores the result of combining conditions: `points or failpoints.from_env(env)` under the name `marks`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - The method `from_env` of `failpoints`.
- Stores the result of calling `ToolBox` under the name `tools`.
  - `ToolBox` from the project's `scheduling_agent.application.tools` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.).
- Stores the result of calling `MemoryService` under the name `memory`.
  - `MemoryService` from the project's `scheduling_agent.application.memory_service` (Remember what people say, recall the three most relevant facts for a task, forget on request.).
- Stores the result of calling `FilePromptStore(settings.prompts_dir).load` under the name `prompt`.
  - The method `load` of `FilePromptStore(settings.prompts_dir)`.
  - `FilePromptStore` from the project's `scheduling_agent.infrastructure.files` (Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name.).
- Stores the result of calling `AgentConfig` under the name `config`.
  - `AgentConfig` from the project's `scheduling_agent.application.agent` (The caps of a run and the size of one model answer.).
- Decision: the indented lines below run only when `new_run_id is None` is true.
  - `is` means the very same object.
- Stores the result of calling `SchedulingAgent` under the name `agent`.
  - `SchedulingAgent` from the project's `scheduling_agent.application.agent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.).
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the result of calling `SchedulingAgent` under the name `agent`.
  - `SchedulingAgent` from the project's `scheduling_agent.application.agent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.).

`src/scheduling_agent/infrastructure/wiring.py`, lines 79 to 79:

```python
    return AgentKit(agent, store, store, store, memory, cal)
```

- Ends the function and gives back the result of calling `AgentKit` to the caller.
  - `AgentKit` from the project's `scheduling_agent.application.task_runner` (One agent with the stores it was built on, so a runner can read what it did.).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import scheduling_agent.infrastructure.recording; print(scheduling_agent.infrastructure.recording.__doc__)"
```

What you should see (captured from this repository):

```text
Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

A recording is a JSON Lines file. Each line holds the request fingerprint, the call's tag, a note about what
produced it and the response. Fixtures hold synthetic data only (no credentials, no personal data).
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/scheduling_agent/infrastructure').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
agent_db.py 2
anthropic_chat.py 2
calendar_client.py 2
calendar_db.py 4
calendar_seed.py 2
clock.py 1
embeddings.py 7
env.py 8
failpoints.py 3
files.py 2
logging.py 4
...
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

- **Common mistakes with this layer.** Letting an adapter decide business rules (they belong in the domain), reading environment variables in many places instead of the one settings module, or swallowing errors. Adapters here turn vendor errors into the project's own named errors.

## Check yourself

1. What is the job of `src/scheduling_agent/infrastructure/recording.py`?

   *Answer:* Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

2. What is the job of `src/scheduling_agent/infrastructure/resilient.py`?

   *Answer:* A decorator that retries transient model failures with backoff and jitter.

3. What is the job of `src/scheduling_agent/infrastructure/retry.py`?

   *Answer:* Retry with exponential backoff and jitter for calls that cross the network.

4. What is the job of `src/scheduling_agent/infrastructure/scripted_policy.py`?

   *Answer:* A deterministic stand-in for the model: a rule-based planner that speaks the same tool-calling protocol.

5. What is the job of `src/scheduling_agent/infrastructure/settings.py`?

   *Answer:* Configuration from the environment, validated once at startup (twelve-factor).

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
