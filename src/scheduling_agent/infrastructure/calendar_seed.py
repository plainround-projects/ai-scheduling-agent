"""Create and reset the calendar database from the numbered SQL files under sql/calendar."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scheduling_agent.infrastructure.sqlite import apply_sql


def init_calendar(connection: sqlite3.Connection, sql_dir: Path) -> None:
    """Create the tables and load the seed if the database has no people yet."""
    apply_sql(connection, sql_dir / "calendar" / "001_schema.sql")
    if connection.execute("SELECT count(*) FROM people").fetchone()[0] == 0:
        apply_sql(connection, sql_dir / "calendar" / "002_seed.sql")


def reset_calendar(connection: sqlite3.Connection, sql_dir: Path) -> None:
    """Delete every row and load the seed again (the demo and test aid behind POST /admin/reset)."""
    connection.execute("PRAGMA foreign_keys = OFF")
    for table in ("idempotency_keys", "event_people", "events", "people"):
        connection.execute(f"DELETE FROM {table}")
    connection.execute("PRAGMA foreign_keys = ON")
    apply_sql(connection, sql_dir / "calendar" / "002_seed.sql")
