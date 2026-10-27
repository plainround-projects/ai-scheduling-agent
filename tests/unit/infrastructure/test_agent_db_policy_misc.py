import json
import os
import signal
import subprocess
import sys
from datetime import date, datetime, timedelta

import pytest

from scheduling_agent.domain.approvals import AuditLine
from scheduling_agent.domain.errors import ApprovalError
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, Role, ToolCall
from scheduling_agent.domain.memory import parse_statement
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
from scheduling_agent.domain.run import PendingWrite, RunState, RunStatus
from scheduling_agent.infrastructure import failpoints, state_codec
from scheduling_agent.infrastructure.agent_db import AgentDb
from scheduling_agent.infrastructure.env import ConfigurationError
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from scheduling_agent.infrastructure.scripted_policy import ScriptedPolicyModel
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.sqlite import apply_sql, connect
from tests.conftest import REPO, FixedClock


@pytest.fixture
def db():
    connection = connect(":memory:")
    apply_sql(connection, REPO / "sql/agent/001_schema.sql")
    return AgentDb(connection, new_id=iter(f"{i:04d}" for i in range(1, 99)).__next__)


def state(**changes):
    base = RunState(
        "run-1",
        "Book it",
        "s1",
        RunStatus.RUNNING,
        2,
        90,
        (
            ChatMessage.user("Book it"),
            ChatMessage(Role.ASSISTANT, "", (ToolCall("c1", "find_free_slots", {"minutes": 30}),)),
            ChatMessage(Role.TOOL, '{"slots":[]}', tool_call_id="c1"),
        ),
    )
    return base.with_(**changes)


def test_a_run_state_survives_a_round_trip_with_messages_tool_calls_and_a_pending_write():
    pending = PendingWrite(
        2,
        "c2",
        "book_meeting",
        Proposal(Action.BOOK, {"people": ["a"], "start": "2026-11-02T10:00", "minutes": 30}),
        "ap-1",
        ("c3",),
    )
    original = state(
        status=RunStatus.AWAITING_APPROVAL, pending=pending, writes_done=("abc",), created_at=datetime(2026, 10, 27)
    )
    assert state_codec.decode(state_codec.encode(original)) == original
    assert state_codec.decode(state_codec.encode(state())).pending is None


def test_saving_a_run_twice_updates_it_and_load_returns_the_latest_state(db):
    now = FixedClock().now()
    db.save(state(), now)
    db.save(state(steps=3, status=RunStatus.AWAITING_APPROVAL), now + timedelta(seconds=1))
    loaded = db.load("run-1")
    assert loaded is not None
    assert (loaded.steps, loaded.status) == (3, RunStatus.AWAITING_APPROVAL)
    assert db.load("nope") is None
    assert db.unfinished() == ["run-1"]
    db.save(state(status=RunStatus.DONE), now)
    assert db.unfinished() == []


def test_approvals_are_created_once_per_step_decided_once_and_listed_while_pending(db):
    now = FixedClock().now()
    proposal = Proposal(Action.CANCEL, {"event_id": "ev-1"})
    first = db.request("run-1", 4, proposal, now)
    assert db.request("run-1", 4, proposal, now).id == first.id
    assert [a.id for a in db.pending()] == [first.id]
    decided = db.decide(first.id, True, "me", now)
    assert (decided.status, decided.decided_by) == (ApprovalStatus.APPROVED, "me")
    assert db.pending() == []
    assert db.get(first.id) == decided
    assert db.get("ap-none") is None
    with pytest.raises(ApprovalError):
        db.decide(first.id, False, "me", now)


def test_the_audit_log_keeps_a_replayed_line_once_and_filters_by_run(db):
    at = FixedClock().now()
    line = AuditLine(at, "run-1", 3, "book", "written", "ap-1", "ev-0042")
    db.append(line)
    db.append(line)
    db.append(AuditLine(at, "run-2", 1, "cancel", "refused", None, "no approval"))
    assert len(db.lines()) == 2
    assert [entry.run_id for entry in db.lines("run-2")] == ["run-2"]


def test_facts_are_stored_one_per_person_and_topic_and_replaced_as_a_set(db):
    today = date(2026, 10, 27)
    facts = [
        parse_statement("alice", "nothing before 10", "s1", today),
        parse_statement("carol", "No meetings on Fridays", "s1", today),
    ]
    db.replace([f for f in facts if f])
    assert sorted((f.person, f.value) for f in db.facts()) == [("alice", "10:00"), ("carol", "4")]
    db.replace([])
    assert db.facts() == []


def messages(task, *results):
    out = [ChatMessage.user(task)]
    for index, result in enumerate(results, start=1):
        out.append(ChatMessage(Role.ASSISTANT, "", (ToolCall(f"c{index}", "x", {}),)))
        out.append(ChatMessage(Role.TOOL, json.dumps(result), tool_call_id=f"c{index}"))
    return tuple(out)


def decide(task, *results):
    response = ScriptedPolicyModel().complete(ChatRequest(messages(task, *results)))
    return response.tool_calls[0] if response.tool_calls else response.text


def test_the_policy_searches_first_then_proposes_the_first_slot_then_reports():
    task = "Book a 30-minute meeting with alice and bob on 2026-11-03 after 13:00."
    search = decide(task)
    assert (search.name, search.arguments["not_before"], search.arguments["people"]) == (
        "find_free_slots",
        "13:00",
        ["alice", "bob"],
    )
    book = decide(task, {"slots": ["2026-11-03T13:30", "2026-11-03T14:00"], "count": 2})
    assert (book.name, book.arguments["start"]) == ("book_meeting", "2026-11-03T13:30")
    assert (
        decide(task, {"slots": ["2026-11-03T13:30"]}, {"status": "booked", "event_id": "ev-0099"})
        == "Booked event ev-0099."
    )


def test_the_policy_applies_remembered_preferences_to_its_search():
    task = "Book a 30-minute meeting with alice on 2026-11-03.\n\nWhat people told you earlier (use it):\n- alice: I never want meetings before 10 (said 2026-10-27, session s1)"
    assert decide(task).arguments["not_before"] == "10:00"


def test_the_policy_gives_up_politely_on_an_error_or_an_empty_search_and_a_persistent_one_keeps_searching():
    task = "Book a 30-minute meeting with zed on 2026-11-03."
    assert "changed nothing" in decide(task, {"error": "UnknownPerson: zed"})
    assert "no free slot" in decide(task, {"slots": []})
    persistent = "Book a 30-minute meeting with bob on 2026-11-06 after 17:00. Do not give up."
    again = decide(persistent, {"slots": [], "count": 0})
    assert again.name == "find_free_slots"
    assert again.arguments["first_day"] == "2026-11-13"
    assert "did not happen" in decide(task, {"slots": ["2026-11-03T10:00"]}, {"status": "refused", "detail": "x"})


def test_the_policy_handles_move_and_cancel_and_says_when_it_does_not_understand():
    move = "Move event ev-0005 to the earliest free slot between 2026-11-09 and 2026-11-10 after 13:00."
    assert decide(move).name == "get_event"
    event = {"event_id": "ev-0005", "people": ["alice"], "minutes": 60, "start": "2026-11-02T10:00"}
    search = decide(move, event)
    assert (search.name, search.arguments["minutes"], search.arguments["not_before"]) == (
        "find_free_slots",
        60,
        "13:00",
    )
    assert decide(move, event, {"slots": ["2026-11-09T13:00"]}).name == "move_meeting"
    assert decide(move, event, {"slots": []}) == "There is no free slot that fits, so I changed nothing."
    assert "Moved ev-0005" in decide(move, event, {"slots": ["x"]}, {"status": "moved", "event_id": "ev-0100"})
    assert "could not find" in decide(move, {"error": "UnknownEvent"})
    cancel = "Cancel event ev-0007."
    assert decide(cancel).name == "get_event"
    assert decide(cancel, event).name == "cancel_meeting"
    assert decide(cancel, event, {"status": "cancelled"}) == "Cancelled ev-0007."
    assert "could not find" in decide(cancel, {"error": "UnknownEvent"})
    assert "did not understand" in decide("Sing me a song")


def test_the_policy_reports_what_it_is_and_counts_tokens_from_the_conversation():
    policy = ScriptedPolicyModel()
    response = policy.complete(ChatRequest(messages("Cancel event ev-0007.")))
    assert (policy.name, policy.supports_sampling) == ("scripted-policy", True)
    assert response.usage.input_tokens > 30
    assert response.model == "scripted-policy"


def test_the_scripted_provider_is_the_default_and_other_providers_are_still_available():
    settings = ModelSettings.from_env({})
    assert settings.provider == "scripted"
    assert isinstance(build_chat_model(settings, FixedClock(), {}), ScriptedPolicyModel)
    assert ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"}).model == "qwen2.5:1.5b"


def test_failpoints_are_off_unless_named_and_a_named_one_kills_with_sigkill():
    assert isinstance(failpoints.from_env({}), failpoints.NoFailPoints)
    failpoints.NoFailPoints().hit("anything")
    named = failpoints.from_env({"FAILPOINT": "after_proposal"})
    assert isinstance(named, failpoints.SigkillAt)
    named.hit("some_other_point")  # survives
    code = "from scheduling_agent.infrastructure.failpoints import SigkillAt; SigkillAt('boom').hit('boom'); print('alive')"
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={**os.environ}, check=False)
    assert done.returncode == -signal.SIGKILL
    assert "alive" not in done.stdout


def test_settings_have_defaults_and_validate_each_value():
    settings = AgentSettings.from_env({})
    assert (settings.max_steps, settings.max_tokens, settings.max_seconds) == (12, 4000, 30.0)
    assert settings.people == ("alice", "bob", "carol", "dave", "erin")
    assert not settings.allow_reset
    assert AgentSettings.from_env({"PEOPLE": "Zoe, Yan", "CALENDAR_ALLOW_RESET": "on"}).people == ("zoe", "yan")
    for bad, name in (
        ({"MAX_STEPS": "0"}, "MAX_STEPS"),
        ({"PEOPLE": " , "}, "PEOPLE"),
        ({"CALENDAR_ALLOW_RESET": "yes"}, "CALENDAR_ALLOW_RESET"),
        ({"MAX_SECONDS": "-1"}, "MAX_SECONDS"),
        ({"LOG_LEVEL": "loud"}, "LOG_LEVEL"),
    ):
        with pytest.raises(ConfigurationError, match=name):
            AgentSettings.from_env(bad)
