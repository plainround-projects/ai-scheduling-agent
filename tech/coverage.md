# Test coverage (coverage.py and pytest-cov)

## What it is

**Test coverage** measures how much of your code the tests actually ran. **coverage.py** watches Python execute and records every line that ran. **pytest-cov** is a plugin that connects it to pytest. A coverage report lists each file, how many statements it has, how many were never run, and the percentage that did run.

100 percent coverage does not prove the code is right (a test can run a line without checking its result), but a line with no coverage is a line no test has ever looked at.

## Why this repository uses it

The domain and application code carry the project's decisions (pricing, estimates, refunds, state transitions). A hard floor of 95 percent on those two folders means nobody can add untested decision logic and still pass `make test`. It turns "we have tests" into a rule the build enforces.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | `[tool.coverage.run]` and `[tool.coverage.report]` |
| `Makefile` | `test` runs `pytest --cov=...` and then `coverage report ... --fail-under=95` |
| `.coverage` | the data file coverage writes (ignored by git) |
| `.gitignore` | lists `.coverage` |

## How it works underneath

Python lets a tool register a *trace function* that is called on every line executed. coverage.py uses a fast compiled tracer to record, for each file, which line numbers (and which pairs of lines, for branches) were visited. When the process ends it writes the visited set to `.coverage`, a SQLite database. `coverage report` reads that database, compares it to the list of executable lines it finds by analysing each source file, and prints the difference.

`--fail-under=95` makes `coverage report` exit with status 2 when the total is under 95. Total percentage with branches on is `(statements run + branches taken) / (statements + branches)`.

## Walkthrough of this repository's use

### The settings in `pyproject.toml`

`pyproject.toml`, lines 73 to 75:

```toml
[tool.coverage.run]
source = ["scheduling_agent"]
branch = true
```

`pyproject.toml`, lines 77 to 79:

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

- `source = ["scheduling_agent"]`: measure only this package. Without it coverage would also report the test files and installed libraries.
- `branch = true`: also track every *branch*. For `if x: A else: B`, line coverage says "A ran"; branch coverage also says whether the `else` path ever ran. A line with an `if` and no test for the false case counts as partially covered.
- `show_missing = true`: the report gets a `Missing` column with line numbers that never ran (and `12->15` for branches never taken).
- `skip_covered = false`: files with 100 percent are still listed.

### The two Makefile lines

`Makefile`, lines 82 to 84:

```make
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=scheduling_agent --cov-report=term
	$(PY) -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95
```

1. `pytest --cov=scheduling_agent --cov-report=term`: the `--cov` option comes from the plugin `pytest-cov`. It starts coverage measurement before the first test and, at the end, prints the table in the terminal (`term`). The data is saved in a file named `.coverage` (a SQLite database; it is in `.gitignore`).
2. `python -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95`: reads `.coverage` again, prints a table for **only** the `domain` and `application` folders (`--include` takes patterns separated by commas), and returns a failure exit code if the total is below 95 percent. This is the quality gate: the core logic and the use cases must stay almost fully tested. Adapters (`infrastructure`) and the command-line wiring (`interfaces`) are tested too, but without a hard percentage because some of their code only runs against real services.

The gate sits in `make test`, which `make check` and the CI job `check` call.

## Try it yourself

1. The installed coverage.py.

```bash
.venv/bin/python -m coverage --version | head -1
```

What you should see (captured from this repository):

```text
Coverage.py, version 7.17.0 with C extension
```

2. The gate itself, run on the data file left by the last `make test`. The last line is the total for the two folders.

```bash
.venv/bin/python -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95 2>&1 | tail -6
```

What you should see (captured from this repository):

```text
src/scheduling_agent/domain/proposals.py                26      0      0      0   100%
src/scheduling_agent/domain/retrieval.py                 7      0      0      0   100%
src/scheduling_agent/domain/run.py                      38      0      0      0   100%
src/scheduling_agent/domain/tasks.py                    43      0      8      0   100%
------------------------------------------------------------------------------------------------
TOTAL                                                  784      4    116      3    99%
```

3. Raise the bar to 100 percent and the same command fails (exit code 2), which is what a broken gate looks like.

```bash
.venv/bin/python -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=100 >/dev/null 2>&1; echo "exit code: $?"
```

What you should see (captured from this repository):

```text
exit code: 2
```

4. The data file exists after a test run (its size will differ on your machine).

```bash
ls -l .coverage | awk '{print $5, $9}'
```

What you should see (captured from this repository):

```text
180224 .coverage
```

## Mistakes people make

- **Chasing 100 percent with meaningless tests.** A line that runs but is never checked counts as covered. The tests here assert on results.
- **Measuring the tests themselves.** `source = ["scheduling_agent"]` limits measurement to the package under test.
- **Ignoring branches.** `branch = true` shows an `if` whose `else` was never tried.
- **Forgetting the gate runs after pytest.** `coverage report` needs the `.coverage` file that the pytest run just wrote; running it first reports nothing.
- **Committing `.coverage`.** It is a binary local file; it is in `.gitignore`.

## Check yourself

1. What does `branch = true` add?

   *Answer:* Tracking of which way each `if` or loop went, not just which lines ran.

2. What makes `make test` fail below 95 percent?

   *Answer:* `coverage report --fail-under=95` returns a non-zero exit code.

3. Why is the gate limited to `domain` and `application`?

   *Answer:* Those folders hold the decisions; adapters touch real services and are checked by integration tests.

4. Where does coverage store what it measured?

   *Answer:* In the `.coverage` file in the project folder.

5. What does the `Missing` column list?

   *Answer:* The line numbers (and branch jumps) that no test reached.

## Further reading

- coverage.py documentation, https://coverage.readthedocs.io/ and pytest-cov, https://pytest-cov.readthedocs.io/ (coverage 7.17.0 and pytest-cov 7.1.0 are pinned in the lock file).
