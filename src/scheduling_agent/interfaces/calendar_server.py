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


if __name__ == "__main__":
    sys.exit(main())
