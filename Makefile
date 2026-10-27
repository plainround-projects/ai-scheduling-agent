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

-include .env
export

.PHONY: help install up db calendar-up calendar-down run demo tasks models record lint format test test-integration test-e2e \
        test-live audit check down clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the lock file

up: $(STAMP) calendar-up ## create the databases and start the calendar service on :8090 (HTTP over SQLite)

db: $(STAMP) ## create out/calendar.db and out/agent.db from the numbered SQL files (safe to repeat)
	mkdir -p out
	sqlite3 out/calendar.db < sql/calendar/001_schema.sql
	sqlite3 out/calendar.db "SELECT count(*) FROM people" | grep -q '^0$$' && sqlite3 out/calendar.db < sql/calendar/002_seed.sql || true
	sqlite3 out/agent.db < sql/agent/001_schema.sql
	@echo "calendar: $$(sqlite3 out/calendar.db 'select count(*) from events') events for $$(sqlite3 out/calendar.db 'select count(*) from people') people"

calendar-up: db ## start the calendar service in the background (writes out/calendar.pid)
	@if [ -f $(CAL_PID) ] && kill -0 $$(cat $(CAL_PID)) 2>/dev/null; then echo "calendar service already running (pid $$(cat $(CAL_PID)))"; \
	else $(CAL_ENV) nohup $(VENV)/bin/calendar-service serve > out/calendar.log 2>&1 & echo $$! > $(CAL_PID); fi
	@for i in $$(seq 1 40); do curl -sf http://127.0.0.1:$(CAL_PORT)/health >/dev/null && break || sleep 0.25; done; curl -sf http://127.0.0.1:$(CAL_PORT)/health && echo

calendar-down: ## stop the calendar service (SIGTERM: in-flight requests finish)
	@if [ -f $(CAL_PID) ]; then kill $$(cat $(CAL_PID)) 2>/dev/null || true; rm -f $(CAL_PID); fi

# One task with the scripted stand-in model: the write waits for a person; --auto-approve plays the person.
demo: up ## book a meeting end to end: propose, approve, write, final answer (and a replay of the same request)
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) tell alice "I never want meetings before 10" --session s1
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) run "Book a 30-minute meeting with alice and bob on 2026-11-03." --run-id demo-1 || [ $$? -eq 5 ]
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) pending
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) resume demo-1 --auto-approve
	$(CAL_ENV) AGENT_DB=out/agent-demo.db $(AGENT) audit --run demo-1

# The lesson's step 6: 30 tasks x 3 runs, each judged by the calendar's real end state.
tasks: up ## run the 30 tasks three times each against the calendar service and print the report
	$(CAL_ENV) $(AGENT) tasks --runs 3

run: up ## the lesson's scenario: the demo, then the 30 tasks x 3 runs, then the service is left running
	$(MAKE) --no-print-directory demo
	$(MAKE) --no-print-directory tasks

models: ## download the pinned small open-weight models for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(LOCAL_MODEL)
	scripts/pull_model.sh $(EMBED_MODEL)

record: up ## record the memory embeddings by running the task set once with the local embedding model (needs make models)
	$(CAL_ENV) EMBEDDER_PROVIDER=openai-compatible EMBED_MODEL=$(EMBED_MODEL) RECORD=on \
	  EMBEDDINGS_PATH=tests/fixtures/embeddings/nomic-embed-text.jsonl $(AGENT) tasks --runs 1

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

# Unit, end-to-end and process tests, all offline. The process tests start the calendar service and kill the agent with SIGKILL.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=scheduling_agent --cov-report=term
	$(PY) -m coverage report --include='src/scheduling_agent/domain/*,src/scheduling_agent/application/*' --fail-under=95

test-integration: $(STAMP) ## the calendar service and the agent as real processes, including the five SIGKILL crash points
	$(PY) -m pytest tests/integration -m integration

test-e2e: $(STAMP) ## the 30 tasks through the real HTTP service
	$(PY) -m pytest tests/e2e -m e2e

test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

check: lint test ## format check, lint, types, import rules and every offline test

down: calendar-down ## stop the calendar service and remove the databases and logs (out/)
	rm -rf out

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
