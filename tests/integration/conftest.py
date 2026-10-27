"""Fixtures that start the calendar service as a real process on a free port."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Service:
    url: str
    db: Path
    process: subprocess.Popen[str]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def base_env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "FAILPOINT"}}
    env.update(MODEL_PROVIDER="scripted", EMBEDDER_PROVIDER="recorded", LOG_LEVEL="WARNING", **extra)
    return env


@pytest.fixture
def service(tmp_path: Path) -> Iterator[Service]:
    port = free_port()
    db = tmp_path / "calendar.db"
    env = base_env(HTTP_PORT=str(port), CALENDAR_DB=str(db), CALENDAR_ALLOW_RESET="on")
    process = subprocess.Popen(
        [sys.executable, "-m", "scheduling_agent.interfaces.calendar_server", "serve"],
        cwd=REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{url}/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("the calendar service did not start")
    yield Service(url, db, process)
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=30)


def agent(
    service: Service, tmp_path: Path, *args: str, failpoint: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the `agent` command as a process against the service, with its own database file."""
    extra = {"FAILPOINT": failpoint} if failpoint else {}
    env = base_env(CALENDAR_URL=service.url, AGENT_DB=str(tmp_path / "agent.db"), **extra)
    return subprocess.run(
        [sys.executable, "-m", "scheduling_agent.interfaces.cli", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def events(service: Service) -> list[dict[str, object]]:
    body: list[dict[str, object]] = httpx.get(f"{service.url}/events", timeout=10).json()
    return body
