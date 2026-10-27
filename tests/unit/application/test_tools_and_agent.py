from datetime import datetime

import pytest

from scheduling_agent.application.agent import AgentConfig, UnknownRun
from scheduling_agent.application.tools import ToolBox, tool_specs
from scheduling_agent.domain.errors import ApprovalError
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
from scheduling_agent.domain.run import RunStatus
from scheduling_agent.infrastructure.failpoints import NoFailPoints
from tests.conftest import Crash, FixedClock, RaiseAt, approve_all, build_kit, new_calendar

BOOK = "Book a 30-minute meeting with alice and bob on 2026-11-03."


def event_count(calendar):
    return len(calendar.active_events())


def toolbox():
    kit = build_kit()
    return ToolBox(kit.calendar, kit.approvals, kit.audit, FixedClock(), NoFailPoints()), kit


def book_proposal(start="2026-11-03T11:00"):
    return Proposal(Action.BOOK, {"people": ["alice", "bob"], "start": start, "minutes": 30})


def test_the_tool_list_has_two_reads_and_three_writes_with_schemas():
    names = [t.name for t in tool_specs()]
    assert names == ["find_free_slots", "get_event", "book_meeting", "move_meeting", "cancel_meeting"]
    assert all(t.parameters["type"] == "object" for t in tool_specs())


def test_reads_return_slots_and_events_and_errors_the_model_can_read():
    box, kit = toolbox()
    found = box.read(
        "find_free_slots", {"people": ["alice"], "first_day": "2026-11-03", "last_day": "2026-11-03", "minutes": 30}
    )
    assert found["count"] >= 1
    assert len(found["slots"]) <= 12
    event = kit.calendar.active_events()[0]
    assert box.read("get_event", {"event_id": event.id})["start"] == event.start.isoformat(timespec="minutes")
    assert (
        "UnknownPerson"
        in box.read(
            "find_free_slots", {"people": ["zed"], "first_day": "2026-11-03", "last_day": "2026-11-03", "minutes": 30}
        )["error"]
    )
    assert "UnknownEvent" in box.read("get_event", {"event_id": "ev-9999"})["error"]
    assert "bad arguments" in box.read("find_free_slots", {"people": ["alice"]})["error"]
    assert "unknown tool" in box.read("fly", {})["error"]


def test_a_proposal_snapshots_the_event_it_would_change():
    box, kit = toolbox()
    event = kit.calendar.active_events()[0]
    cancel = box.propose("cancel_meeting", {"event_id": event.id})
    move = box.propose("move_meeting", {"event_id": event.id, "new_start": "2026-11-10T10:00"})
    assert isinstance(cancel, Proposal)
    assert isinstance(move, Proposal)
    assert cancel.args["minutes"] == event.minutes
    assert move.args["new_start"] == "2026-11-10T10:00"
    assert "UnknownEvent" in box.propose("cancel_meeting", {"event_id": "ev-9999"})["error"]
    assert "bad arguments" in box.propose("book_meeting", {"people": ["alice"]})["error"]


def test_a_write_without_an_approval_id_changes_nothing_and_leaves_one_refused_audit_line():
    box, kit = toolbox()
    before = event_count(kit.calendar)
    result = box.execute_write("run-x", 3, book_proposal(), None)
    assert result["status"] == "refused"
    assert event_count(kit.calendar) == before
    lines = kit.audit.lines("run-x")
    assert [(line.outcome, line.action) for line in lines] == [("refused", "book")]


def test_an_unknown_pending_or_mismatched_approval_does_not_open_the_write():
    box, kit = toolbox()
    before = event_count(kit.calendar)
    proposal = book_proposal()
    box.request_approval("run-x", 3, proposal)
    approval = kit.approvals.pending()[0]
    assert box.execute_write("run-x", 3, proposal, "ap-unknown")["status"] == "refused"
    assert "is pending" in box.execute_write("run-x", 3, proposal, approval.id)["detail"]
    kit.approvals.decide(approval.id, True, "test", FixedClock().now())
    other = book_proposal("2026-11-03T14:00")  # a quiet slot, but not the one that was approved
    assert "different proposal" in box.execute_write("run-x", 3, other, approval.id)["detail"]
    assert event_count(kit.calendar) == before


def test_an_approved_write_runs_once_and_a_second_attempt_with_the_same_key_creates_nothing_new():
    box, kit = toolbox()
    proposal = book_proposal()
    box.request_approval("run-x", 3, proposal)
    approval = kit.approvals.pending()[0]
    kit.approvals.decide(approval.id, True, "test", FixedClock().now())
    before = event_count(kit.calendar)
    first = box.execute_write("run-x", 3, proposal, approval.id)
    second = box.execute_write("run-x", 3, proposal, approval.id)
    assert first["status"] == second["status"] == "booked"
    assert first["event_id"] == second["event_id"]
    assert (first["replayed"], second["replayed"]) == (False, True)
    assert event_count(kit.calendar) == before + 1
    assert [line.outcome for line in kit.audit.lines("run-x")] == ["refused", "written"]


def test_a_write_the_calendar_refuses_is_reported_as_failed_and_logged():
    box, kit = toolbox()
    busy = kit.calendar.active_events()[0]
    proposal = Proposal(
        Action.BOOK,
        {"people": list(busy.people), "start": busy.start.isoformat(timespec="minutes"), "minutes": busy.minutes},
    )
    box.request_approval("run-x", 4, proposal)
    approval = kit.approvals.pending()[0]
    kit.approvals.decide(approval.id, True, "test", FixedClock().now())
    result = box.execute_write("run-x", 4, proposal, approval.id)
    assert result["status"] == "failed"
    assert "SlotUnavailable" in result["error"]
    assert kit.audit.lines("run-x")[-1].outcome == "failed"


def test_deciding_twice_or_on_an_unknown_approval_is_an_error():
    box, kit = toolbox()
    box.request_approval("run-x", 1, book_proposal())
    approval = kit.approvals.pending()[0]
    kit.approvals.decide(approval.id, False, "test", FixedClock().now())
    with pytest.raises(ApprovalError, match="already rejected"):
        kit.approvals.decide(approval.id, True, "test", FixedClock().now())
    with pytest.raises(ApprovalError, match="unknown approval"):
        kit.approvals.decide("ap-nope", True, "test", FixedClock().now())
    again = box.request_approval("run-x", 1, book_proposal())
    assert again["approval_id"] == approval.id  # asking again for the same run and step returns the same approval


def test_a_booking_waits_for_a_person_then_is_written_and_the_run_ends_with_one_sentence():
    kit = build_kit()
    before = event_count(kit.calendar)
    state = kit.agent.start(BOOK, "s1")
    assert state.status is RunStatus.AWAITING_APPROVAL
    assert state.pending is not None
    assert event_count(kit.calendar) == before
    assert [a.status for a in kit.approvals.pending()] == [ApprovalStatus.PENDING]
    done = approve_all(kit, state)
    assert done.status is RunStatus.DONE
    assert done.final_text.startswith("Booked event ev-")
    assert event_count(kit.calendar) == before + 1
    assert [line.outcome for line in kit.audit.lines(state.run_id)] == ["refused", "written"]
    assert len(done.writes_done) == 1


def test_a_rejected_proposal_is_not_executed_and_the_run_says_so():
    kit = build_kit()
    before = event_count(kit.calendar)
    state = kit.agent.start(BOOK, "s1")
    kit.approvals.decide(state.pending.approval_id, False, "test", FixedClock().now())  # type: ignore[union-attr]
    done = kit.agent.resume(state.run_id)
    assert done.status is RunStatus.DONE
    assert "rejected" in done.final_text
    assert event_count(kit.calendar) == before
    assert not any(line.outcome == "written" for line in kit.audit.lines(state.run_id))


def test_resuming_while_the_approval_is_still_pending_keeps_waiting_and_a_finished_run_stays_finished():
    kit = build_kit()
    state = kit.agent.start(BOOK, "s1")
    assert kit.agent.resume(state.run_id).status is RunStatus.AWAITING_APPROVAL
    done = approve_all(kit, state)
    assert kit.agent.resume(state.run_id) == done
    with pytest.raises(UnknownRun):
        kit.agent.resume("no-such-run")


def test_a_move_cancels_the_old_event_and_books_the_new_one_after_approval():
    kit = build_kit()
    event = kit.calendar.active_events()[2]
    state = kit.agent.start(f"Move event {event.id} to the earliest free slot between 2026-11-09 and 2026-11-10.", "s1")
    assert state.pending is not None
    assert state.pending.proposal.action is Action.MOVE
    done = approve_all(kit, state)
    assert done.final_text.startswith(f"Moved {event.id}")
    keys = {e.key() for e in kit.calendar.active_events()}
    assert event.key() not in keys
    assert any(k[0] == tuple(sorted(event.people)) and k[1].startswith(("2026-11-09", "2026-11-10")) for k in keys)


def test_a_cancel_is_a_proposal_too():
    kit = build_kit()
    event = kit.calendar.active_events()[0]
    state = kit.agent.start(f"Cancel event {event.id}.", "s1")
    assert state.pending is not None
    assert event.key() in {e.key() for e in kit.calendar.active_events()}
    approve_all(kit, state)
    assert event.key() not in {e.key() for e in kit.calendar.active_events()}


def test_a_person_outside_the_calendar_ends_the_run_with_no_write_and_no_proposal():
    kit = build_kit()
    before = event_count(kit.calendar)
    state = kit.agent.start("Book a 30-minute meeting with zed and alice on 2026-11-04.", "s1")
    assert state.status is RunStatus.DONE
    assert "changed nothing" in state.final_text
    assert event_count(kit.calendar) == before
    assert kit.approvals.pending() == []


def test_a_task_that_cannot_succeed_stops_at_the_step_cap_and_says_which_cap_fired():
    kit = build_kit()
    before = event_count(kit.calendar)
    state = kit.agent.start(
        "Book a 30-minute meeting with bob and carol on 2026-11-06 after 17:00. Do not give up.", "s1"
    )
    assert state.status is RunStatus.STOPPED
    assert state.stop_reason == "steps"
    assert state.steps == 12
    assert "step cap reached: 12/12" in state.final_text
    assert "no write was made" in state.final_text
    assert state.tokens < 4000
    assert event_count(kit.calendar) == before


def test_the_token_cap_and_the_time_cap_each_stop_a_run_on_their_own():
    tokens = build_kit(config=AgentConfig(max_tokens=60)).agent.start(
        "Book a 30-minute meeting with bob and carol on 2026-11-06 after 17:00. Do not give up.", "s1"
    )
    assert (tokens.status, tokens.stop_reason) == (RunStatus.STOPPED, "tokens")
    assert "token cap reached" in tokens.final_text
    slow = build_kit(config=AgentConfig(max_seconds=2.0), clock=FixedClock(tick=1.0)).agent.start(BOOK, "s1")
    assert (slow.status, slow.stop_reason) == (RunStatus.STOPPED, "seconds")
    assert "time cap reached" in slow.final_text


def test_what_a_person_said_in_an_earlier_session_is_used_in_a_later_run_and_a_changed_preference_replaces_it():
    kit = build_kit()
    plain = approve_all(kit, kit.agent.start(BOOK, "s0", run_id="plain"))
    start_without = datetime.fromisoformat(
        next(
            e for e in kit.calendar.active_events() if e.id == plain.final_text.split()[2].rstrip(".")
        ).start.isoformat()
    )
    kit.memory.remember("alice", "I never want meetings before 10", "s1")
    kit2 = build_kit(store=None)
    kit2.memory.remember("alice", "I never want meetings before 10", "s1")
    state = approve_all(kit2, kit2.agent.start(BOOK, "s2"))
    booked = next(e for e in kit2.calendar.active_events() if e.id == state.final_text.split()[2].rstrip("."))
    assert booked.start.hour >= 10
    assert start_without.hour >= 9
    kit2.memory.remember("alice", "Actually, nothing before 13 from now on", "s3")
    assert [f.value for f in kit2.memory.facts() if f.person == "alice"] == ["13:00"]
    assert kit2.memory.forget("alice") == 1
    assert kit2.memory.facts() == []


@pytest.mark.parametrize(
    "point", ["run_created", "after_step", "after_proposal", "before_write", "after_write_before_checkpoint"]
)
def test_a_crash_at_any_point_then_a_resume_books_exactly_one_event(point):
    calendar = new_calendar()
    before = event_count(calendar)
    first = build_kit(calendar=calendar, points=RaiseAt(point))
    store_kit = first
    with pytest.raises(Crash):
        approve_all(first, first.agent.start(BOOK, "s1", run_id="crash-run"))
    # a new process: a new agent on the same databases
    second = build_kit(calendar=calendar, store=store_kit.approvals)  # type: ignore[arg-type]
    state = (
        second.agent.resume("crash-run")
        if "crash-run" in second.checkpoints.unfinished()
        else second.agent.start(BOOK, "s1", run_id="crash-run")
    )
    done = approve_all(second, state)
    assert done.status is RunStatus.DONE
    assert event_count(calendar) == before + 1
    assert sum(line.outcome == "written" for line in second.audit.lines("crash-run")) == 1


def test_a_crash_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume_without_a_duplicate():
    calendar = new_calendar()
    event = calendar.active_events()[2]
    task = f"Move event {event.id} to the earliest free slot between 2026-11-09 and 2026-11-10."
    first = build_kit(calendar=calendar, points=RaiseAt("between_move_cancel_and_book"))
    with pytest.raises(Crash):
        approve_all(first, first.agent.start(task, "s1", run_id="move-run"))
    assert event.key() not in {e.key() for e in calendar.active_events()}  # the cancel went through
    second = build_kit(calendar=calendar, store=first.approvals)  # type: ignore[arg-type]
    done = approve_all(second, second.agent.resume("move-run"))
    assert done.final_text.startswith(f"Moved {event.id}")
    moved = [
        e for e in calendar.active_events() if e.people == event.people and e.start.date().isoformat() >= "2026-11-09"
    ]
    assert len(moved) == 1
