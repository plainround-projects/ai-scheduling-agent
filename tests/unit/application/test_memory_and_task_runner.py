import dataclasses

import pytest

from scheduling_agent.application.task_runner import ExpectedWritesApprover, TaskRunner
from scheduling_agent.domain.proposals import Action, Proposal
from scheduling_agent.domain.run import RunStatus
from scheduling_agent.domain.tasks import TaskKind, TaskSpec, expected_end_state
from scheduling_agent.infrastructure.calendar_seed import reset_calendar
from scheduling_agent.infrastructure.files import load_tasks
from tests.conftest import REPO, FixedClock, build_kit, new_calendar


def test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten():
    kit = build_kit()
    assert kit.memory.remember("alice", "I like coffee", "s1") is None
    assert kit.memory.facts() == []
    kit.memory.remember("alice", "nothing before 10", "s1")
    kit.memory.remember("bob", "nothing before 11", "s1")
    assert len(kit.memory.facts()) == 2
    assert kit.memory.forget("alice") == 1
    assert [f.person for f in kit.memory.facts()] == ["bob"]


def test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first():
    kit = build_kit()
    for person, text in (
        ("alice", "nothing before 10"),
        ("alice", "No meetings on Fridays"),
        ("alice", "nothing after 4pm"),
        ("bob", "nothing before 11"),
        ("carol", "nothing before 9"),
    ):
        kit.memory.remember(person, text, "s1")
    recalled = kit.memory.recall("Book 30 minutes with alice and bob on Tuesday")
    assert len(recalled) == 3
    assert {f.person for f in recalled} <= {"alice", "bob"}
    assert kit.memory.recall("Book 30 minutes with dave") == []
    everyone = kit.memory.recall("Book a team meeting")
    assert len(everyone) == 3


def test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects():
    task = TaskSpec("t", TaskKind.RESCHEDULE, "x", (), ((("alice", "bob"), "2026-11-10T10:00", 30),), ("ev-1",))
    approver = ExpectedWritesApprover()
    book = Proposal(Action.BOOK, {"people": ["bob", "alice"], "start": "2026-11-10T10:00", "minutes": 30})
    wrong_time = Proposal(Action.BOOK, {"people": ["alice", "bob"], "start": "2026-11-10T11:00", "minutes": 30})
    cancel = Proposal(Action.CANCEL, {"event_id": "ev-1"})
    other_cancel = Proposal(Action.CANCEL, {"event_id": "ev-2"})
    move = Proposal(
        Action.MOVE, {"event_id": "ev-1", "people": ["alice", "bob"], "minutes": 30, "new_start": "2026-11-10T10:00"}
    )
    assert [approver.decide(task, p) for p in (book, wrong_time, cancel, other_cancel, move)] == [
        True,
        False,
        True,
        False,
        True,
    ]


class Admin:
    def __init__(self, calendar):
        self._calendar = calendar

    def reset(self):
        reset_calendar(self._calendar._db, REPO / "sql")


def runner():
    calendar = new_calendar()
    return TaskRunner(
        Admin(calendar), lambda: build_kit(calendar=calendar), ExpectedWritesApprover(), FixedClock()
    ), calendar


def test_the_task_file_has_the_lessons_mix_and_each_expected_state_is_what_the_calendar_search_finds():
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")
    assert len(tasks) == 30
    assert sum(bool(t.facts) for t in tasks) >= 10
    for task in tasks:
        if task.kind is TaskKind.IMPOSSIBLE:
            assert not task.add
            assert not task.remove
        else:
            assert task.add or task.remove


def test_all_thirty_tasks_reach_their_expected_end_state_with_no_write_lacking_an_approval():
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")
    task_runner, _ = runner()
    results = task_runner.run_all(tasks, repeats=1)
    assert len(results) == 30
    failed = [r.task_id for r in results if not r.passed]
    assert failed == []
    assert sum(r.writes_without_approval for r in results) == 0
    assert sum(r.approvals_rejected for r in results) == 0
    impossible = [r for r in results if r.task_id.startswith("t-impossible")]
    assert all(r.approvals_granted == 0 for r in impossible)
    assert {(r.status, r.stop_reason) for r in impossible} == {(RunStatus.DONE, ""), (RunStatus.STOPPED, "steps")}


def test_a_wrong_proposal_is_rejected_by_the_person_and_the_calendar_stays_as_it_was():
    task_runner, calendar = runner()
    seed_keys = {e.key() for e in calendar.active_events()}
    impostor = TaskSpec(
        "t-x",
        TaskKind.BOOK,
        "Book a 30-minute meeting with alice and bob on 2026-11-03.",
        (),
        ((("alice", "bob"), "2026-11-03T16:30", 30),),
        (),
    )
    result = task_runner.run_once(impostor, 1)
    assert result.approvals_rejected >= 1
    assert not result.passed or {e.key() for e in calendar.active_events()} != seed_keys
    assert expected_end_state(calendar.active_events(), impostor)


def test_the_task_report_lists_pass_rates_and_the_totals():
    from scheduling_agent.interfaces.cli import render_task_report

    tasks = load_tasks(REPO / "data" / "tasks.jsonl")[:3]
    task_runner, _ = runner()
    text = render_task_report(task_runner.run_all(tasks, repeats=2), 2)
    assert "tasks passed: 6/6 attempts (3 tasks x 2 runs)" in text
    assert "writes without an approval: 0" in text


def test_a_stop_request_ends_the_run_all_loop_between_attempts():
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")[:3]
    task_runner, _ = runner()
    stops = iter([False, True])
    assert len(task_runner.run_all(tasks, repeats=1, stop_requested=lambda: next(stops))) == 1


FACT_TASKS = [t for t in load_tasks(REPO / "data" / "tasks.jsonl") if t.facts]


@pytest.mark.parametrize("task", FACT_TASKS, ids=lambda t: t.id)
def test_a_fact_told_in_an_earlier_session_decides_where_the_meeting_lands(task):
    """The ten fact-and-task pairs: with the fact the end state is the expected one; without it, it is not."""
    task_runner, _ = runner()
    assert task_runner.run_once(task, 1).passed
    forgotten = dataclasses.replace(task, facts=())
    assert not task_runner.run_once(forgotten, 1).passed


def test_there_are_ten_fact_and_task_pairs_and_one_of_them_changes_a_preference():
    assert len(FACT_TASKS) == 10
    changed = [t for t in FACT_TASKS if len({person for person, _ in t.facts}) < len(t.facts)]
    assert [t.id for t in changed] == ["t-book-05"]
