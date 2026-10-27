"""Build the agent and everything it stands on from the settings."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Callable, Mapping

import httpx

from scheduling_agent.application.agent import AgentConfig, SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import CalendarPort, ChatModel, Clock, Embedder, FailPoints
from scheduling_agent.application.task_runner import AgentKit
from scheduling_agent.application.tools import ToolBox
from scheduling_agent.infrastructure import failpoints
from scheduling_agent.infrastructure.agent_db import AgentDb
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.embeddings import (
    EmbeddingStore,
    OpenAICompatibleEmbedder,
    RecordedEmbedder,
    RecordingEmbedder,
)
from scheduling_agent.infrastructure.env import choice, optional_text, positive_float, text
from scheduling_agent.infrastructure.files import FilePromptStore
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.sqlite import apply_sql, connect


def build_embedder(settings: AgentSettings, environ: Mapping[str, str] | None = None) -> Embedder:
    """`recorded` replays vectors; `openai-compatible` calls the local server (and records if RECORD=on)."""
    env = os.environ if environ is None else environ
    if settings.embedder_provider == "recorded":
        return RecordedEmbedder(EmbeddingStore(settings.embeddings_path), settings.embed_model)
    http = httpx.Client(timeout=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0))
    live = OpenAICompatibleEmbedder(
        http,
        text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
        settings.embed_model,
        optional_text(env, "OPENAI_API_KEY"),
    )
    if choice(env, "RECORD", "off", ("on", "off")) == "on":
        return RecordingEmbedder(live, EmbeddingStore(settings.embeddings_path))
    return live


def build_calendar(settings: AgentSettings) -> HttpCalendar:
    """The HTTP client for the calendar service named in the settings."""
    return HttpCalendar(httpx.Client(timeout=10.0), settings.calendar_url)


def build_kit(
    settings: AgentSettings,
    model: ChatModel,
    clock: Clock,
    embedder: Embedder,
    calendar: CalendarPort | None = None,
    connection: sqlite3.Connection | None = None,
    points: FailPoints | None = None,
    new_run_id: Callable[[], str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> AgentKit:
    """One agent on one agent database. Tests pass a calendar and a connection; the CLI passes neither."""
    env = os.environ if environ is None else environ
    db_connection = connection or connect(settings.agent_db)
    apply_sql(db_connection, settings.sql_dir / "agent" / "001_schema.sql")
    store = AgentDb(db_connection)
    cal = calendar or build_calendar(settings)
    marks = points or failpoints.from_env(env)
    tools = ToolBox(cal, store, store, clock, marks)
    memory = MemoryService(store, embedder, clock, settings.people)
    prompt = FilePromptStore(settings.prompts_dir).load("agent", settings.prompt_version)
    config = AgentConfig(settings.max_steps, settings.max_tokens, settings.max_seconds)
    if new_run_id is None:
        agent = SchedulingAgent(model, tools, store, store, store, memory, clock, prompt, config, marks)
    else:
        agent = SchedulingAgent(model, tools, store, store, store, memory, clock, prompt, config, marks, new_run_id)
    return AgentKit(agent, store, store, store, memory, cal)
