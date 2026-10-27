# ai-scheduling-agent

A scheduling assistant that books, moves and cancels meetings on a sample calendar service. It reads freely; every write waits for a person to approve it. It runs inside step, token and time budgets, saves its state after every step so a crash resumes without booking twice, and remembers what a person told it in an earlier session.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-scheduling-agent`, "Build a scheduling agent that cannot double-book" (`data-structure-explainer/src/content/tracks/ai/98-project-scheduling-agent.md` in the Plainround app) |
| **Planned hours** | 14 |
| **Level** | Intermediate |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions in [docs/adr](docs/adr) |

## Read this first: which model drives the agent

No model key was available when this was built, and the lesson's properties (a write needs a yes, a crash cannot double-book, a budget stops a loop, memory is applied) belong to the harness around the model, not to a model. So the default `MODEL_PROVIDER=scripted` is a **deterministic rule-based stand-in** that speaks the same tool-calling protocol a language model does. It is not a language model. The 90 of 90 task attempts below show that the machinery is right; they say nothing about how well any language model schedules. The Claude adapter (`MODEL_PROVIDER=anthropic`) and the local open-weight adapter (`MODEL_PROVIDER=openai-compatible`, for example `qwen2.5:1.5b` on ollama) are written, unit-tested with mock transports, and exercised only by the opt-in `make test-live`; running the 30 tasks with one of them is the experiment that measures a model. See [ADR 0006](docs/adr/0006-a-deterministic-stand-in-for-the-model.md).

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13; CI uses 3.12) | the agent, the calendar service, the tests |
| GNU Make | 3.81 or newer (the one on macOS works) | every command below |
| `sqlite3` command line | any (preinstalled on macOS) | `make db` runs the numbered SQL files |
| `curl` | any | the health wait in `make up` |
| Python packages | `fastapi` 0.162.0, `uvicorn` 0.54.0, `httpx` 0.28.1, `anthropic` 2.3.0 at run time; pytest, pytest-cov, ruff, mypy, import-linter, pip-audit for development. Pinned with hashes in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| Docker (optional) | any recent Docker with Compose v2 | only `docker compose up` for the calendar service in a container |
| ollama (optional) | any recent version, with `qwen2.5:1.5b` and `nomic-embed-text` | only `make record` and the local part of `make test-live` |
| Anthropic API key (optional) | none needed for any default command | only the opt-in Claude live test |

No cloud account and no secrets. A key is read from your shell's `ANTHROPIC_API_KEY` and nowhere else.

## Setup, run, test, stop

```bash
make up              # create .venv from the lock file, create the two SQLite databases, start the calendar service on :8090
make run             # the lesson's scenario: a booking that waits for approval, then the 30 tasks three times each
make demo            # only the booking: tell, run, pending, approve and resume, audit
make tasks           # only the 30 tasks x 3 runs, judged by the calendar's end state
make test            # every offline test with coverage (unit, real processes with SIGKILL, the 30 tasks over HTTP)
make test-integration   # only the real-process tests: the five SIGKILL crash points, SIGTERM, parallel writes
make lint            # ruff check, ruff format check, mypy --strict, import-linter
make audit           # known-vulnerability check of the locked dependencies
make down            # stop the calendar service and remove out/ (databases, logs)
```

`make help` lists every target. To use the agent by hand while the service is up (`make up`):

```bash
export CALENDAR_URL=http://127.0.0.1:8090 AGENT_DB=out/agent.db
.venv/bin/agent tell alice "I never want meetings before 10"
.venv/bin/agent run "Book a 30-minute meeting with alice and bob on 2026-11-03." --run-id r1   # stops: awaiting approval
.venv/bin/agent pending                                    # what is waiting for a person
.venv/bin/agent approve <approval id> --resume             # or: agent reject <approval id>
.venv/bin/agent audit --run r1
.venv/bin/agent memory                                     # what it remembers;  agent forget alice  deletes it
```

Exit codes: 0 done, 5 awaiting approval, 6 stopped by a budget cap, 2 configuration error, 1 other error. Logs are one logfmt line per event on standard error (`ts=... level=... logger=... msg=... key=value`); they carry run ids, steps, token counts and outcomes, never the task text or model output at INFO level.

To use a real model:

```bash
make models                                         # ollama pull qwen2.5:1.5b and nomic-embed-text (weights stay in ollama's store)
MODEL_PROVIDER=openai-compatible .venv/bin/agent run "Book a 30-minute meeting with alice and bob on 2026-11-03."
MODEL_PROVIDER=anthropic MODEL_NAME=claude-haiku-5-5 .venv/bin/agent tasks --runs 3   # needs ANTHROPIC_API_KEY in your shell
make test-live                                      # opt in; skipped by default
```

Variables are listed in `env.example` (copy it to `.env`).

## What a run looks like

The output of `make demo` and `make tasks` on the recorded build (task ids shortened):

```text
remembered: I never want meetings before 10
run demo-1: awaiting_approval after 2 step(s), 251 tokens
  waiting for approval ap-162bb5ab94: {"action":"book","args":{"minutes":30,"people":["alice","bob"],"start":"2026-11-03T10:00"}}
  decide with: agent approve ap-162bb5ab94 --resume   (or: agent reject ...)
run demo-1: done after 3 step(s), 403 tokens
  Booked event ev-0034.
2026-10-27T01:56:41 run demo-1 step 2 book refused no approval yet; proposal recorded
2026-10-27T01:56:57 run demo-1 step 2 book written ev-0034

task                 passed  steps  tokens  writes without approval  ended
t-book-01            3/3         3     414                        0  done
...
t-impossible-03      3/3        12    1572                        0  stopped:steps
...
tasks passed: 90/90 attempts (30 tasks x 3 runs)
writes without an approval: 0
```

The demo's slot is 10:00, not 09:00, because alice's remembered preference moved the search. `make tasks` prints the full 30-row table.

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | A test that sends the same booking twice with one key finds exactly one new event. | `make test`; `tests/unit/infrastructure/test_calendar_service.py::test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event` | The second call returns the first event with `replayed: true` and the table holds one new row. Next to it: two different bookings with identical content but different keys are both created (the key decides, not the content); a failed write leaves no key behind (key and write commit in one transaction); a reused key with a different request is a 409. The same guarantees are re-proved over HTTP with parallel requests in `tests/integration/test_processes.py`. |
| 2 | A test that calls a write tool without an approval id finds no new event and one "refused" line in the audit log. | `make test`; `tests/unit/application/test_tools_and_agent.py::test_a_write_without_an_approval_id_changes_nothing_and_leaves_one_refused_audit_line` | The calendar is unchanged and the audit log gains exactly one `refused` line. `test_an_unknown_pending_or_mismatched_approval_does_not_open_the_write` covers the trap: an approval granted for one proposal cannot be spent on a changed one, because the approval carries the proposal's digest. `sql/agent/003_queries.sql` query 3 (a `written` audit line without an approved approval) returns no rows after the 30 tasks. |
| 3 | A task that cannot succeed stops at the step cap with that message, and its token use is under the budget. | `make tasks` (row `t-impossible-03`); `test_a_task_that_cannot_succeed_stops_at_the_step_cap_and_says_which_cap_fired` | The row shows `12` steps, `1572` tokens and `stopped:steps`, against a 4,000-token cap; the run's final text starts `Stopped: step cap reached: 12/12` and says what was done and what was not. `test_the_token_cap_and_the_time_cap_each_stop_a_run_on_their_own` makes each of the other two caps fire alone and name itself. |
| 4 | You kill the process (`kill -9`) at five different points during booking tasks, restart each time, and the calendar holds exactly the events the tasks expect, none of them twice. | `make test-integration`; `test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice` | Each point (`run_created`, `after_step`, `after_proposal`, `after_write_before_checkpoint`) is a real `os.kill(os.getpid(), SIGKILL)` inside the agent process, enabled by the `FAILPOINT` variable; the fifth task runs clean. After each resume the test counts events over HTTP and runs the double-booking overlap query from `sql/calendar/003_queries.sql`: five new events, zero overlaps. `test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume` covers the move, which is two writes. The in-process variants are in `test_a_crash_at_any_point_then_a_resume_books_exactly_one_event`. |
| 5 | Across ten fact-and-task pairs, a fact told in one session is applied correctly in a later one, and after a changed preference the old fact is no longer recalled. | `make test`; `tests/unit/application/test_memory_and_task_runner.py::test_a_fact_told_in_an_earlier_session_decides_where_the_meeting_lands`; `tests/unit/domain/test_calendar_memory_budget.py::test_a_changed_preference_replaces_the_old_fact_instead_of_sitting_beside_it` | Ten tasks come with facts (for example "No meetings before 15"). For each, the end state with the fact is the expected one and the end state without the fact is not, so the fact is what moved the booking. `t-book-05` is told "no meetings before 9" and later "nothing before 11 from now on": the booking lands at 11:30, and the memory table holds one fact for that topic (a new fact replaces the old in storage; recall tests check the table, not only the ranking). `agent forget` deletes a person's facts and the test checks storage. |
| 6 | All 30 tasks reach their expected end state, the report shows the pass rate per task across the three runs, and the audit log shows no write without an approval. | `make tasks`; `tests/e2e/test_lesson_scenario.py` (`make test-e2e`) | `tasks passed: 90/90 attempts (30 tasks x 3 runs)`, `writes without an approval: 0`, one row per task with its pass rate. Passing means the calendar's real active events equal the seeded events with the task's changes applied, queried from the service, never read from the agent's reply. The four impossible tasks pass when the calendar is unchanged; three of them end `done` with no proposal (two people outside the calendar, a Saturday) and one, a slot after closing time that the task will not give up on, runs to the step cap. The task runner approves only the changes a task expects; `approvals granted: 78, rejected: 0` on the stand-in model. A model that proposes a wrong write would be rejected and counted. |
| 7 | The Java version passes the same 30 tasks and the five-kill crash test with no double booking. | not built | See "Stretch goals and what is not built". |

Lines 1 to 6 need no key. Line 6 on the stand-in model proves the harness; running the same 30 tasks against a real model needs a key or a local server (`MODEL_PROVIDER=anthropic` or `openai-compatible`), and its result is not recorded here.

## Stretch goals and what is not built

| Stretch (from the lesson) | Built? |
| --- | --- |
| The Java version on Spring AI, same service, same tasks, same crash test (the lesson's step 7) | **No.** The calendar service speaks plain HTTP and the task file is JSON Lines, so a Java agent can run against both unchanged. The two things to match are the idempotency key (`sha256("<run id>:<step>")`, with `:cancel` and `:book` suffixes for a move) and the proposal digest, both documented in [ARCHITECTURE.md](ARCHITECTURE.md). |
| Let an approval wait a day | Mostly. The pending proposal is stored; stop the process, run `agent approve` later and `agent resume`. There is no expiry for old proposals. |
| A memory deletion request with a test that the facts are gone from recall and from storage | **Yes.** `agent forget <person>`; `test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten` and the agent-level test check the table. |
| Trace each run with one span per step and tool call | No. `run_steps` holds one row per step; adding spans is described in ARCHITECTURE.md. |

## What is simplified for teaching

- The model is a deterministic stand-in by default (see the top of this file); the Claude and local adapters are real code with no recorded live result.
- SQLite on one machine for both the calendar and the agent's checkpoints; a shared database would let any worker resume any run.
- Approvals are decided on the command line, and a proposal does not expire.
- Working hours are 09:00 to 17:00 on weekdays, one time zone, no recurring events, no rooms.
- Memory facts are parsed by rules from a few sentence shapes ("nothing before 10", "no meetings after 4pm", "no meetings on Fridays", "Fridays are fine again"), not extracted by a model.
- A move is a cancel and a book, two writes with two keys, because the calendar has the four endpoints the lesson lists.
- The reset endpoint used by the task runner is off unless `CALENDAR_ALLOW_RESET=on`.

## Project structure

```text
src/scheduling_agent/
  domain/            slots and working hours, proposals and their digest, the idempotency key, budgets, memory facts
                     and their write policy, the run state, tasks and end-state comparison, llm value objects, named
                     errors. Depends on nothing but the standard library.
  application/       the agent loop, the tool box (reads, proposals, the approval gate), memory service, the task
                     runner, and the ports (ChatModel, CalendarPort, ApprovalStore, CheckpointStore, AuditLog,
                     MemoryStore, Embedder, FailPoints, Clock). Depends on domain only.
  infrastructure/    SQLite calendar and agent databases, the HTTP calendar client, the scripted stand-in model, the
                     recorded/recording, OpenAI-compatible and Claude clients, retry, failpoints, settings, logfmt
                     logging, signals. Depends on application and domain.
  interfaces/        the `agent` command and the calendar HTTP service (`calendar-service`). Nothing depends on it.
tests/
  unit/              domain, application (fake ports), infrastructure (in-memory SQLite, mock HTTP), CLI.
  integration/       the calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes.
  e2e/               the 30 tasks three times through the real HTTP service.
  live/              opt-in tests against a real model (make test-live).
  fixtures/embeddings/   20 recorded vectors of nomic-embed-text for the remembered facts.
sql/calendar/        001_schema, 002_seed (five people, two weeks of meetings), 003_queries (overlap check and more).
sql/agent/           001_schema (runs, steps, approvals, audit, memory), 003_queries (unfinished runs, pending, audit).
data/                tasks.jsonl (30 tasks with their expected end state).
prompts/             agent/v1.md and CHANGELOG.md.
scripts/             make_calendar_seed.py and make_tasks.py (regenerate the data), pull_model.sh.
docs/adr/            six decision records.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter. A second contract forbids `domain` and `application` from importing `anthropic`, `httpx`, `openai` or any HTTP framework.

## Troubleshooting

- **`address already in use` on `make up`:** another process holds port 8090; set `CAL_PORT=8091 make up` or stop it. `make down` stops the service this repository started.
- **`agent: ... connection refused`:** the calendar service is not running; `make up`.
- **`RecordingMissing` or a missing embedding:** the remembered fact text changed, so the recorded vector no longer matches. Run `make record` with ollama serving `nomic-embed-text`.
- **A run is `awaiting_approval` and exits with code 5:** that is the gate working; `agent pending`, then `agent approve <id> --resume`.

## Verification notes

Verified on 2026-10-27 with `make up`, `make run`, `make test`, `make lint`, `make audit` and `make down`, in the repository and again in a fresh clone.

- **Timing figures** (latencies, durations, the cost-versus-latency ratios) were recorded or measured on a machine whose load average was between 35 and 180, so they support ratios, not service levels. Rerun for clean figures: `make record`.
- **Docker:** the calendar image built and answered `/health` on 2026-10-27. Nothing is pending.

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
