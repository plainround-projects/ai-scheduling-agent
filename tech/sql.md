# SQL

## What it is

A **database** stores data so it can be searched and changed safely. A **relational** database keeps data in **tables**: a table is a grid in which every **row** is one thing (one order, one meeting) and every **column** is one fact about it (the total, the start time). **SQL** (Structured Query Language, said "sequel" or "S-Q-L") is the language you use to talk to such a database. A statement is a sentence ending in a semicolon: `CREATE TABLE` makes a table, `INSERT` adds rows, `SELECT` reads rows, `UPDATE` changes rows, `DELETE` removes rows.

Tables are linked by **keys**. A **primary key** is the column (or columns) that uniquely names each row. A **foreign key** is a column that holds another table's primary key, so each meeting attendee row points at a real meeting. **Constraints** are rules the database itself enforces: `NOT NULL`, `UNIQUE`, `CHECK (...)`, `REFERENCES`.

## Why this repository uses it

Some facts must be right even if the application code has a bug. A refund ledger that can never exceed the order total, a meeting that can never overlap another for the same person, a retry that can never apply a write twice: the repository puts these rules into the **schema** (the table definitions), where the database enforces them on every write, whoever writes. The numbered files under `sql/` are the schema (`001`), the sample data (`002`) and the checking queries (`003`).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `sql/agent/001_schema.sql` | schema |
| `sql/agent/003_queries.sql` | queries that check the data |
| `sql/calendar/001_schema.sql` | schema |
| `sql/calendar/002_seed.sql` | sample data |
| `sql/calendar/003_queries.sql` | queries that check the data |
| `Makefile` | `sqlite3 ... < sql/...` / `$(PSQL) < sql/...` run these files |

## How it works underneath

**Declarative language.** In SQL you say *what* you want, not how to get it. The database's **query planner** chooses the steps (which index, which join order).

**Reading a SELECT.** The clauses run in a fixed logical order, not the order written: `FROM` and `JOIN` (build the rows), `WHERE` (filter rows), `GROUP BY` (form groups), `HAVING` (filter groups), `SELECT` (choose columns), `ORDER BY` (sort), `LIMIT` (cut). That is why `WHERE` cannot use an aggregate like `sum(...)` but `HAVING` can.

**Joins.** `a JOIN b ON a.x = b.y` builds every pair of rows that satisfies the condition. `LEFT JOIN` keeps unmatched left rows, filling the right columns with null.

**Null.** Null means "unknown or absent", and it is not equal to anything, not even to another null. Test with `IS NULL`.

**Transactions.** A group of statements that succeed or fail together (see `sqlite.md`). Constraints are checked inside the transaction, so a rule violation cancels the whole group.

**Idempotent scripts.** `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS` make a schema file safe to run twice, which `make db` relies on.

## Walkthrough of this repository's use

Dialect: SQLite.

`sql/agent/001_schema.sql`, statement by statement.

```sql
-- DDL for the agent's own state (SQLite): saved runs, approvals, the audit log and long-term memory.
-- `make db` creates out/agent.db from it.
PRAGMA foreign_keys = ON;
```

`PRAGMA` is an SQLite setting command. `foreign_keys = ON` makes SQLite enforce `REFERENCES` constraints (it ignores them by default); it applies to this connection only, so every connection turns it on.

```sql
-- The whole state of a run after its latest step (messages, pending write, counters), written in one transaction with
-- the step row below. A run with status running or awaiting_approval is resumed from here after a crash.
CREATE TABLE IF NOT EXISTS runs (
    run_id     TEXT PRIMARY KEY,
    task       TEXT NOT NULL,
    session    TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('running', 'awaiting_approval', 'done', 'stopped', 'failed')),
    steps      INTEGER NOT NULL,
    tokens     INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

Creates the table `runs` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `run_id`: type `TEXT`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null.
- Column `task`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `session`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `status`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `CHECK (status IN ('running', 'awaiting_approval', 'done', 'stopped', 'failed'))`: the database rejects any row for which this is false; `IN (` equals one of the listed values.
- Column `steps`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value.
- Column `tokens`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value.
- Column `state_json`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `created_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `updated_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.

```sql
CREATE TABLE IF NOT EXISTS run_steps (
    run_id              TEXT NOT NULL REFERENCES runs (run_id),
    step                INTEGER NOT NULL,
    status              TEXT NOT NULL,
    pending_approval_id TEXT,
    saved_at            TEXT NOT NULL,
    PRIMARY KEY (run_id, step)
);
```

Creates the table `run_steps` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `run_id`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `REFERENCES runs (run_id)`: a *foreign key*; the value must exist in `runs.run_id`.
- Column `step`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value.
- Column `status`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `pending_approval_id`: type `TEXT`: text of any length.
- Column `saved_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- `PRIMARY KEY (run_id, step)`: the pair of columns together identifies a row (a *composite* key).

```sql
-- A write is a proposal until a person decides. One approval per run and step: asking twice returns the same row.
CREATE TABLE IF NOT EXISTS approvals (
    id            TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL,
    step          INTEGER NOT NULL,
    proposal_json TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at    TEXT NOT NULL,
    decided_at    TEXT,
    decided_by    TEXT,
    UNIQUE (run_id, step)
);
```

Creates the table `approvals` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `id`: type `TEXT`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null.
- Column `run_id`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `step`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value.
- Column `proposal_json`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `status`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `CHECK (status IN ('pending', 'approved', 'rejected'))`: the database rejects any row for which this is false; `IN (` equals one of the listed values.
- Column `created_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `decided_at`: type `TEXT`: text of any length.
- Column `decided_by`: type `TEXT`: text of any length.
- `UNIQUE (run_id, step)`: no two rows may have the same combination of these columns.

```sql
-- Append-only. A replayed write after a crash writes the same line again; the unique key keeps it once.
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    at          TEXT NOT NULL,
    run_id      TEXT NOT NULL,
    step        INTEGER NOT NULL,
    action      TEXT NOT NULL,
    outcome     TEXT NOT NULL CHECK (outcome IN ('refused', 'written', 'failed', 'rejected')),
    approval_id TEXT,
    detail      TEXT NOT NULL,
    UNIQUE (run_id, step, action, outcome)
);
```

Creates the table `audit_log` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `id`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `PRIMARY KEY`: the value that identifies each row; it must be unique and not null; `AUTOINCREMENT`: the database picks the next number itself and never reuses one.
- Column `at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `run_id`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `step`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value.
- Column `action`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `outcome`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `CHECK (outcome IN ('refused', 'written', 'failed', 'rejected'))`: the database rejects any row for which this is false; `IN (` equals one of the listed values.
- Column `approval_id`: type `TEXT`: text of any length.
- Column `detail`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- `UNIQUE (run_id, step, action, outcome)`: no two rows may have the same combination of these columns.

```sql
-- Facts a person stated about themselves: one row per person and topic, so a changed preference replaces the old one.
CREATE TABLE IF NOT EXISTS memory_facts (
    person     TEXT NOT NULL,
    topic      TEXT NOT NULL,                          -- earliest_start, latest_end or day:<weekday number>
    kind       TEXT NOT NULL,
    value      TEXT NOT NULL,
    text       TEXT NOT NULL,
    session    TEXT NOT NULL,
    stated_on  TEXT NOT NULL,
    expires_on TEXT,
    PRIMARY KEY (person, topic)
);
```

Creates the table `memory_facts` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `person`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `topic`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value. The author's note: earliest_start, latest_end or day:&lt;weekday number&gt;.
- Column `kind`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `value`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `text`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `session`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `stated_on`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.
- Column `expires_on`: type `TEXT`: text of any length.
- `PRIMARY KEY (person, topic)`: the pair of columns together identifies a row (a *composite* key).

`sql/agent/003_queries.sql`, statement by statement.

```sql
-- The queries the lesson's checks run against the agent's own database.
-- 1. Unfinished runs: what `agent resume` would pick up after a crash.
SELECT run_id, status, steps, task FROM runs WHERE status IN ('running', 'awaiting_approval');
```

- **`SELECT`** chooses what to return, one result column per item:
  - `run_id`: the column or value.
  - `status`: the column or value.
  - `steps`: the column or value.
  - `task`: the column or value.
- **`FROM`** names the table the rows come from: `runs`.
- **`WHERE`** keeps only the rows for which the condition is true: `status IN ('running', 'awaiting_approval')`. Here `IN (` equals one of the listed values.

```sql
-- 2. Pending approvals: what a person still has to decide.
SELECT id, run_id, step, proposal_json FROM approvals WHERE status = 'pending' ORDER BY created_at;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `id`: the column or value.
  - `run_id`: the column or value.
  - `step`: the column or value.
  - `proposal_json`: the column or value.
- **`FROM`** names the table the rows come from: `approvals`.
- **`WHERE`** keeps only the rows for which the condition is true: `status = 'pending'`.
- **`ORDER BY`** `created_at`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 3. No write without an approval: every 'written' line must have an approved approval. Must return no rows.
SELECT l.run_id, l.step, l.action FROM audit_log l
LEFT JOIN approvals a ON a.id = l.approval_id AND a.status = 'approved'
WHERE l.outcome = 'written' AND a.id IS NULL;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `l.run_id`: the column `run_id` of the table (or alias) `l`.
  - `l.step`: the column `step` of the table (or alias) `l`.
  - `l.action`: the column `action` of the table (or alias) `l`.
- **`FROM`** names the table the rows come from: `audit_log l` (`l` is a short alias for it).
- **`LEFT JOIN`** `approvals a ON a.id = l.approval_id AND a.status = 'approved'`: `LEFT JOIN` also keeps the rows of the left table that have no match on the right (the right-hand columns are then null).
- **`WHERE`** keeps only the rows for which the condition is true: `l.outcome = 'written'`; `a.id IS NULL`. Here `IS NULL` has no value (is null; `= NULL` would not work, because null is never equal to anything).

```sql
-- 4. Refusals: writes that were proposed and not (yet) allowed.
SELECT run_id, step, action, detail FROM audit_log WHERE outcome = 'refused' ORDER BY id;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `run_id`: the column or value.
  - `step`: the column or value.
  - `action`: the column or value.
  - `detail`: the column or value.
- **`FROM`** names the table the rows come from: `audit_log`.
- **`WHERE`** keeps only the rows for which the condition is true: `outcome = 'refused'`.
- **`ORDER BY`** `id`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 5. What the agent remembers, per person.
SELECT person, topic, value, text, stated_on, expires_on FROM memory_facts ORDER BY person, topic;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `person`: the column or value.
  - `topic`: the column or value.
  - `value`: the column or value.
  - `text`: the column or value.
  - `stated_on`: the column or value.
  - `expires_on`: the column or value.
- **`FROM`** names the table the rows come from: `memory_facts`.
- **`ORDER BY`** `person, topic`: sorts the result (`DESC` means largest first; the default is smallest first).

`sql/calendar/001_schema.sql`, statement by statement.

```sql
-- DDL for the sample calendar service (SQLite). Run order: 001_schema.sql, 002_seed.sql, 003_queries.sql.
-- `make db` creates out/calendar.db from the first two.
PRAGMA foreign_keys = ON;
```

`PRAGMA` is an SQLite setting command. `foreign_keys = ON` makes SQLite enforce `REFERENCES` constraints (it ignores them by default); it applies to this connection only, so every connection turns it on.

```sql
CREATE TABLE IF NOT EXISTS people (
    name         TEXT PRIMARY KEY,                     -- lowercase first name, the id used in every call
    display_name TEXT NOT NULL
);
```

Creates the table `people` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `name`: type `TEXT`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null. The author's note: lowercase first name, the id used in every call.
- Column `display_name`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.

```sql
-- An event never disappears: a cancelled event keeps its row (cancelled = 1) and stops blocking anyone's time.
CREATE TABLE IF NOT EXISTS events (
    id         TEXT PRIMARY KEY,                       -- ev-0001, ev-0002, ...
    start      TEXT NOT NULL,                          -- local time, YYYY-MM-DDTHH:MM
    minutes    INTEGER NOT NULL CHECK (minutes BETWEEN 30 AND 240 AND minutes % 30 = 0),
    cancelled  INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1)),
    created_at TEXT NOT NULL
);
```

Creates the table `events` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `id`: type `TEXT`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null. The author's note: ev-0001, ev-0002, ....
- Column `start`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value. The author's note: local time, YYYY-MM-DDTHH:MM.
- Column `minutes`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value; `CHECK (minutes BETWEEN 30 AND 240 AND minutes % 30 = 0)`: the database rejects any row for which this is false; `BETWEEN` lies in the range from the first value to the second, both ends included; `%` the remainder after division (modulo).
- Column `cancelled`: type `INTEGER`: a whole number (SQLite stores it in 1 to 8 bytes as needed); `NOT NULL`: the column must always have a value; `DEFAULT 0`: the value used when an insert gives none; `CHECK (cancelled IN (0, 1))`: the database rejects any row for which this is false; `IN (` equals one of the listed values.
- Column `created_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.

```sql
CREATE TABLE IF NOT EXISTS event_people (
    event_id TEXT NOT NULL REFERENCES events (id),
    person   TEXT NOT NULL REFERENCES people (name),
    PRIMARY KEY (event_id, person)
);
```

Creates the table `event_people` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `event_id`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `REFERENCES events (id)`: a *foreign key*; the value must exist in `events.id`.
- Column `person`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `REFERENCES people (name)`: a *foreign key*; the value must exist in `people.name`.
- `PRIMARY KEY (event_id, person)`: the pair of columns together identifies a row (a *composite* key).

```sql
CREATE INDEX IF NOT EXISTS event_people_person_idx ON event_people (person);
```

Creates an index named `event_people_person_idx` on `event_people(person)`. An index is a sorted side structure that lets the database find rows by these columns without reading the whole table.

```sql
CREATE INDEX IF NOT EXISTS events_start_idx ON events (start);
```

Creates an index named `events_start_idx` on `events(start)`. An index is a sorted side structure that lets the database find rows by these columns without reading the whole table.

```sql
-- One row per Idempotency-Key. The write it protects and this row are committed in one transaction, so a key is never
-- "seen" without its write, and a retry returns the first result without touching events at all.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key          TEXT PRIMARY KEY,
    operation    TEXT NOT NULL CHECK (operation IN ('book', 'cancel')),
    request_hash TEXT NOT NULL,                        -- the same key with a different request is a conflict
    event_id     TEXT NOT NULL REFERENCES events (id),
    created_at   TEXT NOT NULL
);
```

Creates the table `idempotency_keys` if it does not exist yet (`IF NOT EXISTS` makes the script safe to repeat). A table is a grid: one row per thing, one column per fact. Inside the parentheses, each line defines a column or a table rule:
- Column `key`: type `TEXT`: text of any length; `PRIMARY KEY`: the value that identifies each row; it must be unique and not null.
- Column `operation`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `CHECK (operation IN ('book', 'cancel'))`: the database rejects any row for which this is false; `IN (` equals one of the listed values.
- Column `request_hash`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value. The author's note: the same key with a different request is a conflict.
- Column `event_id`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value; `REFERENCES events (id)`: a *foreign key*; the value must exist in `events.id`.
- Column `created_at`: type `TEXT`: text of any length; `NOT NULL`: the column must always have a value.

`sql/calendar/002_seed.sql`, statement by statement.

```sql
-- DML: five people and two weeks of existing meetings (generated by scripts/make_calendar_seed.py).
INSERT INTO people (name, display_name) VALUES
    ('alice', 'Alice'),
    ('bob', 'Bob'),
    ('carol', 'Carol'),
    ... (2 more rows)
```

Adds 5 row(s) to the table `people`. The column list `(name, display_name)` names the columns; each parenthesized line after `VALUES` is one row whose values are in the same order. Text is in single quotes; `DATE '2026-07-07'` is a date literal; numbers have no quotes.

```sql
INSERT INTO events (id, start, minutes, cancelled, created_at) VALUES
    ('ev-0001', '2026-11-02T10:00', 30, 0, '2026-10-27T00:00'),
    ('ev-0002', '2026-11-02T14:30', 30, 0, '2026-10-27T00:00'),
    ('ev-0003', '2026-11-02T11:00', 60, 0, '2026-10-27T00:00'),
    ... (30 more rows)
```

Adds 33 row(s) to the table `events`. The column list `(id, start, minutes, cancelled, created_at)` names the columns; each parenthesized line after `VALUES` is one row whose values are in the same order. Text is in single quotes; `DATE '2026-07-07'` is a date literal; numbers have no quotes.

```sql
INSERT INTO event_people (event_id, person) VALUES
    ('ev-0001', 'alice'),
    ('ev-0001', 'bob'),
    ('ev-0001', 'dave'),
    ... (66 more rows)
```

Adds 69 row(s) to the table `event_people`. The column list `(event_id, person)` names the columns; each parenthesized line after `VALUES` is one row whose values are in the same order. Text is in single quotes; `DATE '2026-07-07'` is a date literal; numbers have no quotes.

`sql/calendar/003_queries.sql`, statement by statement.

```sql
-- The queries the service and the lesson's checks run, each with a line on what it shows.
-- 1. Active events per person: what each person's week looks like.
SELECT ep.person, count(*) AS meetings, sum(e.minutes) AS minutes
FROM events e JOIN event_people ep ON ep.event_id = e.id
WHERE e.cancelled = 0 GROUP BY ep.person ORDER BY ep.person;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `ep.person`: the column `person` of the table (or alias) `ep`.
  - `count(*)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS meetings` names this result column `meetings`.
  - `sum(e.minutes)`: `sum`: adds up the numbers in a column over the group of rows. `AS minutes` names this result column `minutes`.
- **`FROM`** names the table the rows come from: `events e` (`e` is a short alias for it).
- **`JOIN`** `event_people ep ON ep.event_id = e.id`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped.
- **`WHERE`** keeps only the rows for which the condition is true: `e.cancelled = 0`.
- **`GROUP BY`** `ep.person`: rows with the same value(s) form one group, and aggregate functions (`count`, `sum`, ...) are worked out per group.
- **`ORDER BY`** `ep.person`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 2. Double bookings: two active events that overlap for the same person. Must return no rows.
SELECT a.id, b.id, pa.person
FROM events a
JOIN events b ON a.id < b.id AND a.cancelled = 0 AND b.cancelled = 0
 AND a.start < strftime('%Y-%m-%dT%H:%M', b.start, '+' || b.minutes || ' minutes')
 AND b.start < strftime('%Y-%m-%dT%H:%M', a.start, '+' || a.minutes || ' minutes')
JOIN event_people pa ON pa.event_id = a.id
JOIN event_people pb ON pb.event_id = b.id AND pb.person = pa.person;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `a.id`: the column `id` of the table (or alias) `a`.
  - `b.id`: the column `id` of the table (or alias) `b`.
  - `pa.person`: the column `person` of the table (or alias) `pa`.
- **`FROM`** names the table the rows come from: `events a` (`a` is a short alias for it).
- **`JOIN`** `events b ON a.id < b.id AND a.cancelled = 0 AND b.cancelled = 0 AND a.start < strftime('%Y-%m-%dT%H:%M', b.start, '+' || b.minutes || ' minutes') AND b.start < strftime('%Y-%m-%dT%H:%M', a.start, '+' || a.minutes || ' minutes')`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped. `||` joins two pieces of text together.
- **`JOIN`** `event_people pa ON pa.event_id = a.id`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped.
- **`JOIN`** `event_people pb ON pb.event_id = b.id AND pb.person = pa.person`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped.

```sql
-- 3. Replays: how many writes were answered from an idempotency key instead of being applied twice.
SELECT operation, count(*) AS keys FROM idempotency_keys GROUP BY operation;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `operation`: the column or value.
  - `count(*)`: `count`: counts rows (`count(*)` counts every row; `count(x)` counts rows where `x` is not null; `count(DISTINCT x)` counts different values). `AS keys` names this result column `keys`.
- **`FROM`** names the table the rows come from: `idempotency_keys`.
- **`GROUP BY`** `operation`: rows with the same value(s) form one group, and aggregate functions (`count`, `sum`, ...) are worked out per group.

```sql
-- 4. Events that were created by an agent run (their keys are 64 hex characters, built from run id and step).
SELECT e.id, e.start, e.minutes, k.key
FROM events e JOIN idempotency_keys k ON k.event_id = e.id AND k.operation = 'book'
ORDER BY e.id;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `e.id`: the column `id` of the table (or alias) `e`.
  - `e.start`: the column `start` of the table (or alias) `e`.
  - `e.minutes`: the column `minutes` of the table (or alias) `e`.
  - `k.key`: the column `key` of the table (or alias) `k`.
- **`FROM`** names the table the rows come from: `events e` (`e` is a short alias for it).
- **`JOIN`** `idempotency_keys k ON k.event_id = e.id AND k.operation = 'book'`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped.
- **`ORDER BY`** `e.id`: sorts the result (`DESC` means largest first; the default is smallest first).

```sql
-- 5. Cancelled events and when their cancellation was recorded.
SELECT e.id, e.start, k.created_at AS cancelled_at
FROM events e JOIN idempotency_keys k ON k.event_id = e.id AND k.operation = 'cancel'
WHERE e.cancelled = 1 ORDER BY e.id;
```

- **`SELECT`** chooses what to return, one result column per item:
  - `e.id`: the column `id` of the table (or alias) `e`.
  - `e.start`: the column `start` of the table (or alias) `e`.
  - `k.created_at`: the column `created_at` of the table (or alias) `k`. `AS cancelled_at` names this result column `cancelled_at`.
- **`FROM`** names the table the rows come from: `events e` (`e` is a short alias for it).
- **`JOIN`** `idempotency_keys k ON k.event_id = e.id AND k.operation = 'cancel'`: `JOIN` pairs each row with the rows of another table that satisfy the `ON` condition; rows without a match are dropped.
- **`WHERE`** keeps only the rows for which the condition is true: `e.cancelled = 1`.
- **`ORDER BY`** `e.id`: sorts the result (`DESC` means largest first; the default is smallest first).

## Try it yourself

1. The SQLite command-line shell that the Makefile uses.

```bash
sqlite3 --version
```

What you should see (captured from this repository):

```text
3.51.0 2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl (64-bit)
```

2. Run a schema file against a throwaway in-memory database and list the tables it made.

```bash
sqlite3 :memory: ".read sql/calendar/001_schema.sql" ".tables" 2>&1 | head -5
```

What you should see (captured from this repository):

```text
event_people      events            idempotency_keys  people          
```

3. A `CHECK` constraint at work: the second insert is refused by the database.

```bash
sqlite3 :memory: "CREATE TABLE t (n INTEGER CHECK (n > 0)); INSERT INTO t VALUES (5); INSERT INTO t VALUES (-1);" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
Error: stepping, CHECK constraint failed: n > 0 (19)
```

4. Small expressions: `+`, text joining `||`, `abs`, and the null rules (`NULL = NULL` is not true, `NULL IS NULL` is).

```bash
sqlite3 :memory: "SELECT 1 + 1, 'a' || 'b', abs(-3), NULL = NULL, NULL IS NULL"
```

What you should see (captured from this repository):

```text
2|ab|3||1
```

5. `GROUP BY` and `HAVING`: group `a` has total 3 and group `b` has total 5, both above 2.

```bash
sqlite3 :memory: "CREATE TABLE s (g TEXT, v INTEGER); INSERT INTO s VALUES ('a',1),('a',2),('b',5); SELECT g, count(*), sum(v) FROM s GROUP BY g HAVING sum(v) > 2 ORDER BY g;"
```

What you should see (captured from this repository):

```text
a|2|3
b|1|5
```

## Mistakes people make

- **Using `= NULL`.** Never true. Use `IS NULL`.
- **`WHERE` with an aggregate.** Use `HAVING` for conditions on `sum(...)` and `count(...)`.
- **Trusting only application code for rules.** Constraints and triggers hold even if some other program writes the table.
- **Building SQL by gluing text.** Values are passed as parameters (`?` in SQLite, `%s` in psycopg) so a value can never change the meaning of the statement.
- **Forgetting `IF NOT EXISTS`.** Running the schema twice would fail. The files are written to be repeatable.
- **Foreign keys in SQLite.** They are off by default; each connection runs `PRAGMA foreign_keys = ON`.

## Check yourself

1. What does a primary key guarantee?

   *Answer:* Each row has a unique, non-null identifier.

2. What is the difference between `WHERE` and `HAVING`?

   *Answer:* `WHERE` filters rows before grouping; `HAVING` filters groups after aggregates are computed.

3. What does `LEFT JOIN` keep that `JOIN` drops?

   *Answer:* Left rows with no match on the right.

4. Why is `NULL = NULL` not true?

   *Answer:* Null means unknown; two unknowns are not known to be equal.

5. How does a trigger protect the refund ledger?

   *Answer:* It runs before each insert, and aborts the insert if the total would exceed the order total.

## Further reading

- SQLite SQL reference, https://www.sqlite.org/lang.html; PostgreSQL 17 SQL commands, https://www.postgresql.org/docs/17/sql-commands.html (SQLite examples were run locally with sqlite3 3.51; the PostgreSQL files could not be run here because Docker was down, so they are explained but not executed in this session).
