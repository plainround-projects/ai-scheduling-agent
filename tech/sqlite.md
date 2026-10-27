# SQLite

## What it is

**SQLite** is a database that lives in **one ordinary file**. There is no database server to start: your program links the SQLite library, opens the file, and runs SQL against it. It is the most widely deployed database in the world (phones, browsers, applications). Python includes a driver for it in the standard library: the module `sqlite3`.

A **transaction** is a group of changes that become visible together or not at all. **ACID** names the guarantees a good database gives: *atomic* (all or nothing), *consistent* (constraints hold), *isolated* (concurrent transactions do not see each other's half-done work) and *durable* (once committed, a crash does not lose it).

## Why this repository uses it

The calendar, orders and agent state need real transactions, constraints and crash safety, but not a separate server. SQLite gives that with a single file under `out/`, created by `make db` and deleted by `make down`. The same schema ideas (constraints, idempotency keys, version columns) then work with any other relational database.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/infrastructure/sqlite.py` | connection settings, the `transaction` helper and `apply_sql` |
| `sql/` | the schema, seed data and check queries |
| `Makefile` | `db` target runs the `sqlite3` command-line shell on the files |
| `src/scheduling_agent/infrastructure/` | the stores that use it (calendar, orders, agent state, audit log) |
| `out/*.db` | the database files (ignored by git) |

## How it works underneath

**One file, pages.** A SQLite database is a file divided into fixed-size pages that hold tables and indexes as B-trees (sorted tree structures). Reading a row means following the tree from a root page.

**Locking.** Only one connection can write at a time. In the default journal mode a write also blocks readers; in WAL mode, writers append to a `-wal` file next to the database and readers keep using the older consistent view until a *checkpoint* merges the log.

**Transactions and `BEGIN IMMEDIATE`.** SQLite has three kinds: `DEFERRED` (the default; takes locks when first needed, which can fail late), `IMMEDIATE` (takes the write lock at once) and `EXCLUSIVE`. `IMMEDIATE` is the right choice when you know you will write.

**Durability.** On commit SQLite asks the operating system to flush the log to disk (`fsync`), so a crash cannot lose a committed transaction.

**Typing.** SQLite columns have *type affinity*: a declared type is a preference, not a strict rule, unless the table is declared `STRICT`. This is why the schemas add `CHECK` constraints.

**Python's driver.** `sqlite3.connect` returns a connection; `connection.execute(sql, params)` runs one statement with `?` placeholders; `executemany` runs it for a list of parameter tuples; `executescript` runs a whole script.

## Walkthrough of this repository's use

### The helpers: `src/scheduling_agent/infrastructure/sqlite.py`

`src/scheduling_agent/infrastructure/sqlite.py`, lines 11 to 20:

```python
def connect(path: str | Path) -> sqlite3.Connection:
    """Open a database with the settings every store here relies on."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if str(path) != ":memory:":
        connection.execute("PRAGMA journal_mode = WAL")
    return connection
```

- `sqlite3.connect(path, ...)` opens (and creates, if needed) the database file. `timeout=10`: if another connection holds the write lock, wait up to 10 seconds before raising an error. `isolation_level=None` puts Python's driver in **autocommit mode**: it does not open transactions behind your back, so this code starts and ends them explicitly (see below). `check_same_thread=False` allows the connection to be used from threads other than the one that made it; the calendar class takes a lock so that calls take turns.
- `row_factory = sqlite3.Row` makes rows readable by column name (`row["start"]`) as well as by position.
- `PRAGMA foreign_keys = ON` turns on foreign-key enforcement for this connection.
- `PRAGMA journal_mode = WAL` (not for `:memory:`) switches to **write-ahead logging**: changes are first appended to a separate log file, and readers keep reading the last committed state while one writer writes. In the default mode a writer blocks all readers.

`src/scheduling_agent/infrastructure/sqlite.py`, lines 23 to 32:

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

`BEGIN IMMEDIATE` starts a transaction and takes the **write lock right away**, instead of waiting until the first write. Two writers therefore queue at the start instead of both reading and then one failing halfway. The `with` block runs the changes; on success `COMMIT` makes them permanent; on any exception (`BaseException` includes Ctrl-C) `ROLLBACK` undoes them all and the error continues upward. This is the "all or nothing" guarantee.

`src/scheduling_agent/infrastructure/sqlite.py`, lines 35 to 38:

```python
def apply_sql(connection: sqlite3.Connection, *files: Path) -> None:
    """Run SQL script files in the order given (the numbered files under sql/)."""
    for file in files:
        connection.executescript(file.read_text(encoding="utf-8"))
```

`executescript` runs a file with many statements. The numbered files are applied in order.

### A real transaction

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 112 to 129:

```python
        with transaction(self._db):
            replay = self._replay(idempotency_key, "book", digest)
            if replay:
                return replay
            validate_slot(start, minutes)
            if not names:
                raise UnknownPerson("a meeting needs at least one person")
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
```

### Idempotency keys

The services here keep a table `idempotency_keys` (see `sql.md`). A write and its key row are committed in the same transaction, so "the key was seen" and "the write happened" can never disagree. A retry with the same key and the same request returns the first result; the same key with a different request is a conflict. This is what makes a crashed-and-resumed agent safe: repeating a call cannot book a meeting twice.

## Try it yourself

1. The SQLite shell on this machine.

```bash
sqlite3 --version
```

What you should see (captured from this repository):

```text
3.51.0 2025-06-12 13:14:41 f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl (64-bit)
```

2. The SQLite library that Python itself carries.

```bash
.venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

What you should see (captured from this repository):

```text
3.54.1
```

3. Optimistic concurrency by hand: the first update (expecting version 1) changes 1 row; the second, with the same stale expectation, changes 0 rows, which is how a conflict shows.

```bash
sqlite3 :memory: "CREATE TABLE o (id INTEGER PRIMARY KEY, version INTEGER NOT NULL); INSERT INTO o VALUES (1, 1); UPDATE o SET version = version + 1 WHERE id = 1 AND version = 1; SELECT changes(); UPDATE o SET version = version + 1 WHERE id = 1 AND version = 1; SELECT changes();"
```

What you should see (captured from this repository):

```text
1
0
```

4. Foreign keys are off (0) by default and on (1) after the pragma.

```bash
sqlite3 :memory: "PRAGMA foreign_keys; PRAGMA foreign_keys = ON; PRAGMA foreign_keys;"
```

What you should see (captured from this repository):

```text
0
1
```

5. A rolled-back transaction leaves nothing behind: the table `t` does not exist afterwards (count 0).

```bash
sqlite3 :memory: "BEGIN IMMEDIATE; CREATE TABLE t (n); INSERT INTO t VALUES (1); ROLLBACK; SELECT count(*) FROM sqlite_master WHERE name = 't';"
```

What you should see (captured from this repository):

```text
0
```

## Mistakes people make

- **Forgetting `PRAGMA foreign_keys = ON`.** Without it `REFERENCES` is only documentation. Every connection here sets it.
- **Using the default `DEFERRED` transaction for writes.** Two writers can both read, then one fails with `database is locked`. `BEGIN IMMEDIATE` queues them instead.
- **Sharing a connection between threads without a lock.** The calendar class uses a re-entrant lock around each method.
- **Skipping the idempotency key.** A retry after a timeout could apply a write twice.
- **Copying a database file while it is being written.** With WAL, the `-wal` file belongs with the database; stop the service first (`make down` does).
- **Trusting column types.** SQLite will store text in an INTEGER column if it cannot convert it; the schemas add `CHECK` constraints.

## Check yourself

1. Why is there no server to start for SQLite?

   *Answer:* The library runs inside your program and reads the database file directly.

2. What does WAL change?

   *Answer:* Writers append to a log file and readers keep a consistent view, so readers are not blocked by a writer.

3. What does `BEGIN IMMEDIATE` do that `BEGIN` does not?

   *Answer:* It takes the write lock at the start, so writers queue instead of failing halfway.

4. How does `UPDATE ... WHERE version = ?` detect a conflict?

   *Answer:* If another writer changed the version first, no row matches and zero rows are updated.

5. What does an idempotency key table prevent?

   *Answer:* Applying the same write twice when a request is repeated.

## Further reading

- SQLite documentation, https://www.sqlite.org/docs.html (WAL, https://www.sqlite.org/wal.html; transactions, https://www.sqlite.org/lang_transaction.html) and Python `sqlite3`, https://docs.python.org/3/library/sqlite3.html (examples run with sqlite3 3.51.0).
