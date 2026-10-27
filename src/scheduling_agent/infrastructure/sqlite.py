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
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")


def apply_sql(connection: sqlite3.Connection, *files: Path) -> None:
    """Run SQL script files in the order given (the numbered files under sql/)."""
    for file in files:
        connection.executescript(file.read_text(encoding="utf-8"))
