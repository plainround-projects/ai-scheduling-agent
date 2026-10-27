# Make and the Makefile

## What it is

**make** is a program that runs named recipes. You give it a file called `Makefile`. In that file you write *targets* (a name, followed by a colon), the *prerequisites* the target needs (other targets or files), and a *recipe* (the shell commands that make the target). When you type `make test` in a terminal, make finds the target `test`, first brings its prerequisites up to date, then runs its commands one by one.

A **terminal** is the text window where you type commands. A **shell** is the program inside the terminal that reads what you type and starts other programs. A **command** is one line you give the shell. A **target** is the thing you ask make to produce, such as `test`. A **recipe** is the list of commands under a target. A **prerequisite** is something that must exist or be current before the recipe runs.

make was written in 1976 to rebuild programs from source files, and it is still used because it is small and installed almost everywhere. In this repository it does not compile anything. It is a *menu of commands*: it gives every task a short, memorable name.

## Why this repository uses it

A new person cannot guess which ten commands to type, in which order, with which flags. The Makefile writes them down once, so `make up`, `make run`, `make test`, `make lint` and `make down` mean the same thing on every computer and in the continuous-integration job. It also encodes *order*: `make test` first makes sure the virtual environment exists, because the target depends on a stamp file; you cannot forget the install step.

The Makefile also keeps the long environment settings (which model to use, where recordings live, which port) in one place, so the commands in the README stay short.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | the whole file: 21 targets that wrap every command in the project |
| `.github/workflows/ci.yml` | runs `make check` and `make audit` on every push |
| `.editorconfig` | tells editors to use real tab characters in the Makefile (`[Makefile]` section) |
| `README.md` | tells the reader to run `make up`, `make run`, `make test` |

## How it works underneath

**How make reads the file.** make reads the whole Makefile first. It builds a graph: each target points at its prerequisites. Then it walks the graph from the target you asked for. For a target that is the *name of a file*, it compares modification times: if the file exists and is newer than every prerequisite, nothing needs doing; if it is missing or older, the recipe runs. This is what the stamp rule in this repository uses: `.venv/.installed` is rebuilt only when `requirements-dev.lock` or `pyproject.toml` has changed since it was last touched.

**Phony targets.** `test`, `lint` and `down` are not files. The `.PHONY` line says so; make then always runs their recipes.

**Each recipe line is its own shell.** make starts a new `/bin/sh -c "..."` for every line of a recipe. A `cd` on one line is forgotten by the next line. That is why long jobs in this Makefile are written on one line with `;` or `&&` between the parts, or with a trailing backslash that joins physical lines.

**Variables.** `NAME = value` is looked up lazily every time it is used. `NAME := value` is worked out once, right away. `NAME ?= value` sets it only if it is not already set (from the command line or the environment). `$(NAME)` pastes the value. Inside a recipe a single `$` belongs to make, so a `$` meant for the shell is written `$$`.

**Special characters in front of a recipe line.** `@` means do not print the command before running it. `-` means ignore a failure and keep going.

**Exit codes.** Every program ends with a number: `0` means success, anything else means failure. make stops at the first recipe line that returns non-zero and returns failure itself, which is how `make check` makes a build go red.

**The required tab.** A recipe line must start with a real tab character, not spaces. If it does not, GNU Make says `missing separator`. This repository's `.editorconfig` has `[Makefile]` / `indent_style = tab` so editors keep the tabs.

## Walkthrough of this repository's use

`Makefile`, the whole file, block by block. Under each block, every line is explained.

```make
# make up | run | test | test-integration | test-live | lint | down      (make help lists everything)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
AGENT := $(VENV)/bin/agent
STAMP := $(VENV)/.installed
CAL_PORT ?= 8090
CAL_PID := out/calendar.pid
CAL_ENV := CALENDAR_DB=out/calendar.db CALENDAR_ALLOW_RESET=on HTTP_PORT=$(CAL_PORT) CALENDAR_URL=http://127.0.0.1:$(CAL_PORT)
LOCAL_MODEL ?= qwen2.5:1.5b
EMBED_MODEL ?= nomic-embed-text
```

- `# make up | run | test | test-integration | test-live | lint | down      (make help lists everything)`: A comment. make ignores everything after a `#`.
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: Sets `PYTHON` to the Python program used to make the virtual environment. `?=` means "set this only if it is not already set", so you can override it (`make PYTHON=python3.12 up`). `$(shell ...)` runs a shell command while make reads the file and pastes in what it prints. `command -v NAME` prints the full path of `NAME` if it exists and prints nothing (and fails) if not. The `||` means "if the left side failed, try the right side", so the line tries Python 3.13, then 3.12, then plain `python3`.
- `VENV := .venv`: Sets `VENV` to the name of the virtual-environment folder. `:=` means "work out the value now, once".
- `PY := $(VENV)/bin/python`: Sets `PY` to the Python program inside the virtual environment. `$(VENV)` is replaced by `.venv`, so this is `.venv/bin/python`.
- `AGENT := $(VENV)/bin/agent`: Sets `AGENT` to `.venv/bin/agent`, the command-line program of this project that pip installed into the virtual environment (it is declared under `[project.scripts]` in `pyproject.toml`).
- `STAMP := $(VENV)/.installed`: Sets `STAMP` to `.venv/.installed`, an empty file that the install rule creates when it finishes. Its modification time records "the environment was installed at this moment".
- `CAL_PORT ?= 8090`: Sets `CAL_PORT` to `8090` unless you already set it: the port number (a numbered door on this computer that a program listens at) of the HTTP server.
- `CAL_PID := out/calendar.pid`: Sets `CAL_PID` to `out/calendar.pid`, the file where the background server's process id is saved so a later command can stop it. A process id (pid) is the number the operating system gives each running program.
- `CAL_ENV := CALENDAR_DB=out/calendar.db CALENDAR_ALLOW_RESET=on HTTP_PORT=$(CAL_PORT) CALENDAR_URL=http://127.0.0.1:$(CAL_PORT)`: Sets `CAL_ENV` to a list of NAME=value pairs. Other recipes put `$(CAL_ENV)` in front of a command, which gives that command these environment variables. The words of the form NAME=value in front of the program name set environment variables for that one command only: CALENDAR_DB (the path of the SQLite file holding the calendar); CALENDAR_ALLOW_RESET (`on` enables the reset endpoint of the calendar service (demos and the task runner only)); HTTP_PORT (the port number the HTTP server listens on); CALENDAR_URL (the web address of the calendar service).
- `LOCAL_MODEL ?= qwen2.5:1.5b`: Sets `LOCAL_MODEL` to `qwen2.5:1.5b` unless you already set it. This is the name of a small open-weight model that `ollama` can download (the part before the colon is the model family, the part after it is the size variant).
- `EMBED_MODEL ?= nomic-embed-text`: Sets `EMBED_MODEL` to `nomic-embed-text` unless you already set it. This is the name of a small open-weight model that `ollama` can download (the part before the colon is the model family, the part after it is the size variant).

```make
-include .env
export
```

- `-include .env`: Reads the file `.env` if it exists (a plain `include` would stop with an error when it is missing; the leading `-` means "if it is missing, carry on"). The file holds `NAME=value` lines you copied from `env.example`.
- `export`: Passes every make variable to the programs that make starts, as environment variables. Together with the line above, a value written in `.env` reaches the Python program.

```make
.PHONY: help install up db calendar-up calendar-down run demo tasks models record lint format test test-integration test-e2e \
        test-live audit check down clean
```

- `.PHONY: help install up db calendar-up calendar-down run demo tasks models record lint format test test-integration test-e2e test-live audit check down clean`: Declares these names "phony": they are the names of actions, not of files. Without this, a file or folder that happens to be called `test` or `clean` would make make think the target was already up to date and skip it.

```make
help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- `help: ## list the targets`: Defines the target `help`. It has no prerequisites. The text after `##` (`list the targets`) is the help text that `make help` prints.
- `grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: The leading `@` tells make not to print the command before running it. Prints the help list. `grep -E` searches for lines matching a pattern: here, lines that start with a target name made of lowercase letters and hyphens, then a colon, and contain `## `. `$(MAKEFILE_LIST)` is the name of this Makefile. The `|` (pipe) hands grep's output to `sed -E 's/:.*## /\t/'`, which replaces everything from the colon through `## ` with a tab character, leaving `target<TAB>help text`. The next `|` hands that to `sort`, which puts the lines in alphabetical order.

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(STAMP): requirements-dev.lock pyproject.toml`: Defines a rule whose target is a file, the stamp (`.venv/.installed`). Its prerequisites, which make brings up to date before running the recipe: the file `requirements-dev.lock`; the file `pyproject.toml`. If the stamp is missing, or older than either file, make runs the recipe below; otherwise it does nothing, which makes every later `make` command start fast.
- `$(PYTHON) -m venv $(VENV)`: Creates the virtual environment: a private folder `.venv` holding its own copy of the Python program and its own empty place for installed packages. `-m venv` means "run the module named `venv` that ships with Python".
- `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`: Installs every package named in `requirements-dev.lock` into the virtual environment. `-q` is quiet. `--require-hashes` makes pip refuse any file whose fingerprint (a sha256 hash) is not listed in the lock file, and also refuse any package that is not pinned to an exact version. `-r FILE` means "read the list of packages from this file".
- `$(VENV)/bin/pip install -q --no-deps -e .`: Installs this project itself. `.` means "the project in this folder". `-e` (editable) links the code in `src/` instead of copying it, so editing a file takes effect at once. `--no-deps` stops pip from looking for dependencies again: the lock file already installed exactly the versions wanted.
- `touch $@`: Creates the stamp file, or updates its modification time. `$@` is make's automatic name for "the target of this rule", here `.venv/.installed`. The stamp is only touched if every line above succeeded, because make stops at the first failing line.

```make
install: $(STAMP) ## create .venv from the lock file
```

- `install: $(STAMP) ## create .venv from the lock file`: Defines the target `install`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`create .venv from the lock file`) is the help text that `make help` prints.

```make
up: $(STAMP) calendar-up ## create the databases and start the calendar service on :8090 (HTTP over SQLite)
```

- `up: $(STAMP) calendar-up ## create the databases and start the calendar service on :8090 (HTTP over SQLite)`: Defines the target `up`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first; the target `calendar-up`, which starts the calendar service. The text after `##` (`create the databases and start the calendar service on :8090 (HTTP over SQLite)`) is the help text that `make help` prints.

```make
db: $(STAMP) ## create out/calendar.db and out/agent.db from the numbered SQL files (safe to repeat)
	mkdir -p out
	sqlite3 out/calendar.db < sql/calendar/001_schema.sql
	sqlite3 out/calendar.db "SELECT count(*) FROM people" | grep -q '^0$$' && sqlite3 out/calendar.db < sql/calendar/002_seed.sql || true
	sqlite3 out/agent.db < sql/agent/001_schema.sql
	@echo "calendar: $$(sqlite3 out/calendar.db 'select count(*) from events') events for $$(sqlite3 out/calendar.db 'select count(*) from people') people"
```

- `db: $(STAMP) ## create out/calendar.db and out/agent.db from the numbered SQL files (safe to repeat)`: Defines the target `db`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`create out/calendar.db and out/agent.db from the numbered SQL files (safe to repeat)`) is the help text that `make help` prints.
- `mkdir -p out`: Creates the `out` folder. `-p` means "no error if it already exists".
- `sqlite3 out/calendar.db < sql/calendar/001_schema.sql`: Runs the SQL file against the SQLite database file `out/calendar.db`, creating it if needed. The file only creates tables that do not exist yet, so repeating it is safe.
- `sqlite3 out/calendar.db "SELECT count(*) FROM people" | grep -q '^0$$' && sqlite3 out/calendar.db < sql/calendar/002_seed.sql || true`: Loads the seed data only if the `people` table is empty. The first `sqlite3` prints the number of rows; `grep -q '^0$$'` checks silently (`-q`) whether the output is exactly `0` (`$$` is a literal `$` to the shell: end of line). If so (`&&`), the seed file runs. The `|| true` at the end makes the whole line succeed even when the table was not empty, so make does not stop.
- `sqlite3 out/agent.db < sql/agent/001_schema.sql`: Creates the tables of the agent's own database `out/agent.db`.
- `echo "calendar: $$(sqlite3 out/calendar.db 'select count(*) from events') events for $$(sqlite3 out/calendar.db 'select count(*) from people') people"`: The leading `@` tells make not to print the command before running it. Prints how many events and people the calendar database holds, by running two small SQL queries and pasting their answers into the text.

```make
calendar-up: db ## start the calendar service in the background (writes out/calendar.pid)
	@if [ -f $(CAL_PID) ] && kill -0 $$(cat $(CAL_PID)) 2>/dev/null; then echo "calendar service already running (pid $$(cat $(CAL_PID)))"; \
	else $(CAL_ENV) nohup $(VENV)/bin/calendar-service serve > out/calendar.log 2>&1 & echo $$! > $(CAL_PID); fi
	@for i in $$(seq 1 40); do curl -sf http://127.0.0.1:$(CAL_PORT)/health >/dev/null && break || sleep 0.25; done; curl -sf http://127.0.0.1:$(CAL_PORT)/health && echo
```

- `calendar-up: db ## start the calendar service in the background (writes out/calendar.pid)`: Defines the target `calendar-up`. Its prerequisites, which make brings up to date before running the recipe: the target `db`, which creates the databases. The text after `##` (`start the calendar service in the background (writes out/calendar.pid)`) is the help text that `make help` prints.
- `if [ -f $(CAL_PID) ] && kill -0 $$(cat $(CAL_PID)) 2>/dev/null; then echo "calendar service already running (pid $$(cat $(CAL_PID)))"; else $(CAL_ENV) nohup $(VENV)/bin/calendar-service serve > out/calendar.log 2>&1 & echo $$! > $(CAL_PID); fi`: The leading `@` tells make not to print the command before running it. Starts the calendar service unless it is already running. `[ -f FILE ]` is true if the pid file exists. `kill -0 PID` sends no signal at all; it only checks that a process with that id exists (and fails if not). `$$(cat $(CAL_PID))` reads the pid out of the file. If both hold, it prints that the service is running. Otherwise (`else`) it starts the service with the calendar variables set: `nohup` keeps the program alive after the terminal closes; `> out/calendar.log 2>&1` sends both normal output and error output to a log file; the final `&` starts it in the background; `echo $$! > FILE` saves `$!` (the pid of the background program just started) into the pid file. `fi` ends the `if`. The line is written as two physical lines joined by a backslash.
- `for i in $$(seq 1 40); do curl -sf http://127.0.0.1:$(CAL_PORT)/health >/dev/null && break || sleep 0.25; done; curl -sf http://127.0.0.1:$(CAL_PORT)/health && echo`: The leading `@` tells make not to print the command before running it. Waits up to ten seconds (40 tries, a quarter of a second apart) for the service to answer at its `/health` address. `curl -sf` fetches a web address: `-s` is silent and `-f` makes curl fail (non-zero exit code) when the server answers with an error status. Once it works, the loop stops, the last `curl` prints the health answer, and `echo` adds a final newline.

```make
calendar-down: ## stop the calendar service (SIGTERM: in-flight requests finish)
	@if [ -f $(CAL_PID) ]; then kill $$(cat $(CAL_PID)) 2>/dev/null || true; rm -f $(CAL_PID); fi
```

- `calendar-down: ## stop the calendar service (SIGTERM: in-flight requests finish)`: Defines the target `calendar-down`. It has no prerequisites. The text after `##` (`stop the calendar service (SIGTERM: in-flight requests finish)`) is the help text that `make help` prints.
- `if [ -f $(CAL_PID) ]; then kill $$(cat $(CAL_PID)) 2>/dev/null || true; rm -f $(CAL_PID); fi`: The leading `@` tells make not to print the command before running it. Stops the service if a pid file exists. `kill PID` sends the SIGTERM signal, a polite request to finish and exit (in-flight requests complete first). `2>/dev/null || true` hides an error message and keeps going when the process is already gone. Then the pid file is removed.

```make
# One task with the scripted stand-in model: the write waits for a person; --auto-approve plays the person.
demo: up ## book a meeting end to end: propose, approve, write, final answer (and a replay of the same request)
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) tell alice "I never want meetings before 10" --session s1
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) run "Book a 30-minute meeting with alice and bob on 2026-11-03." --run-id demo-1 || [ $$? -eq 5 ]
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) pending
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) resume demo-1 --auto-approve
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) audit --run demo-1
```

- `# One task with the scripted stand-in model: the write waits for a person; --auto-approve plays the person.`: A comment. make ignores everything after a `#`.
- `demo: up ## book a meeting end to end: propose, approve, write, final answer (and a replay of the same request)`: Defines the target `demo`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`book a meeting end to end: propose, approve, write, final answer (and a replay of the same request)`) is the help text that `make help` prints.
- `$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) tell alice "I never want meetings before 10" --session s1`: Runs the `agent tell` command against the demo database with the calendar variables in front. `tell` stores a remembered fact for a person in the agent's long-term memory.
- `$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) run "Book a 30-minute meeting with alice and bob on 2026-11-03." --run-id demo-1 || [ $$? -eq 5 ]`: Runs a task to book a 30-minute meeting. The `||` means "if that failed, try the right side", and `[ $$? -eq 5 ]` is true when the exit code (`$?`) of the failed command equals 5. Exit code 5 is how the agent says "I am waiting for a person's approval", which is the expected state here, so make must not treat it as an error.
- `$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) pending`: Runs the `agent pending` command against the demo database with the calendar variables in front. `pending` lists the approvals waiting for a person.
- `$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) resume demo-1 --auto-approve`: Runs the `agent resume` command against the demo database with the calendar variables in front. `resume demo-1 --auto-approve` continues that run; `--auto-approve` plays the part of the person.
- `$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) audit --run demo-1`: Runs the `agent audit` command against the demo database with the calendar variables in front. `audit --run demo-1` prints the audit trail of that run.

```make
# The lesson's step 6: 30 tasks x 3 runs, each judged by the calendar's real end state.
tasks: up ## run the 30 tasks three times each against the calendar service and print the report
	$(CAL_ENV) $(AGENT) tasks --runs 3
```

- `# The lesson's step 6: 30 tasks x 3 runs, each judged by the calendar's real end state.`: A comment. make ignores everything after a `#`.
- `tasks: up ## run the 30 tasks three times each against the calendar service and print the report`: Defines the target `tasks`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`run the 30 tasks three times each against the calendar service and print the report`) is the help text that `make help` prints.
- `$(CAL_ENV) $(AGENT) tasks --runs 3`: Runs the 30 tasks three times each against the calendar service and prints the report.

```make
run: up ## the lesson's scenario: the demo, then the 30 tasks x 3 runs, then the service is left running
	$(MAKE) --no-print-directory demo
	$(MAKE) --no-print-directory tasks
```

- `run: up ## the lesson's scenario: the demo, then the 30 tasks x 3 runs, then the service is left running`: Defines the target `run`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`the lesson's scenario: the demo, then the 30 tasks x 3 runs, then the service is left running`) is the help text that `make help` prints.
- `$(MAKE) --no-print-directory demo`: Runs the target `demo` through a second make.
- `$(MAKE) --no-print-directory tasks`: Runs the target `tasks` through a second make.

```make
models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(LOCAL_MODEL)
	scripts/pull_model.sh $(EMBED_MODEL)
```

- `models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)`: Defines the target `models`. It has no prerequisites. The text after `##` (`download the pinned small open-weight models for recording and live-local runs (needs ollama)`) is the help text that `make help` prints.
- `scripts/pull_model.sh $(LOCAL_MODEL)`: Runs the shell script `scripts/pull_model.sh` with the model name as its first argument. The script downloads the model through ollama (see `bash.md`).
- `scripts/pull_model.sh $(EMBED_MODEL)`: Runs the download script for the embedding model.

```make
record: up ## record the memory embeddings by running the task set once with the local embedding model (needs make models)
	$(CAL_ENV) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) RECORD=on \
	  EMBEDDINGS_PATH=tests/fixtures/embeddings/nomic-embed-text.jsonl $(AGENT) tasks --runs 1
```

- `record: up ## record the memory embeddings by running the task set once with the local embedding model (needs make models)`: Defines the target `record`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`record the memory embeddings by running the task set once with the local embedding model (needs make models)`) is the help text that `make help` prints.
- `$(CAL_ENV) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) RECORD=on EMBEDDINGS_PATH=tests/fixtures/embeddings/nomic-embed-text.jsonl $(AGENT) tasks --runs 1`: Runs the task set once with the real embedding model and writes the vectors into the fixtures file. The words of the form NAME=value in front of the program name set environment variables for that one command only: EMBEDDER_PROVIDER (which embedding model turns text into vectors: `recorded` replays saved vectors, `openai-compatible` calls a local server); EMBED_MODEL (the embedding model id (`nomic-embed-text` makes 768-number vectors)); RECORD (`on` makes every live answer also get written into the recordings file, so the next run can replay it); EMBEDDINGS_PATH (the file or folder holding the recorded vectors).

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- `lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter`: Defines the target `lint`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`ruff check, ruff format check, mypy, import-linter`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check .`: Runs the ruff linter on every Python file under the current folder (`.`). A linter reads code without running it and reports mistakes and style problems. Exit code 0 means no problems.
- `$(VENV)/bin/ruff format --check .`: Asks ruff's formatter whether every file is already formatted the way it would format it. `--check` means "report, do not change anything"; a file that would change makes the command fail.
- `$(VENV)/bin/mypy`: Runs the mypy type checker. It needs no arguments because `pyproject.toml` lists the folders to check (`files = ["src", "tests"]`).
- `$(VENV)/bin/lint-imports`: Runs import-linter, which reads the contracts in `pyproject.toml` and fails if any module imports something it must not.

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `format: $(STAMP) ## apply ruff's formatting and safe fixes`: Defines the target `format`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`apply ruff's formatting and safe fixes`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check --fix .`: Runs the linter and lets it repair the problems that have a safe automatic fix (`--fix`).
- `$(VENV)/bin/ruff format .`: Rewrites every Python file into ruff's standard layout.

```make
# Unit, end-to-end and process tests, all offline. The process tests start the calendar service and kill the agent with SIGKILL.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=scheduling_agent --cov-report=term
	$(PY) -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95
```

- `# Unit, end-to-end and process tests, all offline. The process tests start the calendar service and kill the agent with SIGKILL.`: A comment. make ignores everything after a `#`.
- `test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)`: Defines the target `test`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`every offline test, with coverage (domain and application must stay at 95% or more)`) is the help text that `make help` prints.
- `$(PY) -m pytest --cov=scheduling_agent --cov-report=term`: Runs pytest as a module of the project's Python. `--cov=scheduling_agent` turns on coverage measurement for the package `scheduling_agent` and `--cov-report=term` prints the table in the terminal.
- `$(PY) -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95`: Prints the coverage table again, but only for the `domain` and `application` folders, and fails (non-zero exit code) if the total is under 95 percent. The quotes stop the shell from expanding the `*` itself.

```make
test-integration: $(STAMP) ## the calendar service and the agent as real processes, including the five SIGKILL crash points
	$(PY) -m pytest tests/integration -m integration
```

- `test-integration: $(STAMP) ## the calendar service and the agent as real processes, including the five SIGKILL crash points`: Defines the target `test-integration`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the calendar service and the agent as real processes, including the five SIGKILL crash points`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/integration -m integration`: Runs only the tests in `tests/integration`, and only those marked `integration` (`-m` selects by marker).

```make
test-e2e: $(STAMP) ## the 30 tasks through the real HTTP service
	$(PY) -m pytest tests/e2e -m e2e
```

- `test-e2e: $(STAMP) ## the 30 tasks through the real HTTP service`: Defines the target `test-e2e`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the 30 tasks through the real HTTP service`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/e2e -m e2e`: Runs only the tests in `tests/e2e`, and only those marked `e2e` (`-m` selects by marker).

```make
test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"
```

- `test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`: Defines the target `test-live`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"`: Runs only the live tests, which call a real model. The default options exclude them (`-m 'not live'`), so `-o addopts="..."` replaces the default options for this run.

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: Defines the target `audit`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`check the locked dependencies for known vulnerabilities`) is the help text that `make help` prints.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Checks every locked package against a database of known security problems. `--no-deps` means "do not work out dependencies again, trust the file"; `--disable-pip` means "do not run pip in a temporary environment"; `-r FILE` names the list to check.

```make
check: lint test ## format check, lint, types, import rules and every offline test
```

- `check: lint test ## format check, lint, types, import rules and every offline test`: Defines the target `check`. Its prerequisites, which make brings up to date before running the recipe: the target `lint`; the target `test`. The text after `##` (`format check, lint, types, import rules and every offline test`) is the help text that `make help` prints.

```make
down: calendar-down ## stop the calendar service and remove the databases and logs (out/)
	rm -rf out
```

- `down: calendar-down ## stop the calendar service and remove the databases and logs (out/)`: Defines the target `down`. Its prerequisites, which make brings up to date before running the recipe: the target `calendar-down`, which stops the calendar service. The text after `##` (`stop the calendar service and remove the databases and logs (out/)`) is the help text that `make help` prints.
- `rm -rf out`: Deletes the `out` folder and everything in it. `-r` means "including folders", `-f` means "no error if it is missing".

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
```

- `clean: down`: Defines the target `clean`. Its prerequisites, which make brings up to date before running the recipe: the target `down`.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage`: Deletes the virtual environment and the cache files the tools wrote. Everything here can be built again.

## Try it yourself

1. List every target with its help text. This prints the `##` comments; nothing is run.

```bash
make help
```

What you should see (captured from this repository):

```text
audit	check the locked dependencies for known vulnerabilities
calendar-down	stop the calendar service (SIGTERM: in-flight requests finish)
calendar-up	start the calendar service in the background (writes out/calendar.pid)
check	format check, lint, types, import rules and every offline test
db	create out/calendar.db and out/agent.db from the numbered SQL files (safe to repeat)
demo	book a meeting end to end: propose, approve, write, final answer (and a replay of the same request)
down	stop the calendar service and remove the databases and logs (out/)
format	apply ruff's formatting and safe fixes
help	list the targets
install	create .venv from the lock file
lint	ruff check, ruff format check, mypy, import-linter
models	download the pinned small open-weight models for recording and live-local runs (needs ollama)
record	record the memory embeddings by running the task set once with the local embedding model (needs make models)
run	the lesson's scenario: the demo, then the 30 tasks x 3 runs, then the service is left running
tasks	run the 30 tasks three times each against the calendar service and print the report
test	every offline test, with coverage (domain and application must stay at 95% or more)
test-integration	the calendar service and the agent as real processes, including the five SIGKILL crash points
test-live	opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
up	create the databases and start the calendar service on :8090 (HTTP over SQLite)
```

2. Dry run. `-n` prints the commands make *would* run for `make check`, without running any of them. Use it whenever you are not sure what a target does.

```bash
make -n check
```

What you should see (captured from this repository):

```text
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python -m pytest --cov=scheduling_agent --cov-report=term
.venv/bin/python -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95
```

3. Shows what the install rule would do. If the stamp file is already up to date make prints nothing, which proves the stamp logic works.

```bash
make -n install
```

What you should see (captured from this repository):

```text
make: Nothing to be done for `install'.
```

4. Shows which make you have. macOS ships GNU Make 3.81; the Makefile only uses features that exist in 3.81, so it works there and on newer versions.

```bash
make --version | head -1
```

What you should see (captured from this repository):

```text
GNU Make 3.81
```

## Mistakes people make

- **Spaces instead of a tab.** A recipe line indented with spaces gives `*** missing separator. Stop.` The repository's `.editorconfig` forces tabs for this file.
- **Forgetting `.PHONY`.** If someone creates a folder named `test`, `make test` would say "nothing to be done". Every action target is listed under `.PHONY`.
- **Writing `$` where `$$` is needed.** `$(wc -l < file)` is read by make as a make variable and comes out empty. Shell substitutions in recipes are written `$$(wc -l < file)`.
- **Expecting `cd` to carry over.** Each line is a fresh shell. This Makefile never uses `cd`; it passes paths instead.
- **Re-running slow setup every time.** Installing packages on every `make test` would be slow. The stamp file `.venv/.installed` makes the install run only when the lock file or `pyproject.toml` changed.
- **Hiding failures.** `-` in front of a command ignores its failure. It is used only where failure is expected and harmless, and the walkthrough above says where.

## Check yourself

1. What is the difference between `A = 1`, `A := 1` and `A ?= 1`?

   *Answer:* `=` is looked up each time it is used, `:=` is computed once when make reads the line, `?=` only sets the variable if nothing set it before.

2. Why does the Makefile write `$$(cat out/x.pid)` instead of `$(cat out/x.pid)`?

   *Answer:* make reads `$(...)` as its own syntax. `$$` becomes a single `$`, so the shell sees `$(cat out/x.pid)` and runs the command.

3. What does `touch $@` do at the end of the install rule, and why is it the last line?

   *Answer:* It creates or refreshes the stamp file, so make remembers the install finished. It is last so that a failure in an earlier line leaves no stamp and the install runs again next time.

4. What would happen if `test` were not listed under `.PHONY` and a folder named `test` existed?

   *Answer:* make would see a file called `test` with no newer prerequisites and would say "`test` is up to date" without running the recipe.

5. How can you see what `make down` would do without doing it?

   *Answer:* `make -n down` prints the commands without running them.

## Further reading

- GNU Make manual, https://www.gnu.org/software/make/manual/make.html (checked locally against GNU Make 3.81 with `make -n` and `make help`; the manual describes the newest release).
