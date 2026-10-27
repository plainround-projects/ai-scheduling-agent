# Python

## What it is

**Python** is a programming language. A **program** is a text file of instructions; a **programming language** is the set of rules for writing them. Python is easy to read: it uses indentation (spaces at the start of a line) to show which lines belong together, and plain words for most operations.

The program that reads and runs Python code is the **interpreter**, also called `python`. It reads the file, turns each line into simple internal steps (called *bytecode*), and carries them out one by one. You do not compile first.

Python code is split into **modules** (files ending in `.py`) and **packages** (folders of modules). A **variable** is a name for a value (`count = 3`). A **function** is named, reusable code (`def add(a, b): return a + b`). A **class** is a blueprint for objects that bundle data with behavior. A **type** says what kind of value something is: whole number (`int`), decimal number (`float`), text (`str`), true or false (`bool`), list, dictionary.

## Why this repository uses it

Python is the language of the AI ecosystem: the Claude SDK, the model-serving tools and the test tools are all Python libraries. It reads close to plain English, which suits a learning repository whose goal is that you understand the code.

The project asks for Python 3.12 or newer (`requires-python = ">=3.12"`). The Makefile uses 3.13 when it is installed. Newer syntax used here includes the `X | None` type form, `StrEnum` and `@dataclass(slots=True)`.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/` | 46 Python files: the program itself |
| `tests/` | 17 Python files: automated tests |
| `scripts/` | 2 Python helper script(s) that generate the committed data files |
| `pyproject.toml` | declares the Python version and the command-line programs |
| `Makefile` | starts every Python program through `.venv/bin` |

## How it works underneath

**Objects everywhere.** Every value in Python is an *object*: a chunk of memory with a type and some data. A variable is a label attached to an object. `a = b` makes a second label on the same object; it does not copy.

**Mutable and immutable.** Numbers, strings, tuples and frozen dataclasses cannot be changed after creation (they are *immutable*). Lists, dictionaries and sets can (they are *mutable*). Code that shares data between threads or between layers prefers immutable objects.

**The import system.** `import a.b` looks for a folder `a` with a file `b.py` on the module search path `sys.path`, runs the file once, and keeps the result in `sys.modules` so later imports reuse it.

**Type hints are not checked at run time.** The interpreter ignores them. The separate tool mypy reads them and reports mismatches (see `mypy.md`).

**Exceptions and the call stack.** Each running function has a frame on the stack. When an exception is raised, Python unwinds the stack frame by frame until an `except` matches; if none does, the program ends and prints a *traceback*, the list of frames.

**Threads and the GIL.** The standard interpreter lets only one thread run Python bytecode at a time (the *global interpreter lock*). Threads are therefore good for waiting on the network, not for heavy calculation. The test helpers and servers here use them for waiting.

**Garbage collection.** Python counts the labels attached to each object and frees it when the count reaches zero.

## Walkthrough of this repository's use

### A first tour of the language (every snippet was run; the output is real)

#### Values, names and types

A **value** is a piece of data. A **name** (variable) is a label you attach to a value with `=`. Every value has a **type**: `int` (whole number), `float` (decimal number), `str` (text), `bool` (`True` or `False`). `print(...)` shows values on the screen; `type(x)` tells you the type.

```python
price = 12.5
name = "meter"
count = 3
print(name, price * count, type(count), type(price), type(name), count > 2)
```

It prints:

```text
meter 37.5 <class 'int'> <class 'float'> <class 'str'> True
```

#### Text

Text is written in quotes. An *f-string* (`f"..."`) fills in values written between braces. Text has methods you call with a dot.

```python
who = "world"
print(f"hello {who}, {len(who)} letters", who.upper(), who.replace("o", "0"))
```

It prints:

```text
hello world, 5 letters WORLD w0rld
```

#### Lists and loops

A **list** is an ordered collection in square brackets. `for item in list:` repeats the indented lines once for each item. A list comprehension builds a new list in one line.

```python
prompts = ["a", "bb", "ccc"]
for p in prompts:
    print(p, len(p))
print([len(p) for p in prompts])
```

It prints:

```text
a 1
bb 2
ccc 3
[1, 2, 3]
```

#### Dictionaries

A **dictionary** (dict) is a collection of `key: value` pairs in braces. You look a value up by its key; `.get(key, default)` gives a default when the key is missing instead of raising an error.

```python
row = {"id": "p01", "kind": "short"}
row["tokens"] = 12
print(row["id"], row.get("missing", "none"), list(row))
```

It prints:

```text
p01 none ['id', 'kind', 'tokens']
```

#### Decisions

`if`, `elif` and `else` choose which indented block runs. Indentation (four spaces) is the grammar: it marks what belongs to what.

```python
n = 7
if n < 5:
    print("small")
elif n < 10:
    print("medium")
else:
    print("large")
```

It prints:

```text
medium
```

#### Functions

`def name(parameters):` defines reusable code. `return` hands a value back. A function with a docstring (a text in triple quotes as its first line) documents itself.

```python
def cost(tokens, per_thousand):
    """Dollars for a number of tokens."""
    return tokens / 1000 * per_thousand
print(cost(2500, 0.0005), cost.__doc__)
```

It prints:

```text
0.00125 Dollars for a number of tokens.
```

#### Classes and dataclasses

A **class** bundles data with the functions that use it. A dataclass writes the boring parts for you.

```python
from dataclasses import dataclass
@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
u = Usage(10, 4)
print(u, u.input_tokens + u.output_tokens)
```

It prints:

```text
Usage(input_tokens=10, output_tokens=4) 14
```

#### Errors

When something goes wrong Python *raises an exception*. `try`/`except` catches it so the program can respond instead of stopping.

```python
try:
    int("twelve")
except ValueError as error:
    print("caught:", error)
```

It prints:

```text
caught: invalid literal for int() with base 10: 'twelve'
```

### How the code is laid out

All code of the program lives in the package `scheduling_agent` under `src/`. It has four sub-packages that form layers: `domain` (the core ideas, with no outside technology), `application` (the use cases that combine them), `infrastructure` (adapters to files, databases, networks and vendor SDKs) and `interfaces` (the command line, the web server). The rule is: outer layers may import inner ones, never the other way. `import-linter` enforces it (see `import-linter.md`).

| File | What the file says it is (its own first docstring line) |
| --- | --- |
| `scripts/make_calendar_seed.py` | Write sql/calendar/002_seed.sql: five people and two weeks of meetings (Monday 2026-11-02 to Friday 2026-11-13). |
| `scripts/make_tasks.py` | Write data/tasks.jsonl: 30 tasks, each with the calendar end state it should reach. |
| `src/scheduling_agent/__init__.py` | A scheduling agent: approval for every write, budgets, crash-safe resumption and long-term memory. |
| `src/scheduling_agent/application/__init__.py` | Use cases and the ports they need. Depends on the domain only. |
| `src/scheduling_agent/application/agent.py` | The agent loop: model step, tool calls, a checkpoint after every step, writes only after a person approves. |
| `src/scheduling_agent/application/memory_service.py` | Long-term memory with a write policy: only what a person states about themselves, one fact per topic. |
| `src/scheduling_agent/application/ports.py` | The boundaries the use cases depend on. Adapters in `infrastructure` implement them. |
| `src/scheduling_agent/application/task_runner.py` | Run the task set and judge every task by the calendar's real end state, never by what the agent said. |
| `src/scheduling_agent/application/tools.py` | The agent's tools: reads run as they are, every write is a proposal that waits for a person's approval. |
| `src/scheduling_agent/domain/__init__.py` | Pure domain logic. Depends on nothing outside the standard library. |
| `src/scheduling_agent/domain/approvals.py` | Value objects for approvals, audit lines and the result of a calendar write. |
| `src/scheduling_agent/domain/budget.py` | Budgets around the agent loop: steps, tokens and wall-clock time, each checked on its own. |
| `src/scheduling_agent/domain/calendar.py` | Calendar rules: working hours, the half-hour grid, overlaps and the search for free slots. |
| `src/scheduling_agent/domain/errors.py` | Named errors. Callers catch these, never a vendor SDK's exception types. |
| `src/scheduling_agent/domain/llm.py` | Vendor-neutral value objects for one chat-model call. No SDK is imported here. |
| `src/scheduling_agent/domain/memory.py` | Long-term memory: facts a person states, a write policy that keeps one fact per topic, and recall by score. |
| `src/scheduling_agent/domain/prompts.py` | A prompt file: its name, its version line and its text. |
| `src/scheduling_agent/domain/proposals.py` | Write proposals, approvals and the idempotency key that makes a replayed write harmless. |
| `src/scheduling_agent/domain/retrieval.py` | Vector similarity for memory recall. |
| `src/scheduling_agent/domain/run.py` | A run of the agent: its status, its saved messages and the write it may be waiting on. |
| `src/scheduling_agent/domain/tasks.py` | A task for the agent and the calendar end state it must reach. |
| `src/scheduling_agent/infrastructure/__init__.py` | Adapters that implement the ports: model clients, files, settings, logging. |
| `src/scheduling_agent/infrastructure/agent_db.py` | The agent's own SQLite database: saved runs, approvals, the audit log and memory facts. |
| `src/scheduling_agent/infrastructure/anthropic_chat.py` | A chat model on the Anthropic Messages API, through the official SDK. |
| `src/scheduling_agent/infrastructure/calendar_client.py` | The calendar service as seen from the agent: an HTTP client with timeouts, retries and an Idempotency-Key header. |
| `src/scheduling_agent/infrastructure/calendar_db.py` | The calendar service's storage: events, attendees and idempotency keys in SQLite. |
| `src/scheduling_agent/infrastructure/calendar_seed.py` | Create and reset the calendar database from the numbered SQL files under sql/calendar. |
| `src/scheduling_agent/infrastructure/clock.py` | The real clock, behind the `Clock` port. |
| `src/scheduling_agent/infrastructure/embeddings.py` | Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording. |
| `src/scheduling_agent/infrastructure/env.py` | Helpers that read and validate environment variables (twelve-factor configuration). |
| `src/scheduling_agent/infrastructure/failpoints.py` | Named places where a test can kill the process with SIGKILL, to prove a crash there is survivable. |
| `src/scheduling_agent/infrastructure/files.py` | Readers for prompt files and the task set. |
| `src/scheduling_agent/infrastructure/logging.py` | Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`). |
| `src/scheduling_agent/infrastructure/model_factory.py` | Builds the configured chat model from the environment: recorded, local server or Claude. |
| `src/scheduling_agent/infrastructure/openai_compatible.py` | A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted). |
| `src/scheduling_agent/infrastructure/recording.py` | Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures. |
| `src/scheduling_agent/infrastructure/resilient.py` | A decorator that retries transient model failures with backoff and jitter. |
| `src/scheduling_agent/infrastructure/retry.py` | Retry with exponential backoff and jitter for calls that cross the network. |
| `src/scheduling_agent/infrastructure/scripted_policy.py` | A deterministic stand-in for the model: a rule-based planner that speaks the same tool-calling protocol. |
| `src/scheduling_agent/infrastructure/settings.py` | Configuration from the environment, validated once at startup (twelve-factor). |
| `src/scheduling_agent/infrastructure/shutdown.py` | Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work. |
| `src/scheduling_agent/infrastructure/sqlite.py` | SQLite connections: autocommit off, foreign keys on, one writer at a time (`BEGIN IMMEDIATE`). |
| `src/scheduling_agent/infrastructure/state_codec.py` | Run state to JSON and back, for the checkpoint table. |
| `src/scheduling_agent/infrastructure/wiring.py` | Build the agent and everything it stands on from the settings. |
| `src/scheduling_agent/interfaces/__init__.py` | Command-line programs. They wire adapters into use cases and own exit codes. |
| `src/scheduling_agent/interfaces/calendar_api.py` | The calendar service over HTTP: free slots, one event, book and cancel with an Idempotency-Key header. |
| `src/scheduling_agent/interfaces/calendar_server.py` | The `calendar-service` command: create the database and serve the calendar over HTTP. |
| `src/scheduling_agent/interfaces/cli.py` | The `agent` command: run a task, approve or reject a write, resume a run, tell it a preference, run the task set. |

The tests under `tests/` use pytest (see `pytest.md`):

| Test file | What it contains |
| --- | --- |
| `tests/conftest.py` | Shared builders for tests: a fixed clock, a hashing embedder and a ready agent kit on in-memory databases. |
| `tests/e2e/conftest.py` | The e2e tests reuse the fixture that starts the calendar service as a real process. |
| `tests/e2e/test_lesson_scenario.py` | The lesson's step 6 through the real HTTP service: 30 tasks, three runs each, judged by the calendar's end state. 1 test functions, for example `test_the_thirty_tasks_three_times_each_through_the_real_http_service_all_reach_their_end_state`. |
| `tests/integration/conftest.py` | Fixtures that start the calendar service as a real process on a free port. |
| `tests/integration/test_processes.py` | The calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes. 6 test functions, for example `test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice`, `test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume`, `test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person`, .... |
| `tests/live/test_live_models.py` | Opt-in tests that call real models. Run with `make test-live`; skipped in every other run. 2 test functions, for example `test_claude_starts_by_reading_the_calendar_not_by_writing`, `test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects`. |
| `tests/unit/application/test_memory_and_task_runner.py` | 10 test functions, for example `test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten`, `test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first`, `test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects`, .... |
| `tests/unit/application/test_tools_and_agent.py` | 19 test functions, for example `test_the_tool_list_has_two_reads_and_three_writes_with_schemas`, `test_reads_return_slots_and_events_and_errors_the_model_can_read`, `test_a_proposal_snapshots_the_event_it_would_change`, .... |
| `tests/unit/domain/test_calendar_memory_budget.py` | 16 test functions, for example `test_a_valid_slot_passes_and_each_rule_names_what_it_broke`, `test_overlap_is_half_open_so_back_to_back_meetings_do_not_collide`, `test_an_event_has_an_end_and_a_key_that_ignores_its_id`, .... |
| `tests/unit/domain/test_llm.py` | 5 test functions, for example `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, .... |
| `tests/unit/domain/test_tasks.py` | 4 test functions, for example `test_the_lessons_mix_of_thirty_tasks_is_accepted`, `test_a_wrong_mix_duplicate_ids_and_an_impossible_task_that_changes_things_are_rejected`, `test_the_expected_end_state_is_the_seed_with_the_removals_and_additions_applied`, .... |
| `tests/unit/infrastructure/test_agent_db_policy_misc.py` | 13 test functions, for example `test_a_run_state_survives_a_round_trip_with_messages_tool_calls_and_a_pending_write`, `test_saving_a_run_twice_updates_it_and_load_returns_the_latest_state`, `test_approvals_are_created_once_per_step_decided_once_and_listed_while_pending`, .... |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 11 test functions, for example `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, .... |
| `tests/unit/infrastructure/test_calendar_service.py` | 14 test functions, for example `test_the_seed_has_five_people_and_two_weeks_of_meetings_and_nobody_is_double_booked`, `test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event`, `test_two_different_bookings_with_identical_content_but_different_keys_are_not_mistaken_for_duplicates`, .... |
| `tests/unit/infrastructure/test_openai_compatible.py` | 12 test functions, for example `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, .... |
| `tests/unit/infrastructure/test_recording.py` | 6 test functions, for example `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, .... |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 15 test functions, for example `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, .... |

### The language features this code uses, with a real example of each

#### Imports

An *import* brings code from another file or package into this one. `import json` makes the module available as `json.something`. `from json import loads` brings in just the name `loads`. A **module** is one `.py` file; a **package** is a folder of modules with an `__init__.py` file. Imports that start with the project's own package name (for example `from scheduling_agent.domain...`) are the project's own code; the rest come from the standard library or from installed packages.

From this repository, `src/scheduling_agent/application/agent.py`, lines 10 to 13:

```python
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import ApprovalStore, AuditLog, ChatModel, CheckpointStore, Clock, FailPoints
from scheduling_agent.application.tools import ToolBox, dump, tool_specs
from scheduling_agent.domain.budget import Budget
```

#### `from __future__ import annotations`

Makes Python store type annotations as text instead of evaluating them when the function or class is defined. A class can then name itself in an annotation, and imports used only for types cost nothing at run time. Every module of this repository starts with it.

From this repository, `src/scheduling_agent/application/agent.py`, lines 3 to 4:

```python
from __future__ import annotations

```

#### Functions with type hints

`def name(a: int, b: str = "x") -> bool:` defines a function. After each parameter, `: int` is a *type hint*: a note for people and for the mypy checker that says what kind of value is expected (Python itself does not enforce it). `= "x"` gives a *default value* used when the caller leaves the argument out. `-> bool` says what the function returns.

From this repository, `src/scheduling_agent/application/agent.py`, lines 75 to 85:

```python
    def start(self, task: str, session: str, run_id: str | None = None) -> RunState:
        """Begin a run: recall what people said, save the new run, then drive it until it stops or waits."""
        facts = self._memory.recall(task)
        first = ChatMessage.user(task + memory_block(facts))
        state = RunState(
            run_id or self._new_run_id(), task, session, RunStatus.RUNNING, 0, 0, (first,), created_at=self._clock.now()
        )
        self._checkpoints.save(state, self._clock.now())
        _log.info("run started", extra={"fields": {"run_id": state.run_id, "recalled_facts": len(facts)}})
        self._failpoints.hit("run_created")
        return self._drive(state)
```

#### Keyword-only parameters

A bare `*,` in the parameter list means every parameter after it must be passed by name: `retry(f, attempts=3)`. This stops mixups between arguments of the same type and makes calls readable.

From this repository, `tests/integration/conftest.py`, lines 70 to 84:

```python
def agent(
    service: Service, tmp_path: Path, *args: str, failpoint: str | None = None
) -> subprocess.CompletedProcess[str]:
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

#### Classes and `self`

A **class** is a blueprint for objects that bundle data and behavior. `__init__` runs when an object is created; its first parameter, `self`, is the object being built, and `self.x = value` stores data on it. A **method** is a function defined inside a class; every method receives `self` first.

From this repository, `src/scheduling_agent/domain/errors.py`, lines 30 to 35:

```python
class BudgetExceeded(DomainError):
    """A run hit one of its caps: steps, tokens or wall-clock time."""

    def __init__(self, cap: str, message: str) -> None:
        super().__init__(message)
        self.cap = cap
```

#### Dataclasses

`@dataclass` is a *decorator* (a line starting with `@` above a definition that changes it). It reads the annotated names in the class body and writes `__init__`, `__repr__` and `__eq__` for you. `frozen=True` forbids changing an object after creation, so it can be shared safely and used as a dictionary key. `slots=True` stores fields in a compact fixed layout.

From this repository, `src/scheduling_agent/application/agent.py`, lines 28 to 35:

```python
@dataclass(frozen=True, slots=True)
class AgentConfig:
    """The caps of a run and the size of one model answer."""

    max_steps: int = 12
    max_tokens: int = 4000
    max_seconds: float = 30.0
    max_output_tokens: int = 400
```

#### Enums

An **enum** is a fixed set of named values. `StrEnum` makes each member also a string (`Role.USER == "user"`), which is convenient for JSON and logs.

From this repository, `src/scheduling_agent/domain/llm.py`, lines 13 to 18:

```python
class Role(StrEnum):
    """Who wrote a message."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
```

#### Protocols (structural typing)

A `Protocol` lists methods an object must have. Any class that has those methods is accepted wherever the protocol is asked for, without inheriting from it. This repository uses protocols as *ports*: the use cases ask for a `ChatModel` or a `Clock`, and the real adapter, the recording adapter and a test fake all fit.

From this repository, `src/scheduling_agent/application/ports.py`, lines 17 to 32:

```python
class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""

    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...

    @property
    def supports_sampling(self) -> bool:
        """False when the provider rejects `temperature` and `top_p` (the request then says so)."""
        ...

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...
```

#### Properties

`@property` turns a method into something read like a field: `model.name` instead of `model.name()`. The value is worked out each time.

From this repository, `src/scheduling_agent/application/ports.py`, lines 20 to 23:

```python
    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...
```

#### Class methods

`@classmethod` defines a method that receives the class (`cls`) instead of an object. It is used here as a named constructor: `ChatMessage.user("hi")`.

From this repository, `src/scheduling_agent/domain/llm.py`, lines 58 to 60:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)
```

#### Exceptions: raise, try, except

An **exception** is an object that signals a problem and jumps out of the running code until something catches it. `raise X(...)` throws one. `try:` ... `except X:` runs the second block if the first threw an `X`. `raise Y from X` throws a new exception while keeping the original as its cause. `finally:` runs whatever happens.

From this repository, `src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 92 to 96:

```python
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
```

#### Custom exception classes

A class that inherits from `Exception` is a new kind of error. Giving errors their own names lets callers catch exactly the failures they know how to handle.

From this repository, `src/scheduling_agent/application/agent.py`, lines 24 to 25:

```python
class UnknownRun(DomainError):
    """No saved run with that id."""
```

#### `try` / `except` blocks

Code that might fail is placed under `try:`; the matching `except` names the error it handles.

From this repository, `src/scheduling_agent/application/agent.py`, lines 111 to 114:

```python
            try:
                budget.check(self._clock.monotonic())
            except BudgetExceeded as stop:
                return self._stop(state, stop)
```

#### `with` blocks

`with thing as name:` is a *context manager*: it runs setup code on entry and cleanup code on exit, even if an error happens inside. Files, locks, database connections and temporary folders all use it.

From this repository, `src/scheduling_agent/infrastructure/agent_db.py`, lines 87 to 91:

```python
        with self._lock:
            rows = self._db.execute(
                "SELECT run_id FROM runs WHERE status IN ('running', 'awaiting_approval') ORDER BY created_at, run_id"
            )
            return [r[0] for r in rows]
```

#### f-strings

A string starting with `f"` can hold `{expression}` parts that are replaced by their values: `f"{count} rows"`. After the expression, `:` begins a format (`{price:.4f}` means four decimals).

From this repository, `src/scheduling_agent/application/agent.py`, line 42:

```python
    lines = [f"- {f.person}: {f.text} (said {f.stated_on}, session {f.session})" for f in facts]
```

#### List and dict comprehensions

`[x * 2 for x in items if x > 0]` builds a list by looping. `{k: v for k, v in pairs}` builds a dictionary. Written inside `sum(...)` or `any(...)` without brackets, it is a *generator expression* that produces values one at a time.

From this repository, `src/scheduling_agent/application/agent.py`, line 42:

```python
    lines = [f"- {f.person}: {f.text} (said {f.stated_on}, session {f.session})" for f in facts]
```

#### Lambdas

`lambda x: x + 1` is a small unnamed function written inline. It is used for a sort key or a callback.

From this repository, `src/scheduling_agent/application/agent.py`, lines 61 to 62:

```python
        new_run_id: Callable[[], str] = lambda: uuid.uuid4().hex[:12],
    ) -> None:
```

#### Union types and `None`

`X | None` means "an X or nothing". `list[str]`, `dict[str, int]` and `tuple[int, ...]` describe collections and what is inside them. `Mapping`, `Sequence` and `Callable` (from `collections.abc`) describe *anything that behaves like* a dictionary, a list, or a function.

From this repository, `src/scheduling_agent/application/agent.py`, line 75:

```python
    def start(self, task: str, session: str, run_id: str | None = None) -> RunState:
```

#### Paths

`pathlib.Path` represents a file location as an object. The `/` operator joins parts (`root / "data" / "x.json"`), and methods such as `read_text()` read the file.

From this repository, `src/scheduling_agent/infrastructure/files.py`, lines 24 to 26:

```python
            raise PromptNotFound(f"no prompt file {path}")
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
```

#### Generators

A function containing `yield` returns a *generator*: it produces its values one at a time and pauses between them. A `yield` inside a function decorated with `@contextmanager` marks the point where the body of a `with` block runs.

From this repository, `src/scheduling_agent/infrastructure/sqlite.py`, lines 23 to 32:

```python
@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block as one write transaction: commit on success, roll back on any error."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
```

#### `Literal` and `Final`

`Literal["a", "b"]` as a type says the value must be exactly one of those. `Final` says a name is assigned once and never changed.

From this repository, `src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 18 to 19:

```python
Thinking = Literal["omit", "disabled", "between_tools"]

```

#### `*args` and `**kwargs`

`*args` collects extra positional arguments into a tuple; `**kwargs` collects extra named arguments into a dictionary. They let a wrapper pass everything on to the function it wraps.

From this repository, `src/scheduling_agent/infrastructure/calendar_client.py`, lines 57 to 61:

```python
        self._sleep = sleep

    def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        def once() -> dict[str, Any] | list[Any]:
            try:
```

#### `isinstance` and `getattr`

`isinstance(x, T)` asks whether `x` is a `T`. `getattr(obj, "name", default)` reads an attribute by a name held in a variable.

From this repository, `src/scheduling_agent/application/agent.py`, lines 146 to 148:

```python
            proposal = self._tools.propose(call.name, call.arguments)
            if not isinstance(proposal, Proposal):
                results.append(ChatMessage(Role.TOOL, dump(proposal), tool_call_id=call.id))
```

#### Threads

A **thread** is a second line of execution inside one program. Threads share memory, so code that changes shared data protects it with a *lock*. See `python-standard-library.md` for `threading`.

From this repository, `src/scheduling_agent/infrastructure/embeddings.py`, lines 69 to 73:

```python
        self._path = path
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
```

#### Generic functions with type parameters (Python 3.12)

`def name[T](...)` declares a *type parameter*: a stand-in for "whatever type the caller uses", so a function can promise "returns the same kind of thing it was given". `**P` declares a *parameter specification*, which stands for a whole list of parameters, used with `Concatenate` to describe a decorator that adds one argument. This is syntax new in Python 3.12, which is why the project requires 3.12.

From this repository, `src/scheduling_agent/infrastructure/calendar_db.py`, lines 41 to 53:

```python
def _locked[**P, R](method: Callable[Concatenate[SqliteCalendar, P], R]) -> Callable[Concatenate[SqliteCalendar, P], R]:
    """Run a method while holding the calendar's lock."""

    @functools.wraps(method)
    def wrapper(self: SqliteCalendar, *args: P.args, **kwargs: P.kwargs) -> R:
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


class SqliteCalendar:
    """Reads and idempotent writes. Every write and its idempotency key are committed in one transaction."""
```

#### Decorators you write yourself

A decorator is a function that takes a function and returns a replacement. `functools.wraps(method)` copies the original's name and docstring onto the replacement. Here a decorator makes a method take a lock before running.

From this repository, `src/scheduling_agent/infrastructure/calendar_db.py`, lines 38 to 50:

```python
    return hashlib.sha256(json.dumps({"op": operation, **payload}, sort_keys=True).encode()).hexdigest()


def _locked[**P, R](method: Callable[Concatenate[SqliteCalendar, P], R]) -> Callable[Concatenate[SqliteCalendar, P], R]:
    """Run a method while holding the calendar's lock."""

    @functools.wraps(method)
    def wrapper(self: SqliteCalendar, *args: P.args, **kwargs: P.kwargs) -> R:
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]

```

#### `if __name__ == "__main__"`

When a file is run directly, Python sets the special variable `__name__` to `"__main__"`. The guard makes some code run only in that case and not when the file is imported.

From this repository, `src/scheduling_agent/interfaces/calendar_server.py`, lines 43 to 45:

```python
if __name__ == "__main__":
    sys.exit(main())

```

### Running the code

You never type `python src/...` in this repository. The Makefile calls the programs that pip installed into `.venv/bin`, such as `.venv/bin/agent`, or runs `.venv/bin/python -m pytest`. `python -m NAME` means "run the module called NAME as a program". The `[project.scripts]` table of `pyproject.toml` (see `pyproject-toml.md`) says which function each installed program calls.

## Try it yourself

1. Which Python the project uses.

```bash
.venv/bin/python --version
```

What you should see (captured from this repository):

```text
Python 3.13.12
```

2. Two names, one list: appending through `y` changes what `x` sees, because `y = x` copies the label, not the list.

```bash
.venv/bin/python -c "x = [1, 2, 3]; y = x; y.append(4); print(x, x is y)"
```

What you should see (captured from this repository):

```text
[1, 2, 3, 4] True
```

3. Why money uses `Decimal`: binary floating point cannot store 0.1 exactly.

```bash
.venv/bin/python -c "print(0.1 + 0.2); from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

What you should see (captured from this repository):

```text
0.30000000000000004
0.3
```

4. Type hints are not enforced when the program runs. The error here comes from the `+`, not from the hint.

```bash
.venv/bin/python -c "def f(a: int) -> int: return a + 1
print(f('x'))" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
TypeError: can only concatenate str (not "int") to str
```

5. The project is an ordinary package that Python finds through the editable install.

```bash
.venv/bin/python -c "import scheduling_agent; print(scheduling_agent.__file__)"
```

What you should see (captured from this repository):

```text
src/scheduling_agent/__init__.py
```

## Mistakes people make

- **Thinking `=` copies.** `b = a` makes a second label; changing a list through one name changes it for both. The code copies explicitly (`list(x)`, `dict(x)`, `dataclasses.replace`) when it needs a separate object.
- **Using `float` for money.** Prices here are `Decimal` so the totals add up exactly.
- **A mutable default argument.** `def f(x=[])` shares one list across all calls. Defaults here are `None` or immutable values.
- **Catching every exception.** A bare `except:` hides bugs. The code names the exceptions it can handle.
- **Confusing indentation.** Mixed spaces and tabs break Python. `.editorconfig` sets four spaces for `.py` files.
- **Importing the wrong direction.** An inner layer importing an outer one makes cycles and drags technology into the core. `import-linter` fails the build if that happens.

## Check yourself

1. What does `-> bool` after a function signature say?

   *Answer:* That the function returns a `bool`. It is a hint for tools and readers.

2. What does `@dataclass(frozen=True)` give you?

   *Answer:* A class with generated `__init__`, `__repr__` and `__eq__`, whose objects cannot be changed after creation.

3. Why is a `Protocol` used for `ChatModel`?

   *Answer:* So any class with the right methods (real adapter, recording, test fake) is accepted without inheriting from a base class.

4. What does `raise B from A` record?

   *Answer:* That `B` was caused by `A`, so the traceback shows both.

5. What does `if __name__ == "__main__":` do?

   *Answer:* Runs the indented code only when the file is run directly, not when imported.

## Further reading

- The Python Tutorial and Language Reference, https://docs.python.org/3.13/tutorial/ and https://docs.python.org/3.13/reference/ (the project requires Python 3.12 or newer; examples here were run on Python 3.13).
