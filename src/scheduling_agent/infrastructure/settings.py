"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scheduling_agent.infrastructure.env import ConfigurationError, choice, positive_float, positive_int, text

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass(frozen=True, slots=True)
class AgentSettings:
    """Where things live and how a run is capped. See env.example for each variable."""

    calendar_url: str
    calendar_db: Path
    agent_db: Path
    sql_dir: Path
    prompts_dir: Path
    prompt_version: str
    tasks_path: Path
    embeddings_path: Path
    embedder_provider: str
    embed_model: str
    people: tuple[str, ...]
    max_steps: int
    max_tokens: int
    max_seconds: float
    host: str
    port: int
    allow_reset: bool
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AgentSettings:
        env = os.environ if environ is None else environ
        people = tuple(
            p.strip().lower() for p in text(env, "PEOPLE", "alice,bob,carol,dave,erin").split(",") if p.strip()
        )
        if not people:
            raise ConfigurationError("PEOPLE must list at least one name")
        return cls(
            calendar_url=text(env, "CALENDAR_URL", "http://127.0.0.1:8090"),
            calendar_db=Path(text(env, "CALENDAR_DB", "out/calendar.db")),
            agent_db=Path(text(env, "AGENT_DB", "out/agent.db")),
            sql_dir=Path(text(env, "SQL_DIR", "sql")),
            prompts_dir=Path(text(env, "PROMPTS_DIR", "prompts")),
            prompt_version=text(env, "AGENT_PROMPT_VERSION", "v1"),
            tasks_path=Path(text(env, "TASKS_PATH", "data/tasks.jsonl")),
            embeddings_path=Path(text(env, "EMBEDDINGS_PATH", "tests/fixtures/embeddings")),
            embedder_provider=choice(env, "EMBEDDER_PROVIDER", "recorded", ("recorded", "openai-compatible")),
            embed_model=text(env, "EMBED_MODEL", "nomic-embed-text"),
            people=people,
            max_steps=positive_int(env, "MAX_STEPS", 12),
            max_tokens=positive_int(env, "MAX_TOKENS", 4000),
            max_seconds=positive_float(env, "MAX_SECONDS", 30.0),
            host=text(env, "HTTP_HOST", "127.0.0.1"),
            port=positive_int(env, "HTTP_PORT", 8090),
            allow_reset=choice(env, "CALENDAR_ALLOW_RESET", "off", ("on", "off")) == "on",
            log_level=choice({"LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )
