from datetime import datetime

import pytest

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.tasks import (
    InvalidTasks,
    TaskKind,
    TaskSpec,
    end_state,
    expected_end_state,
    validate_tasks,
)


def task(i, kind, add=(), remove=()):
    return TaskSpec(f"t{i}", kind, "text", (), tuple(add), tuple(remove))


def mix():
    out: list[TaskSpec] = []
    for kind, count in (
        (TaskKind.BOOK, 12),
        (TaskKind.RESCHEDULE, 6),
        (TaskKind.FIND_SLOT, 4),
        (TaskKind.CANCEL, 4),
        (TaskKind.IMPOSSIBLE, 4),
    ):
        out += [task(len(out) + i, kind) for i in range(count)]
    return out


def test_the_lessons_mix_of_thirty_tasks_is_accepted():
    validate_tasks(mix())


def test_a_wrong_mix_duplicate_ids_and_an_impossible_task_that_changes_things_are_rejected():
    with pytest.raises(InvalidTasks, match="expected"):
        validate_tasks(mix()[:-1])
    dup = mix()
    dup[1] = dup[0]
    with pytest.raises(InvalidTasks, match="unique"):
        validate_tasks(dup)
    bad = mix()
    bad[-1] = task(99, TaskKind.IMPOSSIBLE, remove=["ev-1"])
    with pytest.raises(InvalidTasks, match="changes nothing"):
        validate_tasks(bad)


def test_the_expected_end_state_is_the_seed_with_the_removals_and_additions_applied():
    seed = [
        Event("ev-1", ("alice",), datetime(2026, 11, 2, 9), 30),
        Event("ev-2", ("bob",), datetime(2026, 11, 2, 10), 30),
        Event("ev-3", ("bob",), datetime(2026, 11, 2, 11), 30, cancelled=True),
    ]
    added = (("carol",), "2026-11-03T09:00", 30)
    expected = expected_end_state(seed, task(1, TaskKind.RESCHEDULE, add=[added], remove=["ev-1"]))
    assert expected == {seed[1].key(), added}
    assert end_state([seed[1]]) == {seed[1].key()}


def test_a_task_is_read_from_json():
    row = {
        "id": "t1",
        "kind": "book",
        "text": "x",
        "facts": [["alice", "nothing before 10"]],
        "add": [{"people": ["a", "b"], "start": "2026-11-02T10:00", "minutes": 30}],
        "remove": ["ev-9"],
    }
    parsed = TaskSpec.from_json(row)
    assert parsed.facts == (("alice", "nothing before 10"),)
    assert parsed.add == ((("a", "b"), "2026-11-02T10:00", 30),)
    assert parsed.remove == ("ev-9",)
