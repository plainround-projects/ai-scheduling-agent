# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-27

### Added

- A sample calendar service (FastAPI over SQLite): five people, two weeks of meetings, free slots for a set of people, one event, book and cancel with an `Idempotency-Key` header; DDL, seed and query scripts under `sql/calendar/`.
- A scheduling agent loop with five tools: two reads (`find_free_slots`, `get_event`) and three writes (`book_meeting`, `move_meeting`, `cancel_meeting`). Every write is a proposal that a person approves from the command line; an approval is valid only for the exact proposal it was granted for.
- Budgets on steps, tokens and wall-clock time, checked independently before every model call; a stopped run says which cap fired and what was and was not done.
- A checkpoint after every step (run id, step, messages, pending write) in one SQLite transaction, `agent resume`, and idempotency keys built from the run id and the step, so a run killed at any point resumes without a duplicate booking.
- Long-term memory of what people state about their own calendar, one fact per person and topic, recalled by embedding similarity blended with recency, with lapse and a forget command.
- 30 tasks with the calendar end state each should reach, judged by querying the calendar, with a runner that plays a person who approves only the expected changes.
- A deterministic stand-in model (`MODEL_PROVIDER=scripted`) so the whole system runs offline; model port with recorded, local and Claude adapters.
- Real-process tests: SIGKILL at five points, SIGTERM, parallel writes with one key, and the 30 tasks three times through the HTTP service. Layered package with the dependency rule enforced by import-linter, ruff, mypy, hash-pinned locks, a Dockerfile and compose file for the calendar service, and a CI workflow.
