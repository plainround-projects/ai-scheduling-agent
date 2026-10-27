"""Shared builders for tests: a fixed clock, a hashing embedder and a ready agent kit on in-memory databases."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from scheduling_agent.application.agent import AgentConfig, SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import CalendarPort, ChatModel
from scheduling_agent.application.task_runner import AgentKit
from scheduling_agent.application.tools import ToolBox
from scheduling_agent.domain.llm import ChatRequest, ChatResponse, StopReason, Usage
from scheduling_agent.domain.prompts import Prompt
from scheduling_agent.infrastructure.agent_db import AgentDb
from scheduling_agent.infrastructure.calendar_db import SqliteCalendar
from scheduling_agent.infrastructure.failpoints import NoFailPoints
from scheduling_agent.infrastructure.scripted_policy import ScriptedPolicyModel
from scheduling_agent.infrastructure.sqlite import apply_sql, connect

REPO = Path(__file__).resolve().parents[1]


class FixedClock:
    """A clock that only moves when a test says so; `monotonic` advances by `tick` on every call."""

    def __init__(self, today: date = date(2026, 10, 27), tick: float = 0.25) -> None:
        self._today = today
        self._ticks = 0.0
        self._tick = tick

    def monotonic(self) -> float:
        self._ticks += self._tick
        return self._ticks

    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class HashingEmbedder:
    """A deterministic bag-of-words embedder: similar wording gives similar vectors. For tests only."""

    name = "hashing"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vector = [0.0] * 64
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            out.append(vector)
        return out


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""

    def __init__(
        self, answer: Callable[[ChatRequest], str | tuple[str, int, int]] | None = None, sampling: bool = True
    ) -> None:
        self.requests: list[ChatRequest] = []
        self._answer = answer or (lambda request: ("ok", 10, 3))
        self._sampling = sampling

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def supports_sampling(self) -> bool:
        return self._sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        result = self._answer(request)
        text, tokens_in, tokens_out = (result, 30, 8) if isinstance(result, str) else result
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class Crash(BaseException):
    """Raised by a test failpoint to stand in for the process dying at that point (nothing catches BaseException)."""


class RaiseAt:
    """A failpoint that raises `Crash` the first time execution reaches the named point."""

    def __init__(self, name: str) -> None:
        self._name = name
        self.fired = False

    def hit(self, name: str) -> None:
        if name == self._name and not self.fired:
            self.fired = True
            raise Crash(name)


def new_calendar() -> SqliteCalendar:
    db = connect(":memory:")
    apply_sql(db, REPO / "sql/calendar/001_schema.sql", REPO / "sql/calendar/002_seed.sql")
    return SqliteCalendar(db)


PROMPT = Prompt("agent", "v1", "You schedule meetings.")
PEOPLE = ("alice", "bob", "carol", "dave", "erin")


def build_kit(
    calendar: CalendarPort | None = None,
    model: ChatModel | None = None,
    store: AgentDb | None = None,
    points=None,
    config: AgentConfig | None = None,
    clock: FixedClock | None = None,
) -> AgentKit:
    clock = clock or FixedClock()
    cal = calendar or new_calendar()
    if store is None:
        db = connect(":memory:")
        apply_sql(db, REPO / "sql/agent/001_schema.sql")
        store = AgentDb(db)
    marks = points or NoFailPoints()
    tools = ToolBox(cal, store, store, clock, marks)
    memory = MemoryService(store, HashingEmbedder(), clock, PEOPLE)
    counter = iter(range(1, 10_000))
    agent = SchedulingAgent(
        model or ScriptedPolicyModel(),
        tools,
        store,
        store,
        store,
        memory,
        clock,
        PROMPT,
        config or AgentConfig(),
        marks,
        new_run_id=lambda: f"run-{next(counter)}",
    )
    return AgentKit(agent, store, store, store, memory, cal)


def approve_all(kit: AgentKit, state, decide: Callable[[object], bool] | None = None):
    """Play the person: approve every pending proposal of the run, resuming until the run stops waiting."""
    from scheduling_agent.domain.run import RunStatus

    clock = FixedClock()
    while state.status is RunStatus.AWAITING_APPROVAL:
        for approval in kit.approvals.pending():
            kit.approvals.decide(approval.id, True, "test", clock.now())
        state = kit.agent.resume(state.run_id)
    return state


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()
