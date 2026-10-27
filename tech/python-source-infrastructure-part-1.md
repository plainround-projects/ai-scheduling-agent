# Python source, the infrastructure layer (part 1 of 2)

## What it is

This note walks through every Python file of the `infrastructure` layer of `scheduling_agent`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **infrastructure** layer is the adapters: the code that touches the world. Files, databases, HTTP calls to a model server, the Claude SDK, the clock, signals, logging and settings all live here. Each adapter implements a port from the application layer.

## Why this repository uses it

Keeping every contact with the outside in one layer makes it easy to swap (recorded answers instead of a live model) and to test (a fake HTTP transport instead of a network).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/infrastructure/__init__.py` | 1 non-blank lines |
| `src/scheduling_agent/infrastructure/agent_db.py` | 177 non-blank lines |
| `src/scheduling_agent/infrastructure/anthropic_chat.py` | 102 non-blank lines |
| `src/scheduling_agent/infrastructure/calendar_client.py` | 115 non-blank lines |
| `src/scheduling_agent/infrastructure/calendar_db.py` | 146 non-blank lines |
| `src/scheduling_agent/infrastructure/calendar_seed.py` | 17 non-blank lines |
| `src/scheduling_agent/infrastructure/clock.py` | 12 non-blank lines |
| `src/scheduling_agent/infrastructure/embeddings.py` | 105 non-blank lines |
| `src/scheduling_agent/infrastructure/env.py` | 53 non-blank lines |
| `src/scheduling_agent/infrastructure/failpoints.py` | 22 non-blank lines |
| `src/scheduling_agent/infrastructure/files.py` | 38 non-blank lines |
| `src/scheduling_agent/infrastructure/logging.py` | 40 non-blank lines |
| `src/scheduling_agent/infrastructure/model_factory.py` | 78 non-blank lines |
| `src/scheduling_agent/infrastructure/openai_compatible.py` | 109 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/scheduling_agent/infrastructure/__init__.py`

In its own words: "Adapters that implement the ports: model clients, files, settings, logging."

1 non-blank lines.

`src/scheduling_agent/infrastructure/__init__.py`, lines 1 to 1:

```python
"""Adapters that implement the ports: model clients, files, settings, logging."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/scheduling_agent/infrastructure/agent_db.py`

In its own words: "The agent's own SQLite database: saved runs, approvals, the audit log and memory facts."

177 non-blank lines; it defines `_approval`, `AgentDb`.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 1 to 14:

```python
"""The agent's own SQLite database: saved runs, approvals, the audit log and memory facts."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Callable, Sequence
from datetime import date, datetime

from scheduling_agent.domain.approvals import Approval, AuditLine
from scheduling_agent.domain.errors import ApprovalError
from scheduling_agent.domain.memory import Fact, FactKind
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `sqlite3` (standard library) available.
- Makes the module `threading` (standard library) available.
- Makes the module `uuid` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime` from the standard library module `datetime`.
- Brings in `Approval` (A proposal and what a person decided about it.), `AuditLine` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).) from the project module `scheduling_agent.domain.approvals`.
- Brings in `ApprovalError` (An approval is missing, not approved, or was granted for a different proposal.) from the project module `scheduling_agent.domain.errors`.
- Brings in `Fact` (Something a person said about their own calendar, with where and when they said it and when it lapses.), `FactKind` (What a fact constrains.) from the project module `scheduling_agent.domain.memory`.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 15 to 22:

```python
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
from scheduling_agent.domain.run import RunState
from scheduling_agent.infrastructure import state_codec
from scheduling_agent.infrastructure.sqlite import transaction


def _approval(row: sqlite3.Row) -> Approval:
    proposal = json.loads(row["proposal_json"])
```

- Brings in `Action` (The three writes.), `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.) from the project module `scheduling_agent.domain.run`.
- Brings in `state_codec` from the project module `scheduling_agent.infrastructure`.
- Brings in `transaction` (Run a block as one write transaction: commit on success, roll back on any error.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Defines the function `_approval`. It returns the project type `Approval`.
- Its parameters:
    - `row` holds `sqlite3.Row`.
- Stores the result of calling `json.loads` under the name `proposal`.
  - `json.loads` turns JSON text into Python data.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 23 to 36:

```python
    return Approval(
        row["id"],
        row["run_id"],
        row["step"],
        Proposal(Action(proposal["action"]), proposal["args"]),
        ApprovalStatus(row["status"]),
        datetime.fromisoformat(row["created_at"]),
        datetime.fromisoformat(row["decided_at"]) if row["decided_at"] else None,
        row["decided_by"],
    )


class AgentDb:
    """Implements the checkpoint, approval, audit and memory ports on one SQLite connection."""
```

- Ends the function and gives back the result of calling `Approval` to the caller.
  - `Approval` from the project's `scheduling_agent.domain.approvals` (A proposal and what a person decided about it.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
  - `ApprovalStatus` from the project's `scheduling_agent.domain.proposals` (Where an approval is: waiting for a person, approved or rejected.).
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `Action` from the project's `scheduling_agent.domain.proposals` (The three writes.).
- Defines the class `AgentDb`. The author's own description: "Implements the checkpoint, approval, audit and memory ports on one SQLite connection."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 38 to 50:

```python
    def __init__(
        self, connection: sqlite3.Connection, new_id: Callable[[], str] = lambda: uuid.uuid4().hex[:10]
    ) -> None:
        self._db = connection
        self._new_id = new_id
        self._lock = threading.RLock()

    # --- checkpoints

    def save(self, state: RunState, now: datetime) -> None:
        """The run row and the step row, in one transaction."""
        with self._lock, transaction(self._db):
            created = state.created_at or now
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `connection` holds `sqlite3.Connection`.
    - `new_id` holds a function; if the caller leaves it out it is a small function.
- Stores the value named `connection` under the name `self._db` (as an attribute of this object, so other methods can use it).
- Stores the value named `new_id` under the name `self._new_id` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.RLock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.RLock` makes a lock the same thread may take again.
- Defines the method `save`. It returns nothing (None). The author's own description: "The run row and the step row, in one transaction."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
    - `now` holds a date and time.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- A `with` block: it sets up `self._lock`, `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Stores the result of combining conditions: `state.created_at or now` under the name `created`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/scheduling_agent/infrastructure/agent_db.py`, lines 51 to 67:

```python
            self._db.execute(
                "INSERT INTO runs (run_id, task, session, status, steps, tokens, state_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (run_id) DO UPDATE SET status = excluded.status, "
                "steps = excluded.steps, tokens = excluded.tokens, state_json = excluded.state_json, "
                "updated_at = excluded.updated_at",
                (
                    state.run_id,
                    state.task,
                    state.session,
                    state.status.value,
                    state.steps,
                    state.tokens,
                    state_codec.encode(state.with_(created_at=created)),
                    created.isoformat(),
                    now.isoformat(),
                ),
            )
```

- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - `.encode(...)` turns text into bytes.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).

`src/scheduling_agent/infrastructure/agent_db.py`, lines 68 to 81:

```python
            self._db.execute(
                "INSERT INTO run_steps (run_id, step, status, pending_approval_id, saved_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (run_id, step) DO UPDATE SET status = excluded.status, "
                "pending_approval_id = excluded.pending_approval_id, saved_at = excluded.saved_at",
                (
                    state.run_id,
                    state.steps,
                    state.status.value,
                    state.pending.approval_id if state.pending else None,
                    now.isoformat(),
                ),
            )

    def load(self, run_id: str) -> RunState | None:
```

- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Defines the method `load`. It returns the project type `RunState`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 82 to 95:

```python
        with self._lock:
            row = self._db.execute("SELECT state_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return state_codec.decode(row["state_json"]) if row else None

    def unfinished(self) -> list[str]:
        with self._lock:
            rows = self._db.execute(
                "SELECT run_id FROM runs WHERE status IN ('running', 'awaiting_approval') ORDER BY created_at, run_id"
            )
            return [r[0] for r in rows]

    # --- approvals

    def request(self, run_id: str, step: int, proposal: Proposal, now: datetime) -> Approval:
```

- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._db.execute('SELECT state_json FROM runs W...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.decode(...)` turns bytes into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `unfinished`. It returns a list of text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._db.execute` under the name `rows`.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `request`. It returns the project type `Approval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
    - `step` holds a whole number.
    - `proposal` holds the project type `Proposal`.
    - `now` holds a date and time.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 96 to 109:

```python
        with self._lock, transaction(self._db):
            row = self._db.execute("SELECT * FROM approvals WHERE run_id = ? AND step = ?", (run_id, step)).fetchone()
            if row is not None:
                return _approval(row)
            approval_id = f"ap-{self._new_id()}"
            self._db.execute(
                "INSERT INTO approvals (id, run_id, step, proposal_json, status, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', ?)",
                (approval_id, run_id, step, proposal.canonical(), now.isoformat()),
            )
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            return _approval(row)

    def get(self, approval_id: str) -> Approval | None:
```

- A `with` block: it sets up `self._lock`, `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Stores the result of calling `self._db.execute('SELECT * FROM approvals WHERE...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Decision: the indented lines below run only when `row is not None` is true.
  - `is not` means not the same object.
- Ends the function and gives back the result of calling `_approval` to the caller.
  - `_approval`, a function defined in this file or passed in.
- Stores a text built from pieces (an f-string) under the name `approval_id`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `_new_id` of `self`.
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - The method `canonical` of the project's `Proposal` (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Stores the result of calling `self._db.execute('SELECT * FROM approvals WHERE...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back the result of calling `_approval` to the caller.
  - `_approval`, a function defined in this file or passed in.
- Defines the method `get`. It returns the project type `Approval`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `approval_id` holds text.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 110 to 120:

```python
        with self._lock:
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        return _approval(row) if row else None

    def decide(self, approval_id: str, approved: bool, by: str, now: datetime) -> Approval:
        with self._lock, transaction(self._db):
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            if row is None:
                raise ApprovalError(f"unknown approval {approval_id}")
            if row["status"] != "pending":
                raise ApprovalError(f"approval {approval_id} was already {row['status']}")
```

- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._db.execute('SELECT * FROM approvals WHERE...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `_approval`, a function defined in this file or passed in.
- Defines the method `decide`. It returns the project type `Approval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `approval_id` holds text.
    - `approved` holds true or false.
    - `by` holds text.
    - `now` holds a date and time.
- A `with` block: it sets up `self._lock`, `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Stores the result of calling `self._db.execute('SELECT * FROM approvals WHERE...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Decision: the indented lines below run only when `row is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `row['status'] != 'pending'` is true.
  - `!=` means not equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 121 to 132:

```python
            self._db.execute(
                "UPDATE approvals SET status = ?, decided_at = ?, decided_by = ? WHERE id = ?",
                ("approved" if approved else "rejected", now.isoformat(), by, approval_id),
            )
            return _approval(self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone())

    def pending(self) -> list[Approval]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM approvals WHERE status = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return [_approval(r) for r in rows]
```

- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Ends the function and gives back the result of calling `_approval` to the caller.
  - `_approval`, a function defined in this file or passed in.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Defines the method `pending`. It returns a list of the project type `Approval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._db.execute("SELECT * FROM approvals WHERE...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `_approval`, a function defined in this file or passed in.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 134 to 146:

```python
    # --- audit

    def append(self, line: AuditLine) -> None:
        with self._lock, transaction(self._db):
            self._db.execute(
                "INSERT OR IGNORE INTO audit_log (at, run_id, step, action, outcome, approval_id, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (line.at.isoformat(), line.run_id, line.step, line.action, line.outcome, line.approval_id, line.detail),
            )

    def lines(self, run_id: str | None = None) -> list[AuditLine]:
        with self._lock:
            if run_id is None:
```

- Defines the method `append`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `line` holds the project type `AuditLine`.
- A `with` block: it sets up `self._lock`, `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Defines the method `lines`. It returns a list of the project type `AuditLine`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Decision: the indented lines below run only when `run_id is None` is true.
  - `is` means the very same object.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 147 to 149:

```python
                rows = self._db.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
            else:
                rows = self._db.execute("SELECT * FROM audit_log WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
```

- Stores the result of calling `self._db.execute('SELECT * FROM audit_log ORDER...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the result of calling `self._db.execute('SELECT * FROM audit_log WHERE...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 150 to 161:

```python
        return [
            AuditLine(
                datetime.fromisoformat(r["at"]),
                r["run_id"],
                r["step"],
                r["action"],
                r["outcome"],
                r["approval_id"],
                r["detail"],
            )
            for r in rows
        ]
```

- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 163 to 167:

```python
    # --- memory

    def facts(self) -> list[Fact]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM memory_facts ORDER BY person, topic").fetchall()
```

- Defines the method `facts`. It returns a list of the project type `Fact`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._db.execute('SELECT * FROM memory_facts OR...` under the name `rows`.
  - `.fetchall(...)` reads all rows of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 168 to 181:

```python
        return [
            Fact(
                r["person"],
                FactKind(r["kind"]),
                r["value"],
                r["text"],
                r["session"],
                date.fromisoformat(r["stated_on"]),
                date.fromisoformat(r["expires_on"]) if r["expires_on"] else None,
            )
            for r in rows
        ]

    def replace(self, facts: Sequence[Fact]) -> None:
```

- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `Fact` from the project's `scheduling_agent.domain.memory` (Something a person said about their own calendar, with where and when they said it and when it lapses.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `FactKind` from the project's `scheduling_agent.domain.memory` (What a fact constrains.).
  - `date.fromisoformat` reads a date from ISO text.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Defines the method `replace`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `facts` holds anything that behaves like a list of the project type `Fact`.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 182 to 183:

```python
        with self._lock, transaction(self._db):
            self._db.execute("DELETE FROM memory_facts")
```

- A `with` block: it sets up `self._lock`, `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 1 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.

`src/scheduling_agent/infrastructure/agent_db.py`, lines 184 to 200:

```python
            self._db.executemany(
                "INSERT INTO memory_facts (person, topic, kind, value, text, session, stated_on, expires_on) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        f.person,
                        ":".join(f.topic[1:]).rstrip(":"),
                        f.kind.value,
                        f.value,
                        f.text,
                        f.session,
                        f.stated_on.isoformat(),
                        f.expires_on.isoformat() if f.expires_on else None,
                    )
                    for f in facts
                ],
            )
```

- Calls `executemany` on the stored object `self._db`: it runs one SQL statement for a list of parameter sets with 2 argument(s); the result is not kept.
  - `executemany` on the stored object `self._db`: it runs one SQL statement for a list of parameter sets.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.rstrip(...)` removes spaces from the end of text.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.

### `src/scheduling_agent/infrastructure/anthropic_chat.py`

In its own words: "A chat model on the Anthropic Messages API, through the official SDK."

102 non-blank lines; it defines `_messages_payload`, `AnthropicChatModel`.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 1 to 14:

```python
"""A chat model on the Anthropic Messages API, through the official SDK.

The Messages API rejects `temperature`, `top_p` and `top_k` from API version 2026-10-21 on, so this adapter
reports `supports_sampling = False` and raises `UnsupportedParameter` if a request asks for them. Structured
output uses `output_config.format`; forced `tool_choice` is not used (newer models answer it with a 400).
"""

from __future__ import annotations

from typing import Any, Literal

import anthropic

from scheduling_agent.application.ports import Clock
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Any`, `Literal` from the standard library module `typing`.
- Makes the module `anthropic` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `scheduling_agent.application.ports`.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 15 to 26:

```python
from scheduling_agent.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage

Thinking = Literal["omit", "disabled", "between_tools"]

_STOP = {
    "end_turn": StopReason.END,
    "stop_sequence": StopReason.END,
    "max_tokens": StopReason.LENGTH,
    "tool_use": StopReason.TOOL_CALLS,
    "refusal": StopReason.REFUSAL,
}
```

- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.
- Stores the part of `Literal` picked by `('omit', 'disabled', 'betwe...` under the name `Thinking`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a dictionary with 5 entries under the name `_STOP`.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 29 to 40:

```python
def _messages_payload(messages: tuple[ChatMessage, ...]) -> list[dict[str, Any]]:
    """Map neutral messages to Messages API turns; consecutive tool results share one user turn."""
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role is Role.TOOL:
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif message.role is Role.ASSISTANT and message.tool_calls:
            blocks: list[dict[str, Any]] = [{"type": "text", "text": message.content}] if message.content else []
```

- Defines the function `_messages_payload`. It returns a list of a dictionary from text to any value. The author's own description: "Map neutral messages to Messages API turns; consecutive tool results share one user turn."
- Its parameters:
    - `messages` holds a fixed list of the project type `ChatMessage` (any length).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `out` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `messages`; `message` names the current item.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Stores a dictionary with 3 entries under the name `block`.
- Decision: the indented lines below run only when `out and out[-1]['role'] == 'user' and isinstance(out[-1]['content']...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `isinstance` asks whether a value is of a given type.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `message.role is Role.ASSISTANT and message.tool_calls` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
- Declares `blocks` as a list of a dictionary from text to any value and sets it to one of two values, chosen by a condition.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `A if condition else B` gives A when the condition is true and B otherwise.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 41 to 54:

```python
            blocks.extend(
                {"type": "tool_use", "id": c.id, "name": c.name, "input": dict(c.arguments)} for c in message.tool_calls
            )
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": message.role.value, "content": message.content})
    return out


class AnthropicChatModel:
    """Calls Claude. Build the SDK client with your key from the environment; this class never reads it."""

    def __init__(self, client: anthropic.Anthropic, model: str, clock: Clock, thinking: Thinking = "disabled") -> None:
        self._client = client
```

- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `AnthropicChatModel`. The author's own description: "Calls Claude. Build the SDK client with your key from the environment; this class never reads it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `client` holds `anthropic.Anthropic`.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `thinking` holds `Thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the value named `client` under the name `self._client` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 55 to 68:

```python
        self._model = model
        self._clock = clock
        self._thinking = thinking

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return False

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The keyword arguments for `messages.create` (public so tests can assert on them)."""
```

- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores the value named `thinking` under the name `self._thinking` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `False` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The keyword arguments for `messages.create` (public so tests can assert on them)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 69 to 82:

```python
        if request.temperature is not None or request.top_p is not None:
            raise UnsupportedParameter("the Messages API rejects temperature and top_p; leave them unset")
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_output_tokens,
            "messages": _messages_payload(request.messages),
        }
        if request.system:
            payload["system"] = request.system
        if self._thinking != "omit":
            payload["thinking"] = {"type": self._thinking}
        if request.response_schema is not None:
            payload["output_config"] = {"format": {"type": "json_schema", "schema": dict(request.response_schema)}}
        if request.tools:
```

- Decision: the indented lines below run only when `request.temperature is not None or request.top_p is not None` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
- Raises an error: the result of calling `UnsupportedParameter`. Execution jumps out to the nearest matching `except`.
  - `UnsupportedParameter` from the project's `scheduling_agent.domain.errors` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).).
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 3 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `_messages_payload`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `request.system` is true.
- Stores the `system` of `request` under the name `payload['system']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `self._thinking != 'omit'` is true.
  - `!=` means not equal.
- Stores a dictionary with 1 entry under the name `payload['thinking']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.
- Stores a dictionary with 1 entry under the name `payload['output_config']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 83 to 96:

```python
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
                for t in request.tools
            ]
        return payload

    def complete(self, request: ChatRequest) -> ChatResponse:
        payload = self.build_payload(request)
        started = self._clock.monotonic()
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
```

- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._client.messages.create` under the name `message`.
  - The method `create` of `self._client.messages`.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- `except` handler: it runs when the `try` block raised `anthropic.APIConnectionError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- `except` handler: it runs when the `try` block raised `anthropic.APIStatusError`; `error` names the error object.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 97 to 104:

```python
            if error.status_code in (408, 409, 429) or error.status_code >= 500:
                raise TransientModelError(f"HTTP {error.status_code}: {error.message}") from error
            raise PermanentModelError(f"HTTP {error.status_code}: {error.message}") from error
        elapsed = self._clock.monotonic() - started
        text = "".join(block.text for block in message.content if block.type == "text")
        calls = tuple(
            ToolCall(block.id, block.name, dict(block.input)) for block in message.content if block.type == "tool_use"
        )
```

- Decision: the indented lines below run only when `error.status_code in (408, 409, 429) or error.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Stores the result of calling `''.join` under the name `text`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `==` means equal.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 105 to 118:

```python
        return ChatResponse(
            text=text,
            stop_reason=_STOP.get(message.stop_reason or "", StopReason.OTHER),
            usage=Usage(message.usage.input_tokens, message.usage.output_tokens),
            latency_seconds=round(elapsed, 4),
            model=message.model,
            tool_calls=calls,
        )

    def count_tokens(self, request: ChatRequest) -> int:
        """Ask the provider how many input tokens a request would use (no generation, no charge)."""
        payload = self.build_payload(request)
        for unused in ("max_tokens", "thinking", "output_config"):
            payload.pop(unused, None)
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `count_tokens`. It returns a whole number. The author's own description: "Ask the provider how many input tokens a request would use (no generation, no charge)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Loop: the indented lines below run once for each item of `('max_tokens', 'thinking', 'output_config')`; `unused` names the current item.
- Calls `.pop(...)` removes and returns an item with 2 argument(s); the result is not kept.
  - `.pop(...)` removes and returns an item.

`src/scheduling_agent/infrastructure/anthropic_chat.py`, lines 119 to 119:

```python
        return int(self._client.messages.count_tokens(**payload).input_tokens)
```

- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `**name` inside a call passes every entry of a dictionary as a named argument.

### `src/scheduling_agent/infrastructure/calendar_client.py`

In its own words: "The calendar service as seen from the agent: an HTTP client with timeouts, retries and an Idempotency-Key header."

115 non-blank lines; it defines `_event`, `HttpCalendar`.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 1 to 13:

```python
"""The calendar service as seen from the agent: an HTTP client with timeouts, retries and an Idempotency-Key header."""

from __future__ import annotations

import time as time_module
from collections.abc import Callable, Sequence
from datetime import date, datetime, time
from typing import Any

import httpx

from scheduling_agent.domain.approvals import BookingResult
from scheduling_agent.domain.calendar import Event
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `time` (standard library) available under the name `time_module`.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime`, `time` from the standard library module `datetime`.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Brings in `BookingResult` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.) from the project module `scheduling_agent.domain.approvals`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 14 to 24:

```python
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
```

- Brings in `AlreadyCancelled` (The event is already cancelled.), `CalendarError` (The calendar refused or could not do what was asked.), `CalendarUnavailable` (The calendar service did not answer (timeout, connection refused, 5xx).), `IdempotencyConflict` (An Idempotency-Key was reused for a different request.), `InvalidSlot` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.), `SlotUnavailable` (A person is already busy at that time.), `UnknownEvent` (No event with that id.), `UnknownPerson` (A name that is not one of the calendar's people.) from the project module `scheduling_agent.domain.errors`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `scheduling_agent.infrastructure.retry`.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 26 to 36:

```python
_ERRORS: dict[str, type[CalendarError]] = {
    "UnknownEvent": UnknownEvent,
    "UnknownPerson": UnknownPerson,
    "InvalidSlot": InvalidSlot,
    "SlotUnavailable": SlotUnavailable,
    "AlreadyCancelled": AlreadyCancelled,
    "IdempotencyConflict": IdempotencyConflict,
}


def _event(data: dict[str, Any]) -> Event:
```

- Declares `_ERRORS` as a dictionary from text to type of the project type `CalendarError` and sets it to a dictionary with 6 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `_event`. It returns the project type `Event`.
- Its parameters:
    - `data` holds a dictionary from text to any value.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 37 to 43:

```python
    return Event(
        data["id"], tuple(data["people"]), datetime.fromisoformat(data["start"]), data["minutes"], data["cancelled"]
    )


class HttpCalendar:
    """Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key."""
```

- Ends the function and gives back the result of calling `Event` to the caller.
  - `Event` from the project's `scheduling_agent.domain.calendar` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `datetime.fromisoformat` reads a date and time from ISO text.
- Defines the class `HttpCalendar`. The author's own description: "Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 45 to 57:

```python
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
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `attempts` holds a whole number; if the caller leaves it out it is the number `3`.
    - `base_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `0.2`.
    - `sleep` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `base_url.rstrip` under the name `self._base` (as an attribute of this object, so other methods can use it).
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `attempts` under the name `self._attempts` (as an attribute of this object, so other methods can use it).
- Stores the value named `base_delay_seconds` under the name `self._delay` (as an attribute of this object, so other methods can use it).
- Stores the value named `sleep` under the name `self._sleep` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 59 to 67:

```python
    def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        def once() -> dict[str, Any] | list[Any]:
            try:
                reply = self._http.request(method, f"{self._base}{path}", **kwargs)
            except httpx.TransportError as error:
                raise CalendarUnavailable(f"{type(error).__name__}: {error}") from error
            if reply.status_code >= 500:
                raise CalendarUnavailable(f"HTTP {reply.status_code}")
            if reply.status_code >= 400:
```

- Defines the method `_call`. It returns a dictionary from text to any value, or a list of any value.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `method` holds text.
    - `path` holds text.
    - `**kwargs` collects any extra named arguments into a dictionary.
- Defines the function `once`. It returns a dictionary from text to any value, or a list of any value.
- It takes no parameters.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.request` under the name `reply`.
  - The method `request` of `self._http`.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `CalendarUnavailable`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `CalendarUnavailable` from the project's `scheduling_agent.domain.errors` (The calendar service did not answer (timeout, connection refused, 5xx).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Decision: the indented lines below run only when `reply.status_code >= 500` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `CalendarUnavailable`. Execution jumps out to the nearest matching `except`.
  - `CalendarUnavailable` from the project's `scheduling_agent.domain.errors` (The calendar service did not answer (timeout, connection refused, 5xx).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 68 to 77:

```python
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
```

- Stores one of two values, chosen by a condition under the name `detail`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.startswith(...)` asks whether text begins with the given text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Decision: the indented lines below run only when `isinstance(detail, dict) and detail.get('error') in _ERRORS` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `isinstance` asks whether a value is of a given type.
  - `in` means is contained in.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `_ERRORS[detail['error']]`. Execution jumps out to the nearest matching `except`.
  - The result of `_ERRORS[detail['error']]`, called.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `CalendarError`. Execution jumps out to the nearest matching `except`.
  - `CalendarError` from the project's `scheduling_agent.domain.errors` (The calendar refused or could not do what was asked.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Declares `body` as a dictionary from text to any value, or a list of any value and sets it to the result of calling `reply.json`.
  - `|` is or; in a type, "either".
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the value named `body` to the caller.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 79 to 85:

```python
        return retry(
            once,
            attempts=self._attempts,
            base_delay_seconds=self._delay,
            retry_on=(CalendarUnavailable,),
            sleep=self._sleep or time_module.sleep,
        )
```

- Ends the function and gives back the result of calling `retry` to the caller.
  - `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 87 to 95:

```python
    def free_slots(
        self,
        people: Sequence[str],
        first_day: date,
        last_day: date,
        minutes: int,
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> list[datetime]:
```

- Defines the method `free_slots`. It returns a list of a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `first_day` holds a calendar date.
    - `last_day` holds a calendar date.
    - `minutes` holds a whole number.
    - `not_before` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `not_after` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 96 to 108:

```python
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
```

- Declares `params` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `list` makes a list (a copy when given a collection).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Decision: the indented lines below run only when `not_before` is true.
- Stores the result of calling `not_before.isoformat` under the name `params['not_before']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Decision: the indented lines below run only when `not_after` is true.
- Stores the result of calling `not_after.isoformat` under the name `params['not_after']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Stores the result of calling `self._call` under the name `body`.
  - The method `_call` of this object.
- Checks that `isinstance(body, dict)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 110 to 122:

```python
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
```

- Defines the method `get_event`. It returns the project type `Event`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
- Stores the result of calling `self._call` under the name `body`.
  - The method `_call` of this object.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `isinstance(body, dict)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back the result of calling `_event` to the caller.
  - `_event`, a function defined in this file or passed in.
- Defines the method `book`. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `start` holds a date and time.
    - `minutes` holds a whole number.
    - `idempotency_key` holds text.
- Stores a dictionary with 3 entries under the name `payload`.
  - `list` makes a list (a copy when given a collection).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Stores the result of calling `self._call` under the name `body`.
  - The method `_call` of this object.
- Checks that `isinstance(body, dict)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back the result of calling `BookingResult` to the caller.
  - `BookingResult` from the project's `scheduling_agent.domain.approvals` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.).
  - `_event`, a function defined in this file or passed in.
  - `bool` turns a value into true or false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `cancel`. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
    - `idempotency_key` holds text.
- Stores the result of calling `self._call` under the name `body`.
  - The method `_call` of this object.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/infrastructure/calendar_client.py`, lines 123 to 133:

```python
        assert isinstance(body, dict)
        return BookingResult(_event(body["event"]), bool(body["replayed"]))

    def active_events(self) -> list[Event]:
        body = self._call("GET", "/events")
        assert isinstance(body, list)
        return [_event(item) for item in body]

    def reset(self) -> None:
        """Reseed the calendar (needs the service started with resets enabled; a demo and test aid)."""
        self._call("POST", "/admin/reset")
```

- Checks that `isinstance(body, dict)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back the result of calling `BookingResult` to the caller.
  - `BookingResult` from the project's `scheduling_agent.domain.approvals` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.).
  - `_event`, a function defined in this file or passed in.
  - `bool` turns a value into true or false.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `active_events`. It returns a list of the project type `Event`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the result of calling `self._call` under the name `body`.
  - The method `_call` of this object.
- Checks that `isinstance(body, list)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `_event`, a function defined in this file or passed in.
- Defines the method `reset`. It returns nothing (None). The author's own description: "Reseed the calendar (needs the service started with resets enabled; a demo and test aid)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Calls the method `_call` of this object with 2 argument(s); the result is not kept.
  - The method `_call` of this object.

### `src/scheduling_agent/infrastructure/calendar_db.py`

In its own words: "The calendar service's storage: events, attendees and idempotency keys in SQLite."

146 non-blank lines; it defines `_event`, `_request_hash`, `_locked`, `SqliteCalendar`.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 1 to 14:

```python
"""The calendar service's storage: events, attendees and idempotency keys in SQLite."""

from __future__ import annotations

import functools
import hashlib
import json
import sqlite3
import threading
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta
from typing import Concatenate

from scheduling_agent.domain.approvals import BookingResult
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `functools` (standard library) available.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `sqlite3` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime`, `time`, `timedelta` from the standard library module `datetime`.
- Brings in `Concatenate` from the standard library module `typing`.
- Brings in `BookingResult` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.) from the project module `scheduling_agent.domain.approvals`.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 15 to 28:

```python
from scheduling_agent.domain.calendar import Event, Interval, free_slots, overlaps, validate_slot
from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    IdempotencyConflict,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.sqlite import transaction


def _event(connection: sqlite3.Connection, event_id: str) -> Event | None:
    row = connection.execute("SELECT id, start, minutes, cancelled FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
```

- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.), `Interval`, `free_slots` (Start times, earliest first, at which every listed person is free for `minutes`.), `overlaps` (True when two half-open intervals share any time.), `validate_slot` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `AlreadyCancelled` (The event is already cancelled.), `IdempotencyConflict` (An Idempotency-Key was reused for a different request.), `SlotUnavailable` (A person is already busy at that time.), `UnknownEvent` (No event with that id.), `UnknownPerson` (A name that is not one of the calendar's people.) from the project module `scheduling_agent.domain.errors`.
- Brings in `transaction` (Run a block as one write transaction: commit on success, roll back on any error.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Defines the function `_event`. It returns the project type `Event`, or nothing (None).
- Its parameters:
    - `connection` holds `sqlite3.Connection`.
    - `event_id` holds text.
- Stores the result of calling `connection.execute('SELECT id, start, minutes, ...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `.execute(...)` runs one SQL statement.
- Decision: the indented lines below run only when `row is None` is true.
  - `is` means the very same object.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 29 to 42:

```python
        return None
    people = [
        r[0]
        for r in connection.execute("SELECT person FROM event_people WHERE event_id = ? ORDER BY person", (event_id,))
    ]
    return Event(row["id"], tuple(people), datetime.fromisoformat(row["start"]), row["minutes"], bool(row["cancelled"]))


def _request_hash(operation: str, payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps({"op": operation, **payload}, sort_keys=True).encode()).hexdigest()


def _locked[**P, R](method: Callable[Concatenate[SqliteCalendar, P], R]) -> Callable[Concatenate[SqliteCalendar, P], R]:
    """Run a method while holding the calendar's lock."""
```

- Ends the function and gives back nothing (`None`) to the caller.
- Stores a list built by looping under the name `people`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.execute(...)` runs one SQL statement.
- Ends the function and gives back the result of calling `Event` to the caller.
  - `Event` from the project's `scheduling_agent.domain.calendar` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `bool` turns a value into true or false.
- Defines the function `_request_hash`. It returns text.
- Its parameters:
    - `operation` holds text.
    - `payload` holds a dictionary from text to any object.
- Ends the function and gives back the result of calling `hashlib.sha256(json.dumps({'op': operation, **p...` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
  - `json.dumps` turns Python data into JSON text.
- Defines the function `_locked`. It returns a function. The author's own description: "Run a method while holding the calendar's lock."
- Its parameters:
    - `method` holds a function.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 44 to 56:

```python
    @functools.wraps(method)
    def wrapper(self: SqliteCalendar, *args: P.args, **kwargs: P.kwargs) -> R:
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


class SqliteCalendar:
    """Reads and idempotent writes. Every write and its idempotency key are committed in one transaction."""

    def __init__(self, connection: sqlite3.Connection, now: str = "2026-10-27T00:00") -> None:
        self._db = connection
```

- Defines the function `wrapper`. `@functools.wraps` copies the original function's name and docstring onto the replacement. It returns `R`.
- Its parameters:
    - `self` holds the project type `SqliteCalendar`.
    - `*args` collects any extra positional arguments into a tuple.
    - `**kwargs` collects any extra named arguments into a dictionary.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Ends the function and gives back the result of calling `method` to the caller.
  - `method`, a function defined in this file or passed in.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
  - `*name` inside a call passes every item of a collection as a separate argument.
- Ends the function and gives back the value named `wrapper` to the caller.
- Defines the class `SqliteCalendar`. The author's own description: "Reads and idempotent writes. Every write and its idempotency key are committed in one transaction."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `connection` holds `sqlite3.Connection`.
    - `now` holds text; if the caller leaves it out it is the text `2026-10-27T00:00`.
- Stores the value named `connection` under the name `self._db` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 57 to 69:

```python
        self._now = now
        self._lock = threading.RLock()  # one connection, many request threads: calls take turns

    @_locked
    def people(self) -> list[str]:
        return [r[0] for r in self._db.execute("SELECT name FROM people ORDER BY name")]

    @_locked
    def get_event(self, event_id: str) -> Event:
        event = _event(self._db, event_id)
        if event is None:
            raise UnknownEvent(f"no event {event_id}")
        return event
```

- Stores the value named `now` under the name `self._now` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.RLock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.RLock` makes a lock the same thread may take again.
- Defines the method `people`. The decorator `@_locked` wraps or registers the definition below it. It returns a list of text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Defines the method `get_event`. The decorator `@_locked` wraps or registers the definition below it. It returns the project type `Event`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
- Stores the result of calling `_event` under the name `event`.
  - `_event`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `event is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `UnknownEvent`. Execution jumps out to the nearest matching `except`.
  - `UnknownEvent` from the project's `scheduling_agent.domain.errors` (No event with that id.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `event` to the caller.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 71 to 83:

```python
    @_locked
    def active_events(self) -> list[Event]:
        ids = [r[0] for r in self._db.execute("SELECT id FROM events WHERE cancelled = 0 ORDER BY start, id")]
        return [e for i in ids if (e := _event(self._db, i)) is not None]

    @_locked
    def busy(self, people: Sequence[str]) -> dict[str, list[Interval]]:
        known = set(self.people())
        for person in people:
            if person not in known:
                raise UnknownPerson(f"{person} is not on this calendar")
        out: dict[str, list[Interval]] = {p: [] for p in people}
        marks = ",".join("?" for _ in people)
```

- Defines the method `active_events`. The decorator `@_locked` wraps or registers the definition below it. It returns a list of the project type `Event`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores a list built by looping under the name `ids`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is not` means not the same object.
  - `name := value` stores the value under `name` and also gives it as the result of the expression.
  - `_event`, a function defined in this file or passed in.
- Defines the method `busy`. The decorator `@_locked` wraps or registers the definition below it. It returns a dictionary from text to a list of `Interval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
- Stores the result of calling `set` under the name `known`.
  - `set` makes a set: a collection with no repeated items.
  - The method `people` of this object.
- Loop: the indented lines below run once for each item of `people`; `person` names the current item.
- Decision: the indented lines below run only when `person not in known` is true.
  - `not in` means is not contained in.
- Raises an error: the result of calling `UnknownPerson`. Execution jumps out to the nearest matching `except`.
  - `UnknownPerson` from the project's `scheduling_agent.domain.errors` (A name that is not one of the calendar's people.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Declares `out` as a dictionary from text to a list of `Interval` and sets it to a dictionary built by looping.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `','.join` under the name `marks`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 84 to 92:

```python
        rows = self._db.execute(
            "SELECT ep.person, e.start, e.minutes FROM events e JOIN event_people ep ON ep.event_id = e.id "
            f"WHERE e.cancelled = 0 AND ep.person IN ({marks})",
            list(people),
        )
        for row in rows:
            start = datetime.fromisoformat(row["start"])
            out[row["person"]].append((start, start + timedelta(minutes=row["minutes"])))
        return out
```

- Stores the result of calling `self._db.execute` under the name `rows`.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `list` makes a list (a copy when given a collection).
- Loop: the indented lines below run once for each item of `rows`; `row` names the current item.
- Stores the result of calling `datetime.fromisoformat` under the name `start`.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Ends the function and gives back the value named `out` to the caller.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 94 to 104:

```python
    @_locked
    def free_slots(
        self,
        people: Sequence[str],
        first_day: date,
        last_day: date,
        minutes: int,
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> list[datetime]:
        return free_slots(self.busy(people), people, first_day, last_day, minutes, not_before, not_after)
```

- Defines the method `free_slots`. The decorator `@_locked` wraps or registers the definition below it. It returns a list of a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `first_day` holds a calendar date.
    - `last_day` holds a calendar date.
    - `minutes` holds a whole number.
    - `not_before` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `not_after` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Ends the function and gives back the result of calling `free_slots` to the caller.
  - `free_slots` from the project's `scheduling_agent.domain.calendar` (Start times, earliest first, at which every listed person is free for `minutes`.).
  - The method `busy` of this object.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 106 to 118:

```python
    @_locked
    def book(self, people: Sequence[str], start: datetime, minutes: int, idempotency_key: str) -> BookingResult:
        names = sorted(set(people))
        digest = _request_hash(
            "book", {"people": names, "start": start.isoformat(timespec="minutes"), "minutes": minutes}
        )
        with transaction(self._db):
            replay = self._replay(idempotency_key, "book", digest)
            if replay:
                return replay
            validate_slot(start, minutes)
            if not names:
                raise UnknownPerson("a meeting needs at least one person")
```

- Defines the method `book`. The decorator `@_locked` wraps or registers the definition below it. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `start` holds a date and time.
    - `minutes` holds a whole number.
    - `idempotency_key` holds text.
- Stores the result of calling `sorted` under the name `names`.
  - `sorted` returns a new list with the items in order.
  - `set` makes a set: a collection with no repeated items.
- Stores the result of calling `_request_hash` under the name `digest`.
  - `_request_hash`, a function defined in this file or passed in.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- A `with` block: it sets up `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).
- Stores the result of calling `self._replay` under the name `replay`.
  - The method `_replay` of this object.
- Decision: the indented lines below run only when `replay` is true.
- Ends the function and gives back the value named `replay` to the caller.
- Calls `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) with 2 argument(s); the result is not kept.
  - `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.).
- Decision: the indented lines below run only when `not names` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `UnknownPerson`. Execution jumps out to the nearest matching `except`.
  - `UnknownPerson` from the project's `scheduling_agent.domain.errors` (A name that is not one of the calendar's people.).

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 119 to 131:

```python
            busy = self.busy(names)
            end = start + timedelta(minutes=minutes)
            for person in names:
                if any(overlaps(start, end, b0, b1) for b0, b1 in busy[person]):
                    raise SlotUnavailable(f"{person} is busy at {start:%Y-%m-%d %H:%M}")
            number = self._db.execute(
                "SELECT COALESCE(MAX(CAST(substr(id, 4) AS INTEGER)), 0) + 1 FROM events"
            ).fetchone()[0]
            event_id = f"ev-{number:04d}"
            self._db.execute(
                "INSERT INTO events (id, start, minutes, cancelled, created_at) VALUES (?, ?, ?, 0, ?)",
                (event_id, start.isoformat(timespec="minutes"), minutes, self._now),
            )
```

- Stores the result of calling `self.busy` under the name `busy`.
  - The method `busy` of this object.
- Stores the result of `start + timedelta(minutes=minutes)` under the name `end`.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Loop: the indented lines below run once for each item of `names`; `person` names the current item.
- Decision: the indented lines below run only when `any((overlaps(start, end, b0, b1) for b0, b1 in busy[person]))` is true.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `overlaps` from the project's `scheduling_agent.domain.calendar` (True when two half-open intervals share any time.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `SlotUnavailable`. Execution jumps out to the nearest matching `except`.
  - `SlotUnavailable` from the project's `scheduling_agent.domain.errors` (A person is already busy at that time.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the part of `self._db.execute('SELECT CO...` picked by `0` under the name `number`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Stores a text built from pieces (an f-string) under the name `event_id`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 132 to 145:

```python
            self._db.executemany(
                "INSERT INTO event_people (event_id, person) VALUES (?, ?)", [(event_id, p) for p in names]
            )
            self._db.execute(
                "INSERT INTO idempotency_keys (key, operation, request_hash, event_id, created_at) "
                "VALUES (?, 'book', ?, ?, ?)",
                (idempotency_key, digest, event_id, self._now),
            )
            return BookingResult(self.get_event(event_id), replayed=False)

    @_locked
    def cancel(self, event_id: str, idempotency_key: str) -> BookingResult:
        digest = _request_hash("cancel", {"event_id": event_id})
        with transaction(self._db):
```

- Calls `executemany` on the stored object `self._db`: it runs one SQL statement for a list of parameter sets with 2 argument(s); the result is not kept.
  - `executemany` on the stored object `self._db`: it runs one SQL statement for a list of parameter sets.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back the result of calling `BookingResult` to the caller.
  - `BookingResult` from the project's `scheduling_agent.domain.approvals` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.).
  - The method `get_event` of this object.
- Defines the method `cancel`. The decorator `@_locked` wraps or registers the definition below it. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
    - `idempotency_key` holds text.
- Stores the result of calling `_request_hash` under the name `digest`.
  - `_request_hash`, a function defined in this file or passed in.
- A `with` block: it sets up `transaction(self._db)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `transaction` from the project's `scheduling_agent.infrastructure.sqlite` (Run a block as one write transaction: commit on success, roll back on any error.).

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 146 to 158:

```python
            replay = self._replay(idempotency_key, "cancel", digest)
            if replay:
                return replay
            event = self.get_event(event_id)
            if event.cancelled:
                raise AlreadyCancelled(f"{event_id} is already cancelled")
            self._db.execute("UPDATE events SET cancelled = 1 WHERE id = ?", (event_id,))
            self._db.execute(
                "INSERT INTO idempotency_keys (key, operation, request_hash, event_id, created_at) "
                "VALUES (?, 'cancel', ?, ?, ?)",
                (idempotency_key, digest, event_id, self._now),
            )
            return BookingResult(self.get_event(event_id), replayed=False)
```

- Stores the result of calling `self._replay` under the name `replay`.
  - The method `_replay` of this object.
- Decision: the indented lines below run only when `replay` is true.
- Ends the function and gives back the value named `replay` to the caller.
- Stores the result of calling `self.get_event` under the name `event`.
  - The method `get_event` of this object.
- Decision: the indented lines below run only when `event.cancelled` is true.
- Raises an error: the result of calling `AlreadyCancelled`. Execution jumps out to the nearest matching `except`.
  - `AlreadyCancelled` from the project's `scheduling_agent.domain.errors` (The event is already cancelled.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Calls `execute` on the stored object `self._db`: it runs one SQL statement with 2 argument(s); the result is not kept.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Ends the function and gives back the result of calling `BookingResult` to the caller.
  - `BookingResult` from the project's `scheduling_agent.domain.approvals` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.).
  - The method `get_event` of this object.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 160 to 168:

```python
    def _replay(self, key: str, operation: str, digest: str) -> BookingResult | None:
        row = self._db.execute(
            "SELECT operation, request_hash, event_id FROM idempotency_keys WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        if row["operation"] != operation or row["request_hash"] != digest:
            raise IdempotencyConflict("this Idempotency-Key was used for a different request")
        return BookingResult(self.get_event(row["event_id"]), replayed=True)
```

- Defines the method `_replay`. It returns the project type `BookingResult`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `operation` holds text.
    - `digest` holds text.
- Stores the result of calling `self._db.execute('SELECT operation, request_has...` under the name `row`.
  - `.fetchone(...)` reads one row of a query result.
  - `execute` on the stored object `self._db`: it runs one SQL statement.
- Decision: the indented lines below run only when `row is None` is true.
  - `is` means the very same object.
- Ends the function and gives back nothing (`None`) to the caller.
- Decision: the indented lines below run only when `row['operation'] != operation or row['request_hash'] != digest` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `!=` means not equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `IdempotencyConflict`. Execution jumps out to the nearest matching `except`.
  - `IdempotencyConflict` from the project's `scheduling_agent.domain.errors` (An Idempotency-Key was reused for a different request.).
- Ends the function and gives back the result of calling `BookingResult` to the caller.
  - `BookingResult` from the project's `scheduling_agent.domain.approvals` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.).
  - The method `get_event` of this object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `src/scheduling_agent/infrastructure/calendar_seed.py`

In its own words: "Create and reset the calendar database from the numbered SQL files under sql/calendar."

17 non-blank lines; it defines `init_calendar`, `reset_calendar`.

`src/scheduling_agent/infrastructure/calendar_seed.py`, lines 1 to 14:

```python
"""Create and reset the calendar database from the numbered SQL files under sql/calendar."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scheduling_agent.infrastructure.sqlite import apply_sql


def init_calendar(connection: sqlite3.Connection, sql_dir: Path) -> None:
    """Create the tables and load the seed if the database has no people yet."""
    apply_sql(connection, sql_dir / "calendar" / "001_schema.sql")
    if connection.execute("SELECT count(*) FROM people").fetchone()[0] == 0:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `sqlite3` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `apply_sql` (Run SQL script files in the order given (the numbered files under sql/).) from the project module `scheduling_agent.infrastructure.sqlite`.
- Defines the function `init_calendar`. It returns nothing (None). The author's own description: "Create the tables and load the seed if the database has no people yet."
- Its parameters:
    - `connection` holds `sqlite3.Connection`.
    - `sql_dir` holds a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Decision: the indented lines below run only when `connection.execute('SELECT count(*) FROM people').fetchone()[0] == 0` is true.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.fetchone(...)` reads one row of a query result.
  - `.execute(...)` runs one SQL statement.

`src/scheduling_agent/infrastructure/calendar_seed.py`, lines 15 to 24:

```python
        apply_sql(connection, sql_dir / "calendar" / "002_seed.sql")


def reset_calendar(connection: sqlite3.Connection, sql_dir: Path) -> None:
    """Delete every row and load the seed again (the demo and test aid behind POST /admin/reset)."""
    connection.execute("PRAGMA foreign_keys = OFF")
    for table in ("idempotency_keys", "event_people", "events", "people"):
        connection.execute(f"DELETE FROM {table}")
    connection.execute("PRAGMA foreign_keys = ON")
    apply_sql(connection, sql_dir / "calendar" / "002_seed.sql")
```

- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Defines the function `reset_calendar`. It returns nothing (None). The author's own description: "Delete every row and load the seed again (the demo and test aid behind POST /admin/reset)."
- Its parameters:
    - `connection` holds `sqlite3.Connection`.
    - `sql_dir` holds a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Loop: the indented lines below run once for each item of `('idempotency_keys', 'event_people', 'events', 'people')`; `table` names the current item.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.

### `src/scheduling_agent/infrastructure/clock.py`

In its own words: "The real clock, behind the `Clock` port."

12 non-blank lines; it defines `SystemClock`.

`src/scheduling_agent/infrastructure/clock.py`, lines 1 to 13:

```python
"""The real clock, behind the `Clock` port."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime


class SystemClock:
    """Wall-clock and monotonic time from the operating system."""

    def monotonic(self) -> float:
        return time.monotonic()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `time` (standard library) available.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Defines the class `SystemClock`. The author's own description: "Wall-clock and monotonic time from the operating system."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `time.monotonic` to the caller.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.

`src/scheduling_agent/infrastructure/clock.py`, lines 15 to 19:

```python
    def today(self) -> date:
        return datetime.now(UTC).date()

    def now(self) -> datetime:
        return datetime.now(UTC)
```

- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now(UTC).date` to the caller.
  - The method `date` of `datetime.now(UTC)`.
  - `datetime.now` the current date and time.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now` to the caller.
  - `datetime.now` the current date and time.

### `src/scheduling_agent/infrastructure/embeddings.py`

In its own words: "Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording."

105 non-blank lines; it defines `text_key`, `_pack`, `_unpack`, `OpenAICompatibleEmbedder`, `EmbeddingStore`, `RecordedEmbedder`, `RecordingEmbedder`.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 1 to 13:

```python
"""Embedding adapters: an OpenAI-compatible server, a recording of its answers, and the replay of that recording."""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import threading
from collections.abc import Sequence
from pathlib import Path

import httpx
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `base64` (standard library) available.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `struct` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `httpx` (installed package) available.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 15 to 25:

```python
from scheduling_agent.application.ports import Embedder
from scheduling_agent.domain.errors import PermanentModelError, RecordingMissing, TransientModelError


def text_key(text: str) -> str:
    """The recording key of a text: its SHA-256. The model name is not part of it."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pack(vector: Sequence[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")
```

- Brings in `Embedder` (Turns texts into vectors.) from the project module `scheduling_agent.application.ports`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `scheduling_agent.domain.errors`.
- Defines the function `text_key`. It returns text. The author's own description: "The recording key of a text: its SHA-256. The model name is not part of it."
- Its parameters:
    - `text` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `hashlib.sha256(text.encode('utf-8')).hexdigest` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Defines the function `_pack`. It returns text.
- Its parameters:
    - `vector` holds anything that behaves like a list of a decimal number.
- Ends the function and gives back the result of calling `base64.b64encode(struct.pack(f'<{len(vector)}f'...` to the caller.
  - `.decode(...)` turns bytes into text.
  - `base64.b64encode` turns bytes into base64 text.
  - `struct.pack` packs numbers into bytes.
  - `*name` inside a call passes every item of a collection as a separate argument.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).

`src/scheduling_agent/infrastructure/embeddings.py`, lines 28 to 39:

```python
def _unpack(blob: str) -> list[float]:
    raw = base64.b64decode(blob)
    return list(struct.unpack(f"<{len(raw) // 4}f", raw))


class OpenAICompatibleEmbedder:
    """Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, api_key: str | None = None) -> None:
        self._http = http
        self._url = f"{base_url.rstrip('/')}/embeddings"
        self._model = model
```

- Defines the function `_unpack`. It returns a list of a decimal number.
- Its parameters:
    - `blob` holds text.
- Stores the result of calling `base64.b64decode` under the name `raw`.
  - `base64.b64decode` turns base64 text into bytes.
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
  - `struct.unpack` unpacks bytes into numbers.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `//` is divide and drop the fraction.
  - `len` counts the items in a collection (or the characters in text).
- Defines the class `OpenAICompatibleEmbedder`. The author's own description: "Calls `POST {base_url}/embeddings`, which ollama and OpenAI-compatible servers provide."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `model` holds text.
    - `api_key` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores a text built from pieces (an f-string) under the name `self._url` (as an attribute of this object, so other methods can use it).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/embeddings.py`, lines 40 to 53:

```python
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            reply = self._http.post(self._url, json={"model": self._model, "input": list(texts)}, headers=self._headers)
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
```

- Stores one of two values, chosen by a condition under the name `self._headers` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.post` under the name `reply`.
  - `post` on the stored object `self._http`: it sends an HTTP POST request.
  - `list` makes a list (a copy when given a collection).
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Decision: the indented lines below run only when `reply.status_code == 429 or reply.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 54 to 66:

```python
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
        try:
            data = sorted(reply.json()["data"], key=lambda item: item["index"])
            vectors = [[float(x) for x in item["embedding"]] for item in data]
        except (KeyError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected embeddings response: {error!r}") from error
        if len(vectors) != len(texts):
            raise PermanentModelError(f"asked for {len(texts)} embeddings, got {len(vectors)}")
        return vectors


class EmbeddingStore:
    """A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded."""
```

- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `sorted` under the name `data`.
  - `sorted` returns a new list with the items in order.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `lambda args: expression` is a small unnamed function written inline.
- Stores a list built by looping under the name `vectors`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `float` turns a value into a decimal number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, TypeError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `len(vectors) != len(texts)` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the value named `vectors` to the caller.
- Defines the class `EmbeddingStore`. The author's own description: "A JSON Lines file of vectors by text key (float32, base64), appended to as texts are embedded."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 68 to 79:

```python
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._vectors: dict[str, list[float]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._vectors[entry["key"]] = _unpack(entry["vector"])
        self._append_to = path / "embeddings.jsonl" if path.is_dir() else path
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.Lock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.Lock` makes a lock.
- Declares `self._vectors` as a dictionary from text to a list of a decimal number and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `files`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `.exists(...)` asks whether the path exists.
- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- A `with` block: it sets up `file.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `file`.
- Loop: the indented lines below run once for each item of `handle`; `line` names the current item.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `_unpack` under the name `self._vectors[entry['key']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_unpack`, a function defined in this file or passed in.
- Stores one of two values, chosen by a condition under the name `self._append_to` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `/` is divide.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 81 to 93:

```python
    def __len__(self) -> int:
        return len(self._vectors)

    def get(self, key: str) -> list[float] | None:
        return self._vectors.get(key)

    def put(self, key: str, vector: Sequence[float], model: str) -> None:
        with self._lock:
            self._vectors[key] = list(vector)
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "model": model, "vector": _pack(vector)}) + "\n")
                handle.flush()
```

- Defines the method `__len__`. It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `get`. It returns a list of a decimal number, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
- Ends the function and gives back the result of calling `self._vectors.get` to the caller.
  - `get` on the stored object `self._vectors`: it reads a dictionary entry, giving a default when the key is missing.
- Defines the method `put`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `vector` holds anything that behaves like a list of a decimal number.
    - `model` holds text.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `list` under the name `self._vectors[key]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `list` makes a list (a copy when given a collection).
- Calls `mkdir` on the stored object `self._append_to.parent`: it creates a folder with 2 argument(s); the result is not kept.
  - `mkdir` on the stored object `self._append_to.parent`: it creates a folder.
- A `with` block: it sets up `self._append_to.open('a', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._append_to`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
  - `_pack`, a function defined in this file or passed in.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 96 to 107:

```python
class RecordedEmbedder:
    """Replays recorded vectors. A text nobody embedded raises `RecordingMissing`."""

    def __init__(self, store: EmbeddingStore, name: str = "recorded") -> None:
        self._store = store
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
```

- Defines the class `RecordedEmbedder`. The author's own description: "Replays recorded vectors. A text nobody embedded raises `RecordingMissing`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `EmbeddingStore`.
    - `name` holds text; if the caller leaves it out it is the text `recorded`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Stores the value named `name` under the name `self._name` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_name` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 108 to 121:

```python
        out: list[list[float]] = []
        for text in texts:
            vector = self._store.get(text_key(text))
            if vector is None:
                raise RecordingMissing(
                    f"no recorded embedding for a text of {len(text)} characters starting {text[:40]!r}; "
                    "run `make record` against the embedding model to refresh the fixtures"
                )
            out.append(vector)
        return out


class RecordingEmbedder:
    """Wraps a live embedder and writes each new vector into the recording; known texts are replayed."""
```

- Declares `out` as a list of a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `texts`; `text` names the current item.
- Stores the result of calling `self._store.get` under the name `vector`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `vector is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `RecordingMissing`. Execution jumps out to the nearest matching `except`.
  - `RecordingMissing` from the project's `scheduling_agent.domain.errors` (The recorded adapter has no response for this request. Re-record with `make record`.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `RecordingEmbedder`. The author's own description: "Wraps a live embedder and writes each new vector into the recording; known texts are replayed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 123 to 135:

```python
    def __init__(self, inner: Embedder, store: EmbeddingStore) -> None:
        self._inner = inner
        self._store = store

    @property
    def name(self) -> str:
        return self._inner.name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        unknown = [t for t in dict.fromkeys(texts) if self._store.get(text_key(t)) is None]
        if unknown:
            for text, vector in zip(unknown, self._inner.embed(unknown), strict=True):
                self._store.put(text_key(text), vector, self._inner.name)
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `Embedder`.
    - `store` holds the project type `EmbeddingStore`.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `embed`. It returns a list of a list of a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- Stores a list built by looping under the name `unknown`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `fromkeys` of `dict`.
  - `is` means the very same object.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `unknown` is true.
- Loop: the indented lines below run once for each item of `zip(unknown, self._inner.embed(unknown), strict=True)`; `(text, vector)` names the current item.
  - `zip` walks several collections side by side, item by item.
  - The method `embed` of `self._inner`.
- Calls `put` on the stored object `self._store`: it sends an HTTP PUT request with 3 argument(s); the result is not kept.
  - `put` on the stored object `self._store`: it sends an HTTP PUT request.
  - `text_key`, a function defined in this file or passed in.

`src/scheduling_agent/infrastructure/embeddings.py`, lines 136 to 136:

```python
        return [self._store.get(text_key(t)) or [] for t in texts]
```

- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - `text_key`, a function defined in this file or passed in.

### `src/scheduling_agent/infrastructure/env.py`

In its own words: "Helpers that read and validate environment variables (twelve-factor configuration)."

53 non-blank lines; it defines `ConfigurationError`, `text`, `optional_text`, `positive_int`, `non_negative_int`, `positive_float`, `non_negative_float`, `choice`.

`src/scheduling_agent/infrastructure/env.py`, lines 1 to 14:

```python
"""Helpers that read and validate environment variables (twelve-factor configuration)."""

from __future__ import annotations

from collections.abc import Collection, Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def text(environ: Mapping[str, str], name: str, default: str) -> str:
    """A non-empty string, or `default` when the variable is unset."""
    value = environ.get(name, default).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Collection`, `Mapping` from the standard library module `collections.abc`.
- Defines the class `ConfigurationError`. It builds on `ValueError`. The author's own description: "An environment variable is missing or has an unusable value."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the function `text`. It returns text. The author's own description: "A non-empty string, or `default` when the variable is unset."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, default).strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/scheduling_agent/infrastructure/env.py`, lines 15 to 28:

```python
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value


def optional_text(environ: Mapping[str, str], name: str) -> str | None:
    """The variable's text, or None when it is unset or blank."""
    value = environ.get(name, "").strip()
    return value or None


def positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 1 or more."""
    raw = environ.get(name, str(default)).strip()
```

- Decision: the indented lines below run only when `not value` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `optional_text`. It returns text, or nothing (None). The author's own description: "The variable's text, or None when it is unset or blank."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, '').strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of combining conditions: `value or None` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the function `positive_int`. It returns a whole number. The author's own description: "An integer of 1 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/scheduling_agent/infrastructure/env.py`, lines 29 to 42:

```python
    if not raw.isdigit() or int(raw) < 1:
        raise ConfigurationError(f"{name} must be a positive integer, got {raw!r}")
    return int(raw)


def non_negative_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 0 or more."""
    raw = environ.get(name, str(default)).strip()
    if not raw.isdigit():
        raise ConfigurationError(f"{name} must be a non-negative integer, got {raw!r}")
    return int(raw)


def positive_float(environ: Mapping[str, str], name: str, default: float) -> float:
```

- Decision: the indented lines below run only when `not raw.isdigit() or int(raw) < 1` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `<` means less than.
  - `.isdigit(...)` asks whether text is only digits.
  - `int` turns a value into a whole number.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `non_negative_int`. It returns a whole number. The author's own description: "An integer of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- Decision: the indented lines below run only when `not raw.isdigit()` is true.
  - `not` flips true and false.
  - `.isdigit(...)` asks whether text is only digits.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `positive_float`. It returns a decimal number. The author's own description: "A number greater than zero."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.

`src/scheduling_agent/infrastructure/env.py`, lines 43 to 56:

```python
    """A number greater than zero."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero, got {raw!r}")
    return value


def non_negative_float(environ: Mapping[str, str], name: str, default: float) -> float:
    """A number of 0 or more."""
    raw = environ.get(name, str(default)).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value <= 0` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `non_negative_float`. It returns a decimal number. The author's own description: "A number of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/scheduling_agent/infrastructure/env.py`, lines 57 to 70:

```python
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value < 0:
        raise ConfigurationError(f"{name} must not be negative, got {raw!r}")
    return value


def choice(environ: Mapping[str, str], name: str, default: str, allowed: Collection[str]) -> str:
    """One of the `allowed` strings."""
    value = text(environ, name, default)
    if value not in allowed:
        raise ConfigurationError(f"{name} must be one of {sorted(allowed)}, got {value!r}")
```

- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value < 0` is true.
  - `<` means less than.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `choice`. It returns text. The author's own description: "One of the `allowed` strings."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
    - `allowed` holds a collection with a size of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `text` under the name `value`.
  - `text`, a function of this file (A non-empty string, or `default` when the variable is unset.).
- Decision: the indented lines below run only when `value not in allowed` is true.
  - `not in` means is not contained in.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sorted` returns a new list with the items in order.

`src/scheduling_agent/infrastructure/env.py`, lines 71 to 71:

```python
    return value
```

- Ends the function and gives back the value named `value` to the caller.

### `src/scheduling_agent/infrastructure/failpoints.py`

In its own words: "Named places where a test can kill the process with SIGKILL, to prove a crash there is survivable."

22 non-blank lines; it defines `NoFailPoints`, `SigkillAt`, `from_env`.

`src/scheduling_agent/infrastructure/failpoints.py`, lines 1 to 14:

```python
"""Named places where a test can kill the process with SIGKILL, to prove a crash there is survivable."""

from __future__ import annotations

import os
import signal
from collections.abc import Mapping


class NoFailPoints:
    """The production default: nothing ever fails on purpose."""

    def hit(self, name: str) -> None:
        return None
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Makes the module `signal` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Defines the class `NoFailPoints`. The author's own description: "The production default: nothing ever fails on purpose."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `hit`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- Ends the function and gives back nothing (`None`) to the caller.

`src/scheduling_agent/infrastructure/failpoints.py`, lines 17 to 28:

```python
class SigkillAt:
    """Kills the whole process with SIGKILL (no cleanup, no `finally`) when execution reaches the named point.

    Enabled only by the `FAILPOINT` environment variable, which exists for the crash tests and is never set otherwise.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    def hit(self, name: str) -> None:
        if name == self._name:
            os.kill(os.getpid(), signal.SIGKILL)
```

- Defines the class `SigkillAt`. The author's own description: "Kills the whole process with SIGKILL (no cleanup, no `finally`) when execution reaches the named point."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- Stores the value named `name` under the name `self._name` (as an attribute of this object, so other methods can use it).
- Defines the method `hit`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- Decision: the indented lines below run only when `name == self._name` is true.
  - `==` means equal.
- Calls `os.kill` sends a signal to a process with 2 argument(s); the result is not kept.
  - `os.kill` sends a signal to a process.
  - `os.getpid` gives the number of this process.

`src/scheduling_agent/infrastructure/failpoints.py`, lines 31 to 34:

```python
def from_env(environ: Mapping[str, str]) -> NoFailPoints | SigkillAt:
    """`SigkillAt` when `FAILPOINT` names a point, otherwise `NoFailPoints`."""
    name = environ.get("FAILPOINT", "").strip()
    return SigkillAt(name) if name else NoFailPoints()
```

- Defines the function `from_env`. It returns the project type `NoFailPoints`, or the project type `SigkillAt`. The author's own description: "`SigkillAt` when `FAILPOINT` names a point, otherwise `NoFailPoints`."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get('FAILPOINT', '').strip` under the name `name`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `SigkillAt`, a class of this project (Kills the whole process with SIGKILL (no cleanup, no `finally`) when execution reaches the named point.).
  - `NoFailPoints`, a class of this project (The production default: nothing ever fails on purpose.).

### `src/scheduling_agent/infrastructure/files.py`

In its own words: "Readers for prompt files and the task set."

38 non-blank lines; it defines `FilePromptStore`, `load_tasks`.

`src/scheduling_agent/infrastructure/files.py`, lines 1 to 12:

```python
"""Readers for prompt files and the task set."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scheduling_agent.domain.prompts import Prompt, PromptNotFound
from scheduling_agent.domain.tasks import InvalidTasks, TaskSpec, validate_tasks

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `re` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.), `PromptNotFound` (No prompt file for that name and version, or the file's version line does not match.) from the project module `scheduling_agent.domain.prompts`.
- Brings in `InvalidTasks` (The task file breaks a rule of the lesson.), `TaskSpec` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.), `validate_tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) from the project module `scheduling_agent.domain.tasks`.
- Stores the result of calling `re.compile` under the name `_FRONT_MATTER`.
  - `re.compile` prepares a regular expression.

`src/scheduling_agent/infrastructure/files.py`, lines 15 to 26:

```python
class FilePromptStore:
    """Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def load(self, name: str, version: str) -> Prompt:
        path = self._root / name / f"{version}.md"
        if not path.exists():
            raise PromptNotFound(f"no prompt file {path}")
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
```

- Defines the class `FilePromptStore`. The author's own description: "Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `root` holds a file path.
- Stores the value named `root` under the name `self._root` (as an attribute of this object, so other methods can use it).
- Defines the method `load`. It returns the project type `Prompt`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
    - `version` holds text.
- Stores the result of `self._root / name / f'{version}.md'` under the name `path`.
  - `/` is divide.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `not path.exists()` is true.
  - `not` flips true and false.
  - `.exists(...)` asks whether the path exists.
- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `scheduling_agent.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `_FRONT_MATTER.match` under the name `match`.
  - `.match(...)` tries a regular expression at the start of text.
  - `.read_text(...)` reads a whole file as text.
- Decision: the indented lines below run only when `not match` is true.
  - `not` flips true and false.

`src/scheduling_agent/infrastructure/files.py`, lines 27 to 40:

```python
            raise PromptNotFound(f"{path} has no front matter with a version line")
        header = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
        if header.get("version", "").strip() != version:
            raise PromptNotFound(
                f"{path}: the version line says {header.get('version', '').strip()!r}, not {version!r}"
            )
        return Prompt(name, version, match.group(2).strip())


def load_tasks(path: Path) -> list[TaskSpec]:
    """Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked."""
    tasks: list[TaskSpec] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
```

- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `scheduling_agent.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `dict` under the name `header`.
  - `dict` makes a dictionary (a copy when given one).
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.split(...)` cuts text into a list of pieces at a separator.
  - `.splitlines(...)` cuts text into a list of lines.
  - `in` means is contained in.
  - `.group(...)` reads a captured part of a regular-expression match.
- Decision: the indented lines below run only when `header.get('version', '').strip() != version` is true.
  - `!=` means not equal.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `PromptNotFound`. Execution jumps out to the nearest matching `except`.
  - `PromptNotFound` from the project's `scheduling_agent.domain.prompts` (No prompt file for that name and version, or the file's version line does not match.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `Prompt` to the caller.
  - `Prompt` from the project's `scheduling_agent.domain.prompts` (A prompt as sent to the model, with the version that produced a given result.).
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.group(...)` reads a captured part of a regular-expression match.
- Defines the function `load_tasks`. It returns a list of the project type `TaskSpec`. The author's own description: "Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked."
- Its parameters:
    - `path` holds a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `tasks` as a list of the project type `TaskSpec` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- A `with` block: it sets up `path.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `path`.
- Loop: the indented lines below run once for each item of `enumerate(handle, start=1)`; `(number, line)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).

`src/scheduling_agent/infrastructure/files.py`, lines 41 to 48:

```python
            if not line.strip():
                continue
            try:
                tasks.append(TaskSpec.from_json(json.loads(line)))
            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
                raise InvalidTasks(f"{path}:{number}: {error!r}") from error
    validate_tasks(tasks)
    return tasks
```

- Decision: the indented lines below run only when `not line.strip()` is true.
  - `not` flips true and false.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Skips the rest of this round of the loop and starts the next.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - The method `from_json` of `TaskSpec`.
  - `json.loads` turns JSON text into Python data.
- `except` handler: it runs when the `try` block raised `(json.JSONDecodeError, KeyError, ValueError, TypeError)`; `error` names the error object.
- Raises an error: the result of calling `InvalidTasks`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidTasks` from the project's `scheduling_agent.domain.tasks` (The task file breaks a rule of the lesson.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) with 1 argument(s); the result is not kept.
  - `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.).
- Ends the function and gives back the value named `tasks` to the caller.

### `src/scheduling_agent/infrastructure/logging.py`

In its own words: "Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`)."

40 non-blank lines; it defines `_quote`, `LogfmtFormatter`, `fields`, `configure_logging`.

`src/scheduling_agent/infrastructure/logging.py`, lines 1 to 13:

```python
"""Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`).

Prompt and completion text never goes into an INFO line. Log sizes, ids, hashes and counts; a DEBUG line may
carry text for a developer who asked for it.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `UTC`, `datetime` from the standard library module `datetime`.
- Brings in `Any`, `TextIO` from the standard library module `typing`.

`src/scheduling_agent/infrastructure/logging.py`, lines 16 to 25:

```python
def _quote(value: object) -> str:
    text = str(value)
    return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text


class LogfmtFormatter(logging.Formatter):
    """Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
```

- Defines the function `_quote`. It returns text.
- Its parameters:
    - `value` holds any object.
- Stores the result of calling `str` under the name `text`.
  - `str` turns a value into text.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `json.dumps` turns Python data into JSON text.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.
- Defines the class `LogfmtFormatter`. It builds on the logging `Formatter` (turns a record into text). The author's own description: "Format a log record as one logfmt line, with the record's extra fields as key=value pairs."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `format`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `record` holds `logging.LogRecord`.
- Stores the result of calling `datetime.fromtimestamp(record.created, tz=UTC)....` under the name `timestamp`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `datetime.fromtimestamp` from the standard library module `datetime`.

`src/scheduling_agent/infrastructure/logging.py`, lines 26 to 39:

```python
        parts = [
            f"ts={timestamp}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={_quote(record.getMessage())}",
        ]
        parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
        if record.exc_info:
            parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


def fields(**values: Any) -> dict[str, Any]:
    """Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."""
```

- Stores a list of 4 item(s) under the name `parts`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `getMessage` of `record`.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `_quote`, a function defined in this file or passed in.
  - `getattr` reads an attribute whose name is held in a variable.
- Decision: the indented lines below run only when `record.exc_info` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `formatException` of `self`.
- Ends the function and gives back the result of calling `' '.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `fields`. It returns a dictionary from text to any value. The author's own description: "Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."
- Its parameters:
    - `**values` collects any extra named arguments into a dictionary.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/infrastructure/logging.py`, lines 40 to 52:

```python
    return {"fields": values}


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    """Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(LogfmtFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    quiet = max(logging.getLevelName(level), logging.WARNING)
    for noisy in ("httpx", "httpx2", "httpcore", "httpcore2", "anthropic"):
        logging.getLogger(noisy).setLevel(quiet)
```

- Ends the function and gives back a dictionary with 1 entry to the caller.
- Defines the function `configure_logging`. It returns nothing (None). The author's own description: "Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."
- Its parameters:
    - `level` holds text.
    - `stream` holds an open text file, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `logging.StreamHandler` under the name `handler`.
  - `logging.StreamHandler` from the standard library module `logging`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Calls the method `setFormatter` of `handler` with 1 argument(s); the result is not kept.
  - The method `setFormatter` of `handler`.
  - `LogfmtFormatter`, a class of this project (Format a log record as one logfmt line, with the record's extra fields as key=value pairs.).
- Stores the result of calling `logging.getLogger` under the name `root`.
  - `logging.getLogger` gets the logger with the given name.
- Stores a list of 1 item(s) under the name `root.handlers[:]`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Calls the method `setLevel` of `root` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `root`.
- Stores the result of calling `max` under the name `quiet`.
  - `max` picks the largest value.
  - `logging.getLevelName` from the standard library module `logging`.
- Loop: the indented lines below run once for each item of `('httpx', 'httpx2', 'httpcore', 'httpcore2', 'anthropic')`; `noisy` names the current item.
- Calls the method `setLevel` of `logging.getLogger(noisy)` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `logging.getLogger(noisy)`.
  - `logging.getLogger` gets the logger with the given name.

### `src/scheduling_agent/infrastructure/model_factory.py`

In its own words: "Builds the configured chat model from the environment: recorded, local server or Claude."

78 non-blank lines; it defines `ModelSettings`, `build_chat_model`.

`src/scheduling_agent/infrastructure/model_factory.py`, lines 1 to 14:

```python
"""Builds the configured chat model from the environment: recorded, local server or Claude."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import anthropic
import httpx

from scheduling_agent.application.ports import ChatModel, Clock
from scheduling_agent.infrastructure.anthropic_chat import AnthropicChatModel, Thinking
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx` (installed package) available.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `Clock` (Time, injected so tests are deterministic.) from the project module `scheduling_agent.application.ports`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.), `Thinking` from the project module `scheduling_agent.infrastructure.anthropic_chat`.

`src/scheduling_agent/infrastructure/model_factory.py`, lines 15 to 28:

```python
from scheduling_agent.infrastructure.env import (
    ConfigurationError,
    choice,
    optional_text,
    positive_float,
    positive_int,
    text,
)
from scheduling_agent.infrastructure.openai_compatible import OpenAICompatibleChatModel
from scheduling_agent.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from scheduling_agent.infrastructure.resilient import RetryingChatModel
from scheduling_agent.infrastructure.scripted_policy import ScriptedPolicyModel

PROVIDERS = ("scripted", "recorded", "anthropic", "openai-compatible")
```

- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_float` (A number greater than zero.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `scheduling_agent.infrastructure.openai_compatible`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `scheduling_agent.infrastructure.recording`.
- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `scheduling_agent.infrastructure.resilient`.
- Brings in `ScriptedPolicyModel` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.) from the project module `scheduling_agent.infrastructure.scripted_policy`.
- Stores a tuple of 4 item(s) under the name `PROVIDERS`.

`src/scheduling_agent/infrastructure/model_factory.py`, lines 31 to 42:

```python
@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Which model to call and how. See .env.example for every variable."""

    provider: str
    model: str
    recordings: Path
    record: bool
    openai_base_url: str
    openai_api_key: str | None
    anthropic_thinking: Thinking
    timeout_seconds: float
```

- Defines the class `ModelSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Which model to call and how. See .env.example for every variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `provider` as text; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `recordings` as a file path; it has no default, so a value must be given when the object is made.
- Declares `record` as true or false; it has no default, so a value must be given when the object is made.
- Declares `openai_base_url` as text; it has no default, so a value must be given when the object is made.
- Declares `openai_api_key` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `anthropic_thinking` as `Thinking`; it has no default, so a value must be given when the object is made.
- Declares `timeout_seconds` as a decimal number; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/infrastructure/model_factory.py`, lines 43 to 55:

```python
    attempts: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ModelSettings:
        env = os.environ if environ is None else environ
        provider = choice(env, "MODEL_PROVIDER", "scripted", PROVIDERS)
        default_model = {
            "scripted": "scripted-policy",
            "recorded": "recorded",
            "anthropic": "claude-haiku-5-5",
            "openai-compatible": "qwen2.5:1.5b",
        }[provider]
        thinking = choice(env, "ANTHROPIC_THINKING", "disabled", ("omit", "disabled", "between_tools"))
```

- Declares `attempts` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ModelSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of calling `choice` under the name `provider`.
  - `choice` from the project's `scheduling_agent.infrastructure.env` (One of the `allowed` strings.).
- Stores the part of `{'scripted': 'scripted-poli...` picked by `provider` under the name `default_model`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `choice` under the name `thinking`.
  - `choice` from the project's `scheduling_agent.infrastructure.env` (One of the `allowed` strings.).

`src/scheduling_agent/infrastructure/model_factory.py`, lines 56 to 69:

```python
        return cls(
            provider=provider,
            model=text(env, "MODEL_NAME", default_model),
            recordings=Path(text(env, "RECORDINGS_PATH", "tests/fixtures/recordings")),
            record=choice(env, "RECORD", "off", ("on", "off")) == "on",
            openai_base_url=text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
            openai_api_key=optional_text(env, "OPENAI_API_KEY"),
            anthropic_thinking=thinking,  # type: ignore[arg-type]
            timeout_seconds=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0),
            attempts=positive_int(env, "MODEL_ATTEMPTS", 3),
        )


def build_chat_model(settings: ModelSettings, clock: Clock, environ: Mapping[str, str] | None = None) -> ChatModel:
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `text` from the project's `scheduling_agent.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `==` means equal.
  - `optional_text` from the project's `scheduling_agent.infrastructure.env` (The variable's text, or None when it is unset or blank.).
  - `positive_float` from the project's `scheduling_agent.infrastructure.env` (A number greater than zero.).
  - `positive_int` from the project's `scheduling_agent.infrastructure.env` (An integer of 1 or more.).
  - `choice` from the project's `scheduling_agent.infrastructure.env` (One of the `allowed` strings.).
- Defines the function `build_chat_model`. It returns the project type `ChatModel`. The author's own description: "Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."
- Its parameters:
    - `settings` holds the project type `ModelSettings`.
    - `clock` holds the project type `Clock`.
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).

`src/scheduling_agent/infrastructure/model_factory.py`, lines 70 to 83:

```python
    """Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."""
    env = os.environ if environ is None else environ
    if settings.provider == "scripted":
        return ScriptedPolicyModel()
    if settings.provider == "recorded":
        return RecordedChatModel(RecordingStore(settings.recordings))
    live: ChatModel
    if settings.provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY must be set in the environment to use the anthropic provider")
        client = anthropic.Anthropic(timeout=settings.timeout_seconds, max_retries=0)
        live = AnthropicChatModel(client, settings.model, clock, settings.anthropic_thinking)
    else:
        http = httpx.Client(timeout=settings.timeout_seconds)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Decision: the indented lines below run only when `settings.provider == 'scripted'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `ScriptedPolicyModel` to the caller.
  - `ScriptedPolicyModel` from the project's `scheduling_agent.infrastructure.scripted_policy` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.).
- Decision: the indented lines below run only when `settings.provider == 'recorded'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `RecordedChatModel` to the caller.
  - `RecordedChatModel` from the project's `scheduling_agent.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Declares `live` as the project type `ChatModel`.
- Decision: the indented lines below run only when `settings.provider == 'anthropic'` is true.
  - `==` means equal.
- Decision: the indented lines below run only when `not env.get('ANTHROPIC_API_KEY')` is true.
  - `not` flips true and false.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `scheduling_agent.infrastructure.env` (An environment variable is missing or has an unusable value.).
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
- Stores the result of calling `AnthropicChatModel` under the name `live`.
  - `AnthropicChatModel` from the project's `scheduling_agent.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.

`src/scheduling_agent/infrastructure/model_factory.py`, lines 84 to 89:

```python
        live = OpenAICompatibleChatModel(http, settings.openai_base_url, settings.model, clock, settings.openai_api_key)
    live = RetryingChatModel(live, attempts=settings.attempts)
    if settings.record:
        note = {"provider": settings.provider, "requested_model": settings.model}
        return RecordingChatModel(live, RecordingStore(settings.recordings), note)
    return live
```

- Stores the result of calling `OpenAICompatibleChatModel` under the name `live`.
  - `OpenAICompatibleChatModel` from the project's `scheduling_agent.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
- Stores the result of calling `RetryingChatModel` under the name `live`.
  - `RetryingChatModel` from the project's `scheduling_agent.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
- Decision: the indented lines below run only when `settings.record` is true.
- Stores a dictionary with 2 entries under the name `note`.
- Ends the function and gives back the result of calling `RecordingChatModel` to the caller.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Ends the function and gives back the value named `live` to the caller.

### `src/scheduling_agent/infrastructure/openai_compatible.py`

In its own words: "A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."

109 non-blank lines; it defines `_message_payload`, `OpenAICompatibleChatModel`, `_arguments`.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 1 to 12:

```python
"""A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from scheduling_agent.application.ports import Clock
from scheduling_agent.domain.errors import PermanentModelError, TransientModelError
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `scheduling_agent.application.ports`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 14 to 26:

```python
_FINISH = {
    "stop": StopReason.END,
    "length": StopReason.LENGTH,
    "tool_calls": StopReason.TOOL_CALLS,
    "content_filter": StopReason.REFUSAL,
}


def _message_payload(message: ChatMessage) -> dict[str, Any]:
    if message.role is Role.TOOL:
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
    payload: dict[str, Any] = {"role": message.role.value, "content": message.content}
    if message.tool_calls:
```

- Stores a dictionary with 4 entries under the name `_FINISH`.
- Defines the function `_message_payload`. It returns a dictionary from text to any value.
- Its parameters:
    - `message` holds the project type `ChatMessage`.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Ends the function and gives back a dictionary with 3 entries to the caller.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 2 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `message.tool_calls` is true.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 27 to 40:

```python
        payload["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(dict(c.arguments))}}
            for c in message.tool_calls
        ]
    return payload


class OpenAICompatibleChatModel:
    """Talks to any server that implements `POST {base_url}/chat/completions`."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, clock: Clock, api_key: str | None = None) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._model = model
```

- Stores a list built by looping under the name `payload['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `json.dumps` turns Python data into JSON text.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the class `OpenAICompatibleChatModel`. The author's own description: "Talks to any server that implements `POST {base_url}/chat/completions`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `api_key` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `base_url.rstrip` under the name `self._base_url` (as an attribute of this object, so other methods can use it).
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 41 to 54:

```python
        self._clock = clock
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return True

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The JSON body for a request (public so tests can assert on it)."""
        messages: list[dict[str, Any]] = []
```

- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores one of two values, chosen by a condition under the name `self._headers` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The JSON body for a request (public so tests can assert on it)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 55 to 68:

```python
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(_message_payload(m) for m in request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_schema is not None:
```

- Decision: the indented lines below run only when `request.system` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `_message_payload`, a function defined in this file or passed in.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Decision: the indented lines below run only when `request.temperature is not None` is true.
  - `is not` means not the same object.
- Stores the `temperature` of `request` under the name `payload['temperature']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.top_p is not None` is true.
  - `is not` means not the same object.
- Stores the `top_p` of `request` under the name `payload['top_p']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 69 to 81:

```python
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": dict(request.response_schema), "strict": True},
            }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": dict(t.parameters)},
                }
                for t in request.tools
            ]
        return payload
```

- Stores a dictionary with 2 entries under the name `payload['response_format']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.
- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 83 to 95:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        started = self._clock.monotonic()
        try:
            reply = self._http.post(
                f"{self._base_url}/chat/completions", json=self.build_payload(request), headers=self._headers
            )
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        elapsed = self._clock.monotonic() - started
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
```

- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.post` under the name `reply`.
  - `post` on the stored object `self._http`: it sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `build_payload` of this object (The JSON body for a request (public so tests can assert on it).).
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Decision: the indented lines below run only when `reply.status_code == 429 or reply.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `scheduling_agent.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 96 to 107:

```python
        return self._parse(reply.json(), elapsed)

    def _parse(self, body: dict[str, Any], elapsed: float) -> ChatResponse:
        try:
            choice = body["choices"][0]
            message = choice["message"]
            usage = body["usage"]
            calls = tuple(
                ToolCall(str(c.get("id", f"call_{i}")), c["function"]["name"], _arguments(c["function"]["arguments"]))
                for i, c in enumerate(message.get("tool_calls") or [])
            )
            stop = StopReason.TOOL_CALLS if calls else _FINISH.get(choice.get("finish_reason") or "", StopReason.OTHER)
```

- Ends the function and gives back the result of calling `self._parse` to the caller.
  - The method `_parse` of this object.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the method `_parse`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `body` holds a dictionary from text to any value.
    - `elapsed` holds a decimal number.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the part of `body['choices']` picked by `0` under the name `choice`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `choice` picked by `'message'` under the name `message`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `body` picked by `'usage'` under the name `usage`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_arguments`, a function defined in this file or passed in.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores one of two values, chosen by a condition under the name `stop`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 108 to 121:

```python
            return ChatResponse(
                text=message.get("content") or "",
                stop_reason=stop,
                usage=Usage(int(usage["prompt_tokens"]), int(usage["completion_tokens"])),
                latency_seconds=round(elapsed, 4),
                model=str(body.get("model", self._model)),
                tool_calls=calls,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected response shape: {error!r}") from error


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `int` turns a value into a whole number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, IndexError, TypeError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `scheduling_agent.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_arguments`. It returns a dictionary from text to any value.
- Its parameters:
    - `raw` holds any value.
- Decision: the indented lines below run only when `isinstance(raw, dict)` is true.
  - `isinstance` asks whether a value is of a given type.

`src/scheduling_agent/infrastructure/openai_compatible.py`, lines 122 to 126:

```python
        return raw
    parsed = json.loads(raw) if raw else {}
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed
```

- Ends the function and gives back the value named `raw` to the caller.
- Stores one of two values, chosen by a condition under the name `parsed`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `json.loads` turns JSON text into Python data.
- Decision: the indented lines below run only when `not isinstance(parsed, dict)` is true.
  - `not` flips true and false.
  - `isinstance` asks whether a value is of a given type.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Ends the function and gives back the value named `parsed` to the caller.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import scheduling_agent.infrastructure.__init__; print(scheduling_agent.infrastructure.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Adapters that implement the ports: model clients, files, settings, logging.
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

1. What is the job of `src/scheduling_agent/infrastructure/__init__.py`?

   *Answer:* Adapters that implement the ports: model clients, files, settings, logging.

2. What is the job of `src/scheduling_agent/infrastructure/agent_db.py`?

   *Answer:* The agent's own SQLite database: saved runs, approvals, the audit log and memory facts.

3. What is the job of `src/scheduling_agent/infrastructure/anthropic_chat.py`?

   *Answer:* A chat model on the Anthropic Messages API, through the official SDK.

4. What is the job of `src/scheduling_agent/infrastructure/calendar_client.py`?

   *Answer:* The calendar service as seen from the agent: an HTTP client with timeouts, retries and an Idempotency-Key header.

5. What is the job of `src/scheduling_agent/infrastructure/calendar_db.py`?

   *Answer:* The calendar service's storage: events, attendees and idempotency keys in SQLite.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
