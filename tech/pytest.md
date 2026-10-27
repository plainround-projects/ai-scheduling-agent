# pytest

## What it is

A **test** is a small program that runs a piece of your code and checks that it did what you expect. **pytest** is the program that finds those tests, runs them, and reports which passed and which failed. A test is an ordinary function whose name starts with `test_`; it uses `assert` to state a fact. If every assert holds, the test passes.

Automated tests matter because code changes. Running them after every change tells you at once if something that used to work has broken.

## Why this repository uses it

The repository's claims ("the estimate is within a few percent of the bill", "a killed process resumes without paying twice", "the refund cannot be applied twice") are only believable if a test proves each one. pytest keeps the tests short, shows clear failure messages, and has a rich set of fixtures for temporary folders, fake environments and captured output. Markers let the same suite hold fast offline tests, tests that start real processes, and opt-in tests that call a real model.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/` | 134 test functions in unit, integration and end-to-end groups |
| `tests/conftest.py` | fixtures shared by every test |
| `pyproject.toml` | `[tool.pytest.ini_options]`: where tests live, default options and markers |
| `Makefile` | `test`, `test-integration`, `test-e2e`, `test-live` |
| `.github/workflows/ci.yml` | `make check` runs the whole offline suite |

## How it works underneath

**Collection.** pytest walks `testpaths`, imports every file named `test_*.py`, and collects every function named `test_*` (and methods of classes named `Test*`). It builds the list of tests before running any.

**Assertion rewriting.** When pytest imports a test file it rewrites the plain `assert` statements so that a failure shows the values on both sides. You write `assert a == b`; pytest prints what `a` and `b` were.

**Fixtures by name.** For each test pytest looks at the parameter names, finds fixtures with those names (in the test file, then `conftest.py` files from the nearest folder upward, then built-in and plugin fixtures), runs them, and passes the results in. A fixture with a `yield` runs the code after the `yield` as cleanup when the test ends.

**Exit codes.** pytest ends with 0 if all tests passed, 1 if some failed, 2 if the run was interrupted, 3 for an internal error, 4 for a usage error and 5 if no tests were collected. `make` stops on any non-zero code.

**Plugins.** pytest finds installed plugins by name; `pytest-cov` adds the `--cov` options (see `coverage.md`).

## Walkthrough of this repository's use

### The settings

The pytest table of `pyproject.toml` is explained line by line in `pyproject-toml.md`. In short: `testpaths` makes pytest look only in `tests/`; `addopts` is added to every run; here it is `-ra --strict-markers -m 'not live'`; `markers` declares the labels below. Because `--strict-markers` is on, a typo such as `@pytest.mark.integraton` is an error and not a silently ignored label.

### Markers (labels on tests)

A **marker** is a label put on a test with `@pytest.mark.NAME` (or on a whole file with `pytestmark = pytest.mark.NAME`). `-m EXPRESSION` selects tests by label. This repository declares:

- `integration`: runs the calendar service and the agent as real processes, including SIGKILL crashes. Used by 1 test file(s).
- `e2e`: the lesson's scenario end to end with the recorded model. Used by 1 test file(s).
- `live`: calls a real model; needs a key or a local server, run by `make test-live` only. Used by 1 test file(s).

The Makefile uses them: `make test` runs with the default options above (the marker filter in `addopts` leaves out the labels it names); `make test-integration` runs `-m integration`; `make test-e2e` runs `-m e2e`; `make test-live` runs `-m live` and is never part of `make check`.

### How many tests there are

134 test functions (a parametrized test counts once here; pytest reports each parameter row as its own test), by folder:

| Folder | Test functions |
| --- | --- |
| `tests/e2e` | 1 |
| `tests/integration` | 6 |
| `tests/live` | 2 |
| `tests/unit/application` | 29 |
| `tests/unit/domain` | 25 |
| `tests/unit/infrastructure` | 71 |

### Every kind of test construct used here, with a real example

#### A plain test

A test is a function whose name starts with `test_`. It sets something up, runs the code being tested, and uses `assert` to state what must be true. If an `assert` is false, pytest marks the test failed and prints both sides of the comparison.

From this repository, `tests/unit/application/test_memory_and_task_runner.py`, lines 14 to 22:

```python
def test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten():
    kit = build_kit()
    assert kit.memory.remember("alice", "I like coffee", "s1") is None
    assert kit.memory.facts() == []
    kit.memory.remember("alice", "nothing before 10", "s1")
    kit.memory.remember("bob", "nothing before 11", "s1")
    assert len(kit.memory.facts()) == 2
    assert kit.memory.forget("alice") == 1
    assert [f.person for f in kit.memory.facts()] == ["bob"]
```

#### Fixtures

A **fixture** is a function marked `@pytest.fixture` that builds something tests need (a sample object, a temporary folder, a fake clock). A test asks for it by naming it as a parameter, and pytest calls the fixture and passes the result in. Fixtures defined in `conftest.py` are available to every test below that folder.

From this repository, `tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 26 to 30:

```python
@pytest.fixture
def db():
    connection = connect(":memory:")
    apply_sql(connection, REPO / "sql/agent/001_schema.sql")
    return AgentDb(connection, new_id=iter(f"{i:04d}" for i in range(1, 99)).__next__)
```

#### Parametrized tests

`@pytest.mark.parametrize("names", [values...])` runs the same test function once for each row of values. Each run is reported as its own test.

From this repository, `tests/unit/application/test_memory_and_task_runner.py`, lines 140 to 146:

```python
@pytest.mark.parametrize("task", FACT_TASKS, ids=lambda t: t.id)
def test_a_fact_told_in_an_earlier_session_decides_where_the_meeting_lands(task):
    """The ten fact-and-task pairs: with the fact the end state is the expected one; without it, it is not."""
    task_runner, _ = runner()
    assert task_runner.run_once(task, 1).passed
    forgotten = dataclasses.replace(task, facts=())
    assert not task_runner.run_once(forgotten, 1).passed
```

#### `tmp_path`: a private temporary folder

A built-in fixture. pytest creates a new empty folder for the test and passes it as a `Path`. Tests write their files there, so they never touch the real `data/` or `out/` folders.

From this repository, `tests/unit/infrastructure/test_recording.py`, lines 15 to 22:

```python
def test_recording_then_replaying_returns_the_same_response(tmp_path):
    path = tmp_path / "r.jsonl"
    live = ScriptedModel(lambda r: ("live answer", 12, 4))
    recorder = RecordingChatModel(live, RecordingStore(path), {"provider": "test"})
    first = recorder.complete(request())
    replay = RecordedChatModel(RecordingStore(path))
    assert replay.complete(request()) == first
    assert len(live.requests) == 1
```

#### `pytest.raises`: checking that an error is raised

`with pytest.raises(SomeError):` passes if the code inside raises that error and fails if it does not.

From this repository, `tests/unit/application/test_tools_and_agent.py`, lines 129 to 130:

```python
    with pytest.raises(ApprovalError, match="already rejected"):
        kit.approvals.decide(approval.id, True, "test", FixedClock().now())
```

## Try it yourself

1. Which pytest is installed.

```bash
.venv/bin/python -m pytest --version
```

What you should see (captured from this repository):

```text
pytest 9.1.1
```

2. Collect without running: how many tests the default options select. The last line shows how many were left out by the marker filter.

```bash
.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/infrastructure/test_resilience_logging_factory.py::test_info_logs_of_a_failed_call_never_carry_the_prompt_text

161/163 tests collected (2 deselected) in N.NNs
```

3. The markers this project declares, as pytest prints them.

```bash
.venv/bin/python -m pytest --markers 2>&1 | grep -E '^@pytest.mark.(integration|e2e|live)'
```

What you should see (captured from this repository):

```text
@pytest.mark.integration: runs the calendar service and the agent as real processes, including SIGKILL crashes
@pytest.mark.e2e: the lesson's scenario end to end with the recorded model
@pytest.mark.live: calls a real model; needs a key or a local server, run by `make test-live` only
```

4. Run only the domain unit tests. `-q` is quiet, and the last line is the summary with the number of tests and the time.

```bash
.venv/bin/python -m pytest tests/unit/domain -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
................................                                         [100%]
32 passed in N.NNs
```

5. The live tests exist but are deselected by default; with `-m live` they are collected.

```bash
.venv/bin/python -m pytest -m live --collect-only -q 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/live/test_live_models.py::test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects

2/163 tests collected (161 deselected) in N.NNs
```

## Mistakes people make

- **A test that depends on another test.** Tests may run in any order. Each test here builds its own data (fixtures, `tmp_path`).
- **Tests that touch the real files or network.** They would pass or fail by chance. The offline suite uses `tmp_path`, recorded answers and local ports.
- **Assertions that can never fail.** `assert x` on a non-empty list is always true. The tests compare exact values.
- **Typos in marker names.** `--strict-markers` turns them into errors.
- **Running live tests by accident.** `addopts` excludes them (`-m 'not live'`); only `make test-live` overrides it.
- **Testing implementation details.** Tests call the public functions and check results, so the code behind them can change.

## Check yourself

1. What makes a function a test for pytest?

   *Answer:* Its name starts with `test_` and it is in a file named `test_*.py` under `testpaths`.

2. How does a test get a fixture?

   *Answer:* By naming it as a parameter; pytest calls the fixture and passes the result.

3. What does `-m 'not live'` do?

   *Answer:* Skips every test marked `live`.

4. What does `tmp_path` give a test?

   *Answer:* A new empty temporary folder that is private to that test.

5. Why is `--strict-markers` on?

   *Answer:* So an unknown or misspelled marker is an error instead of being silently ignored.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned in the lock file; the commands above were run with it).
