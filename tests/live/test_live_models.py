"""Opt-in tests that call real models. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from scheduling_agent.application.tools import tool_specs
from scheduling_agent.domain.llm import ChatMessage, ChatRequest
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from tests.conftest import REPO

pytestmark = pytest.mark.live

SYSTEM = (REPO / "prompts" / "agent" / "v1.md").read_text().split("---\n", 2)[2].strip()
TASK = "Book a 30-minute meeting with alice and bob on 2026-11-03."


def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def first_step(provider: str):
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": provider}), SystemClock())
    request = ChatRequest((ChatMessage.user(TASK),), system=SYSTEM, max_output_tokens=300, tools=tool_specs())
    return model.complete(request)


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_starts_by_reading_the_calendar_not_by_writing():
    response = first_step("anthropic")
    assert response.tool_calls
    assert response.tool_calls[0].name == "find_free_slots"


@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_model_answers_with_a_tool_call_in_the_protocol_the_agent_expects():
    response = first_step("openai-compatible")
    assert response.tool_calls or response.text
    for call in response.tool_calls:
        assert call.name in {t.name for t in tool_specs()}
        assert isinstance(call.arguments, dict)
