# Python source, the unit tests (part 1 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 6 files with 67 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/application/test_memory_and_task_runner.py` | 122 non-blank lines |
| `tests/unit/application/test_tools_and_agent.py` | 245 non-blank lines |
| `tests/unit/domain/test_calendar_memory_budget.py` | 148 non-blank lines |
| `tests/unit/domain/test_llm.py` | 22 non-blank lines |
| `tests/unit/domain/test_tasks.py` | 60 non-blank lines |
| `tests/unit/infrastructure/test_agent_db_policy_misc.py` | 188 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/application/test_memory_and_task_runner.py`

122 non-blank lines; it defines `test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten`, `test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first`, `test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects`, `Admin`, `runner`, `test_the_task_file_has_the_lessons_mix_and_each_expected_state_is_what_the_calendar_search_finds`, `test_all_thirty_tasks_reach_their_expected_end_state_with_no_write_lacking_an_approval`, `test_a_wrong_proposal_is_rejected_by_the_person_and_the_calendar_stays_as_it_was`, `test_the_task_report_lists_pass_rates_and_the_totals`, `test_a_stop_request_ends_the_run_all_loop_between_attempts`, `test_a_fact_told_in_an_earlier_session_decides_where_the_meeting_lands`, `test_there_are_ten_fact_and_task_pairs_and_one_of_them_changes_a_preference`.

`tests/unit/application/test_memory_and_task_runner.py`, lines 1 to 14:

```python
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
```

- Makes the module `dataclasses` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `ExpectedWritesApprover` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.), `TaskRunner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.) from the project module `scheduling_agent.application.task_runner`.
- Brings in `Action` (The three writes.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Brings in `TaskKind` (The five kinds of task in the set.), `TaskSpec` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.), `expected_end_state` (The seeded calendar with the task's removals and additions applied, as comparable keys.) from the project module `scheduling_agent.domain.tasks`.
- Brings in `reset_calendar` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).) from the project module `scheduling_agent.infrastructure.calendar_seed`.
- Brings in `load_tasks` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.) from the project module `scheduling_agent.infrastructure.files`.
- Brings in `REPO`, `FixedClock` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.), `build_kit`, `new_calendar` from the project module `tests.conftest`.
- Defines the function `test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten`.
- It takes no parameters.

`tests/unit/application/test_memory_and_task_runner.py`, lines 15 to 26:

```python
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
```

- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Checks that `kit.memory.remember('alice', 'I like coffee', 's1') is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Checks that `kit.memory.facts() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `facts` of `kit.memory`.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Checks that `len(kit.memory.facts()) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `facts` of `kit.memory`.
- Checks that `kit.memory.forget('alice') == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `forget` of the project's `MemoryService` (Delete every fact about a person from storage; returns how many were removed.).
- Checks that `[f.person for f in kit.memory.facts()] == ['bob']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `kit.memory`.
- Defines the function `test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.

`tests/unit/application/test_memory_and_task_runner.py`, lines 27 to 40:

```python
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
```

- Loop: the indented lines below run once for each item of `(('alice', 'nothing before 10'), ('alice', 'No meetings o...`; `(person, text)` names the current item.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Stores the result of calling `kit.memory.recall` under the name `recalled`.
  - The method `recall` of the project's `MemoryService` (The most relevant live facts for a task: those of the people it names, ranked by similarity and recency.).
- Checks that `len(recalled) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `{f.person for f in recalled} <= {'alice', 'bob'}` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `kit.memory.recall('Book 30 minutes with dave') == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `recall` of the project's `MemoryService` (The most relevant live facts for a task: those of the people it names, ranked by similarity and recency.).
- Stores the result of calling `kit.memory.recall` under the name `everyone`.
  - The method `recall` of the project's `MemoryService` (The most relevant live facts for a task: those of the people it names, ranked by similarity and recency.).
- Checks that `len(everyone) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).

`tests/unit/application/test_memory_and_task_runner.py`, lines 43 to 52:

```python
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
```

- Defines the function `test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects`.
- It takes no parameters.
- Stores the result of calling `TaskSpec` under the name `task`.
  - `TaskSpec` from the project's `scheduling_agent.domain.tasks` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.).
- Stores the result of calling `ExpectedWritesApprover` under the name `approver`.
  - `ExpectedWritesApprover` from the project's `scheduling_agent.application.task_runner` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.).
- Stores the result of calling `Proposal` under the name `book`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `wrong_time`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `cancel`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `other_cancel`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `move`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).

`tests/unit/application/test_memory_and_task_runner.py`, lines 53 to 66:

```python
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
```

- Checks that `[approver.decide(task, p) for p in (book, wrong_time, cancel, other_cancel, m...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `decide` of `approver`.
- Defines the class `Admin`.
- Defines the method `__init__`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `calendar`.
- Stores the value named `calendar` under the name `self._calendar` (as an attribute of this object, so other methods can use it).
- Defines the method `reset`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`tests/unit/application/test_memory_and_task_runner.py`, lines 67 to 80:

```python
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
```

- Calls `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).) with 2 argument(s); the result is not kept.
  - `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).).
  - `/` is divide.
- Defines the function `runner`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `TaskRunner` from the project's `scheduling_agent.application.task_runner` (Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects.).
  - `Admin`, a class of this project.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ExpectedWritesApprover` from the project's `scheduling_agent.application.task_runner` (Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
  - `build_kit` from the project's `tests.conftest`.
- Defines the function `test_the_task_file_has_the_lessons_mix_and_each_expected_state_is_what_the_calendar_search_finds`.
- It takes no parameters.
- Stores the result of calling `load_tasks` under the name `tasks`.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.
- Checks that `len(tasks) == 30` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `sum((bool(t.facts) for t in tasks)) >= 10` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `bool` turns a value into true or false.

`tests/unit/application/test_memory_and_task_runner.py`, lines 81 to 94:

```python
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
```

- Loop: the indented lines below run once for each item of `tasks`; `task` names the current item.
- Decision: the indented lines below run only when `task.kind is TaskKind.IMPOSSIBLE` is true.
  - `is` means the very same object.
- Checks that `not task.add` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Checks that `not task.remove` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- `else:` — the indented lines below run when none of the conditions above were true.
- Checks that `task.add or task.remove` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the function `test_all_thirty_tasks_reach_their_expected_end_state_with_no_write_lacking_an_approval`.
- It takes no parameters.
- Stores the result of calling `load_tasks` under the name `tasks`.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.
- Stores the result of calling `runner` under the name `(task_runner, _)`.
  - `runner`, a function of this file.
- Stores the result of calling `task_runner.run_all` under the name `results`.
  - The method `run_all` of the project's `TaskRunner` (Every task `repeats` times, in order.).
- Checks that `len(results) == 30` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores a list built by looping under the name `failed`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `not` flips true and false.

`tests/unit/application/test_memory_and_task_runner.py`, lines 95 to 105:

```python
    assert failed == []
    assert sum(r.writes_without_approval for r in results) == 0
    assert sum(r.approvals_rejected for r in results) == 0
    impossible = [r for r in results if r.task_id.startswith("t-impossible")]
    assert all(r.approvals_granted == 0 for r in impossible)
    assert {(r.status, r.stop_reason) for r in impossible} == {(RunStatus.DONE, ""), (RunStatus.STOPPED, "steps")}


def test_a_wrong_proposal_is_rejected_by_the_person_and_the_calendar_stays_as_it_was():
    task_runner, calendar = runner()
    seed_keys = {e.key() for e in calendar.active_events()}
```

- Checks that `failed == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `sum((r.writes_without_approval for r in results)) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `sum((r.approvals_rejected for r in results)) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores a list built by looping under the name `impossible`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.startswith(...)` asks whether text begins with the given text.
- Checks that `all((r.approvals_granted == 0 for r in impossible))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Checks that `{(r.status, r.stop_reason) for r in impossible} == {(RunStatus.DONE, ''), (Ru...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_a_wrong_proposal_is_rejected_by_the_person_and_the_calendar_stays_as_it_was`.
- It takes no parameters.
- Stores the result of calling `runner` under the name `(task_runner, calendar)`.
  - `runner`, a function of this file.
- Stores a set built by looping under the name `seed_keys`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - The method `active_events` of `calendar`.

`tests/unit/application/test_memory_and_task_runner.py`, lines 106 to 117:

```python
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
```

- Stores the result of calling `TaskSpec` under the name `impostor`.
  - `TaskSpec` from the project's `scheduling_agent.domain.tasks` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.).
- Stores the result of calling `task_runner.run_once` under the name `result`.
  - The method `run_once` of the project's `TaskRunner` (One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task.).
- Checks that `result.approvals_rejected >= 1` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
- Checks that `not result.passed or {e.key() for e in calendar.active_events()} != seed_keys` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `!=` means not equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - The method `active_events` of `calendar`.
- Checks that `expected_end_state(calendar.active_events(), impostor)` is true; if it is not, the test fails with an `AssertionError`.
  - `expected_end_state` from the project's `scheduling_agent.domain.tasks` (The seeded calendar with the task's removals and additions applied, as comparable keys.).
  - The method `active_events` of `calendar`.

`tests/unit/application/test_memory_and_task_runner.py`, lines 120 to 131:

```python
def test_the_task_report_lists_pass_rates_and_the_totals():
    from scheduling_agent.interfaces.cli import render_task_report

    tasks = load_tasks(REPO / "data" / "tasks.jsonl")[:3]
    task_runner, _ = runner()
    text = render_task_report(task_runner.run_all(tasks, repeats=2), 2)
    assert "tasks passed: 6/6 attempts (3 tasks x 2 runs)" in text
    assert "writes without an approval: 0" in text


def test_a_stop_request_ends_the_run_all_loop_between_attempts():
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")[:3]
```

- Defines the function `test_the_task_report_lists_pass_rates_and_the_totals`.
- It takes no parameters.
- Brings in `render_task_report` (Pass rate per task across the runs, and the totals the lesson asks for.) from the project module `scheduling_agent.interfaces.cli`.
- Stores the part of `load_tasks(REPO / 'data' / ...` picked by `:3` under the name `tasks`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.
- Stores the result of calling `runner` under the name `(task_runner, _)`.
  - `runner`, a function of this file.
- Stores the result of calling `render_task_report` under the name `text`.
  - `render_task_report` from the project's `scheduling_agent.interfaces.cli` (Pass rate per task across the runs, and the totals the lesson asks for.).
  - The method `run_all` of the project's `TaskRunner` (Every task `repeats` times, in order.).
- Checks that `'tasks passed: 6/6 attempts (3 tasks x 2 runs)' in text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'writes without an approval: 0' in text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_a_stop_request_ends_the_run_all_loop_between_attempts`.
- It takes no parameters.
- Stores the part of `load_tasks(REPO / 'data' / ...` picked by `:3` under the name `tasks`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.

`tests/unit/application/test_memory_and_task_runner.py`, lines 132 to 145:

```python
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
```

- Stores the result of calling `runner` under the name `(task_runner, _)`.
  - `runner`, a function of this file.
- Stores the result of calling `iter` under the name `stops`.
  - `iter` makes an iterator over a collection.
- Checks that `len(task_runner.run_all(tasks, repeats=1, stop_requested=lambda: next(stops))...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `run_all` of the project's `TaskRunner` (Every task `repeats` times, in order.).
  - `lambda args: expression` is a small unnamed function written inline.
  - `next` takes the next item from an iterator.
- Stores a list built by looping under the name `FACT_TASKS`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `load_tasks` from the project's `scheduling_agent.infrastructure.files` (Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked.).
  - `/` is divide.
- Defines the function `test_a_fact_told_in_an_earlier_session_decides_where_the_meeting_lands`. `@pytest.mark.parametrize` runs the test once for each row of values listed. The author's own description: "The ten fact-and-task pairs: with the fact the end state is the expected one; without it, it is not."
- Its parameters:
    - `task`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `runner` under the name `(task_runner, _)`.
  - `runner`, a function of this file.
- Checks that `task_runner.run_once(task, 1).passed` is true; if it is not, the test fails with an `AssertionError`.
  - The method `run_once` of the project's `TaskRunner` (One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task.).
- Stores the result of calling `dataclasses.replace` under the name `forgotten`.
  - `dataclasses.replace` makes a copy of a frozen object with some fields changed.

`tests/unit/application/test_memory_and_task_runner.py`, lines 146 to 152:

```python
    assert not task_runner.run_once(forgotten, 1).passed


def test_there_are_ten_fact_and_task_pairs_and_one_of_them_changes_a_preference():
    assert len(FACT_TASKS) == 10
    changed = [t for t in FACT_TASKS if len({person for person, _ in t.facts}) < len(t.facts)]
    assert [t.id for t in changed] == ["t-book-05"]
```

- Checks that `not task_runner.run_once(forgotten, 1).passed` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - The method `run_once` of the project's `TaskRunner` (One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task.).
- Defines the function `test_there_are_ten_fact_and_task_pairs_and_one_of_them_changes_a_preference`.
- It takes no parameters.
- Checks that `len(FACT_TASKS) == 10` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores a list built by looping under the name `changed`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `<` means less than.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `[t.id for t in changed] == ['t-book-05']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

### `tests/unit/application/test_tools_and_agent.py`

245 non-blank lines; it defines `event_count`, `toolbox`, `book_proposal`, `test_the_tool_list_has_two_reads_and_three_writes_with_schemas`, `test_reads_return_slots_and_events_and_errors_the_model_can_read`, `test_a_proposal_snapshots_the_event_it_would_change`, `test_a_write_without_an_approval_id_changes_nothing_and_leaves_one_refused_audit_line`, `test_an_unknown_pending_or_mismatched_approval_does_not_open_the_write`, `test_an_approved_write_runs_once_and_a_second_attempt_with_the_same_key_creates_nothing_new`, `test_a_write_the_calendar_refuses_is_reported_as_failed_and_logged`, `test_deciding_twice_or_on_an_unknown_approval_is_an_error`, `test_a_booking_waits_for_a_person_then_is_written_and_the_run_ends_with_one_sentence`, ....

`tests/unit/application/test_tools_and_agent.py`, lines 1 to 13:

```python
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
```

- Brings in `datetime` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `AgentConfig` (The caps of a run and the size of one model answer.), `UnknownRun` (No saved run with that id.) from the project module `scheduling_agent.application.agent`.
- Brings in `ToolBox` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.), `tool_specs` (The tool definitions as the model sees them.) from the project module `scheduling_agent.application.tools`.
- Brings in `ApprovalError` (An approval is missing, not approved, or was granted for a different proposal.) from the project module `scheduling_agent.domain.errors`.
- Brings in `Action` (The three writes.), `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Brings in `NoFailPoints` (The production default: nothing ever fails on purpose.) from the project module `scheduling_agent.infrastructure.failpoints`.
- Brings in `Crash` (Raised by a test failpoint to stand in for the process dying at that point (nothing catches BaseException).), `FixedClock` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.), `RaiseAt` (A failpoint that raises `Crash` the first time execution reaches the named point.), `approve_all` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.), `build_kit`, `new_calendar` from the project module `tests.conftest`.
- Stores the text `Book a 30-minute meeting with alice and bob on ...` under the name `BOOK`.

`tests/unit/application/test_tools_and_agent.py`, lines 16 to 26:

```python
def event_count(calendar):
    return len(calendar.active_events())


def toolbox():
    kit = build_kit()
    return ToolBox(kit.calendar, kit.approvals, kit.audit, FixedClock(), NoFailPoints()), kit


def book_proposal(start="2026-11-03T11:00"):
    return Proposal(Action.BOOK, {"people": ["alice", "bob"], "start": start, "minutes": 30})
```

- Defines the function `event_count`.
- Its parameters:
    - `calendar`.
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
  - The method `active_events` of `calendar`.
- Defines the function `toolbox`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `ToolBox` from the project's `scheduling_agent.application.tools` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
  - `NoFailPoints` from the project's `scheduling_agent.infrastructure.failpoints` (The production default: nothing ever fails on purpose.).
- Defines the function `book_proposal`.
- Its parameters:
    - `start`; if the caller leaves it out it is the text `2026-11-03T11:00`.
- Ends the function and gives back the result of calling `Proposal` to the caller.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).

`tests/unit/application/test_tools_and_agent.py`, lines 29 to 40:

```python
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
```

- Defines the function `test_the_tool_list_has_two_reads_and_three_writes_with_schemas`.
- It takes no parameters.
- Stores a list built by looping under the name `names`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `tool_specs` from the project's `scheduling_agent.application.tools` (The tool definitions as the model sees them.).
- Checks that `names == ['find_free_slots', 'get_event', 'book_meeting', 'move_meeting', 'ca...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `all((t.parameters['type'] == 'object' for t in tool_specs()))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `tool_specs` from the project's `scheduling_agent.application.tools` (The tool definitions as the model sees them.).
- Defines the function `test_reads_return_slots_and_events_and_errors_the_model_can_read`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.
- Stores the result of calling `box.read` under the name `found`.
  - `.read(...)` reads from an open file.
- Checks that `found['count'] >= 1` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/application/test_tools_and_agent.py`, lines 41 to 52:

```python
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
```

- Checks that `len(found['slots']) <= 12` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `kit.calendar.active_events()` picked by `0` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `kit.calendar`.
- Checks that `box.read('get_event', {'event_id': event.id})['start'] == event.start.isoform...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `.read(...)` reads from an open file.
- Checks that `'UnknownPerson' in box.read('find_free_slots', {'people': ['zed'], 'first_day...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.read(...)` reads from an open file.
- Checks that `'UnknownEvent' in box.read('get_event', {'event_id': 'ev-9999'})['error']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.read(...)` reads from an open file.
- Checks that `'bad arguments' in box.read('find_free_slots', {'people': ['alice']})['error']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.read(...)` reads from an open file.
- Checks that `'unknown tool' in box.read('fly', {})['error']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.read(...)` reads from an open file.

`tests/unit/application/test_tools_and_agent.py`, lines 55 to 65:

```python
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
```

- Defines the function `test_a_proposal_snapshots_the_event_it_would_change`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.
- Stores the part of `kit.calendar.active_events()` picked by `0` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `kit.calendar`.
- Stores the result of calling `box.propose` under the name `cancel`.
  - The method `propose` of the project's `ToolBox` (Build the proposal for a write tool call, or an error result when the arguments or the target are bad.).
- Stores the result of calling `box.propose` under the name `move`.
  - The method `propose` of the project's `ToolBox` (Build the proposal for a write tool call, or an error result when the arguments or the target are bad.).
- Checks that `isinstance(cancel, Proposal)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `isinstance(move, Proposal)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `cancel.args['minutes'] == event.minutes` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `move.args['new_start'] == '2026-11-10T10:00'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'UnknownEvent' in box.propose('cancel_meeting', {'event_id': 'ev-9999'})['err...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `propose` of the project's `ToolBox` (Build the proposal for a write tool call, or an error result when the arguments or the target are bad.).
- Checks that `'bad arguments' in box.propose('book_meeting', {'people': ['alice']})['error']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `propose` of the project's `ToolBox` (Build the proposal for a write tool call, or an error result when the arguments or the target are bad.).

`tests/unit/application/test_tools_and_agent.py`, lines 68 to 79:

```python
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
```

- Defines the function `test_a_write_without_an_approval_id_changes_nothing_and_leaves_one_refused_audit_line`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `box.execute_write` under the name `result`.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
  - `book_proposal`, a function of this file.
- Checks that `result['status'] == 'refused'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
- Stores the result of calling `kit.audit.lines` under the name `lines`.
  - The method `lines` of `kit.audit`.
- Checks that `[(line.outcome, line.action) for line in lines] == [('refused', 'book')]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_an_unknown_pending_or_mismatched_approval_does_not_open_the_write`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.

`tests/unit/application/test_tools_and_agent.py`, lines 80 to 93:

```python
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
```

- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `book_proposal` under the name `proposal`.
  - `book_proposal`, a function of this file.
- Calls the method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.) with 3 argument(s); the result is not kept.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).
- Stores the part of `kit.approvals.pending()` picked by `0` under the name `approval`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `pending` of `kit.approvals`.
- Checks that `box.execute_write('run-x', 3, proposal, 'ap-unknown')['status'] == 'refused'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Checks that `'is pending' in box.execute_write('run-x', 3, proposal, approval.id)['detail']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `book_proposal` under the name `other`.
  - `book_proposal`, a function of this file.
- Checks that `'different proposal' in box.execute_write('run-x', 3, other, approval.id)['de...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
- Defines the function `test_an_approved_write_runs_once_and_a_second_attempt_with_the_same_key_creates_nothing_new`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.

`tests/unit/application/test_tools_and_agent.py`, lines 94 to 105:

```python
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
```

- Stores the result of calling `book_proposal` under the name `proposal`.
  - `book_proposal`, a function of this file.
- Calls the method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.) with 3 argument(s); the result is not kept.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).
- Stores the part of `kit.approvals.pending()` picked by `0` under the name `approval`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `pending` of `kit.approvals`.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `box.execute_write` under the name `first`.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Stores the result of calling `box.execute_write` under the name `second`.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Checks that `first['status'] == second['status'] == 'booked'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `first['event_id'] == second['event_id']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `(first['replayed'], second['replayed']) == (False, True)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `event_count(kit.calendar) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
  - `+` is add.
- Checks that `[line.outcome for line in kit.audit.lines('run-x')] == ['refused', 'written']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `lines` of `kit.audit`.

`tests/unit/application/test_tools_and_agent.py`, lines 108 to 119:

```python
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
```

- Defines the function `test_a_write_the_calendar_refuses_is_reported_as_failed_and_logged`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.
- Stores the part of `kit.calendar.active_events()` picked by `0` under the name `busy`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `kit.calendar`.
- Stores the result of calling `Proposal` under the name `proposal`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
  - `list` makes a list (a copy when given a collection).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Calls the method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.) with 3 argument(s); the result is not kept.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).
- Stores the part of `kit.approvals.pending()` picked by `0` under the name `approval`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `pending` of `kit.approvals`.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `box.execute_write` under the name `result`.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Checks that `result['status'] == 'failed'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/application/test_tools_and_agent.py`, lines 120 to 133:

```python
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
```

- Checks that `'SlotUnavailable' in result['error']` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `kit.audit.lines('run-x')[-1].outcome == 'failed'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `lines` of `kit.audit`.
- Defines the function `test_deciding_twice_or_on_an_unknown_approval_is_an_error`.
- It takes no parameters.
- Stores the result of calling `toolbox` under the name `(box, kit)`.
  - `toolbox`, a function of this file.
- Calls the method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.) with 3 argument(s); the result is not kept.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).
  - `book_proposal`, a function of this file.
- Stores the part of `kit.approvals.pending()` picked by `0` under the name `approval`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `pending` of `kit.approvals`.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- A `with` block: it sets up `pytest.raises(ApprovalError, match='already rejected')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- A `with` block: it sets up `pytest.raises(ApprovalError, match='unknown approval')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `box.request_approval` under the name `again`.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).
  - `book_proposal`, a function of this file.

`tests/unit/application/test_tools_and_agent.py`, lines 134 to 147:

```python
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
```

- Checks that `again['approval_id'] == approval.id` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_booking_waits_for_a_person_then_is_written_and_the_run_ends_with_one_sentence`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
- Checks that `state.status is RunStatus.AWAITING_APPROVAL` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `state.pending is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
- Checks that `[a.status for a in kit.approvals.pending()] == [ApprovalStatus.PENDING]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `pending` of `kit.approvals`.
- Stores the result of calling `approve_all` under the name `done`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
- Checks that `done.status is RunStatus.DONE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `done.final_text.startswith('Booked event ev-')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.

`tests/unit/application/test_tools_and_agent.py`, lines 148 to 161:

```python
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
```

- Checks that `event_count(kit.calendar) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
  - `+` is add.
- Checks that `[line.outcome for line in kit.audit.lines(state.run_id)] == ['refused', 'writ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `lines` of `kit.audit`.
- Checks that `len(done.writes_done) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_rejected_proposal_is_not_executed_and_the_run_says_so`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `kit.agent.resume` under the name `done`.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Checks that `done.status is RunStatus.DONE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `'rejected' in done.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.

`tests/unit/application/test_tools_and_agent.py`, lines 162 to 175:

```python
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
```

- Checks that `not any((line.outcome == 'written' for line in kit.audit.lines(state.run_id)))` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - The method `lines` of `kit.audit`.
- Defines the function `test_resuming_while_the_approval_is_still_pending_keeps_waiting_and_a_finished_run_stays_finished`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
- Checks that `kit.agent.resume(state.run_id).status is RunStatus.AWAITING_APPROVAL` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Stores the result of calling `approve_all` under the name `done`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
- Checks that `kit.agent.resume(state.run_id) == done` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- A `with` block: it sets up `pytest.raises(UnknownRun)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.) with 1 argument(s); the result is not kept.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Defines the function `test_a_move_cancels_the_old_event_and_books_the_new_one_after_approval`.
- It takes no parameters.

`tests/unit/application/test_tools_and_agent.py`, lines 176 to 189:

```python
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
```

- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the part of `kit.calendar.active_events()` picked by `2` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `kit.calendar`.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `state.pending is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Checks that `state.pending.proposal.action is Action.MOVE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Stores the result of calling `approve_all` under the name `done`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
- Checks that `done.final_text.startswith(f'Moved {event.id}')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores a set built by looping under the name `keys`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - The method `active_events` of `kit.calendar`.
- Checks that `event.key() not in keys` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
- Checks that `any((k[0] == tuple(sorted(event.people)) and k[1].startswith(('2026-11-09', '...` is true; if it is not, the test fails with an `AssertionError`.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `.startswith(...)` asks whether text begins with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `sorted` returns a new list with the items in order.
- Defines the function `test_a_cancel_is_a_proposal_too`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.

`tests/unit/application/test_tools_and_agent.py`, lines 190 to 203:

```python
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
```

- Stores the part of `kit.calendar.active_events()` picked by `0` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `kit.calendar`.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `state.pending is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Checks that `event.key() in {e.key() for e in kit.calendar.active_events()}` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `kit.calendar`.
- Calls `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.) with 2 argument(s); the result is not kept.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
- Checks that `event.key() not in {e.key() for e in kit.calendar.active_events()}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `kit.calendar`.
- Defines the function `test_a_person_outside_the_calendar_ends_the_run_with_no_write_and_no_proposal`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
- Checks that `state.status is RunStatus.DONE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `'changed nothing' in state.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/application/test_tools_and_agent.py`, lines 204 to 217:

```python
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
```

- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
- Checks that `kit.approvals.pending() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `pending` of `kit.approvals`.
- Defines the function `test_a_task_that_cannot_succeed_stops_at_the_step_cap_and_says_which_cap_fired`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
- Checks that `state.status is RunStatus.STOPPED` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `state.stop_reason == 'steps'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `state.steps == 12` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'step cap reached: 12/12' in state.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/application/test_tools_and_agent.py`, lines 218 to 231:

```python
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
```

- Checks that `'no write was made' in state.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `state.tokens < 4000` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
- Checks that `event_count(kit.calendar) == before` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
- Defines the function `test_the_token_cap_and_the_time_cap_each_stop_a_run_on_their_own`.
- It takes no parameters.
- Stores the result of calling `build_kit(config=AgentConfig(max_tokens=60)).ag...` under the name `tokens`.
  - `.start(...)` starts a thread or process.
  - `build_kit` from the project's `tests.conftest`.
  - `AgentConfig` from the project's `scheduling_agent.application.agent` (The caps of a run and the size of one model answer.).
- Checks that `(tokens.status, tokens.stop_reason) == (RunStatus.STOPPED, 'tokens')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'token cap reached' in tokens.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Stores the result of calling `build_kit(config=AgentConfig(max_seconds=2.0), ...` under the name `slow`.
  - `.start(...)` starts a thread or process.
  - `build_kit` from the project's `tests.conftest`.
  - `AgentConfig` from the project's `scheduling_agent.application.agent` (The caps of a run and the size of one model answer.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Checks that `(slow.status, slow.stop_reason) == (RunStatus.STOPPED, 'seconds')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'time cap reached' in slow.final_text` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/application/test_tools_and_agent.py`, lines 234 to 245:

```python
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
```

- Defines the function `test_what_a_person_said_in_an_earlier_session_is_used_in_a_later_run_and_a_changed_preference_replaces_it`.
- It takes no parameters.
- Stores the result of calling `build_kit` under the name `kit`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `approve_all` under the name `plain`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
  - `.start(...)` starts a thread or process.
- Stores the result of calling `datetime.fromisoformat` under the name `start_without`.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `next` takes the next item from an iterator.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `kit.calendar`.
  - `==` means equal.
  - `.rstrip(...)` removes spaces from the end of text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Stores the result of calling `build_kit` under the name `kit2`.
  - `build_kit` from the project's `tests.conftest`.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Stores the result of calling `approve_all` under the name `state`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
  - `.start(...)` starts a thread or process.

`tests/unit/application/test_tools_and_agent.py`, lines 246 to 259:

```python
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
```

- Stores the result of calling `next` under the name `booked`.
  - `next` takes the next item from an iterator.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `kit2.calendar`.
  - `==` means equal.
  - `.rstrip(...)` removes spaces from the end of text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.split(...)` cuts text into a list of pieces at a separator.
- Checks that `booked.start.hour >= 10` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
- Checks that `start_without.hour >= 9` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
- Checks that `[f.value for f in kit2.memory.facts() if f.person == 'alice'] == ['13:00']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `kit2.memory`.
- Checks that `kit2.memory.forget('alice') == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `forget` of the project's `MemoryService` (Delete every fact about a person from storage; returns how many were removed.).
- Checks that `kit2.memory.facts() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `facts` of `kit2.memory`.
- Defines the function `test_a_crash_at_any_point_then_a_resume_books_exactly_one_event`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `point`.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.

`tests/unit/application/test_tools_and_agent.py`, lines 260 to 273:

```python
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
```

- Stores the result of calling `event_count` under the name `before`.
  - `event_count`, a function of this file.
- Stores the result of calling `build_kit` under the name `first`.
  - `build_kit` from the project's `tests.conftest`.
  - `RaiseAt` from the project's `tests.conftest` (A failpoint that raises `Crash` the first time execution reaches the named point.).
- Stores the value named `first` under the name `store_kit`.
- A `with` block: it sets up `pytest.raises(Crash)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.) with 2 argument(s); the result is not kept.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
  - `.start(...)` starts a thread or process.
- Stores the result of calling `build_kit` under the name `second`.
  - `build_kit` from the project's `tests.conftest`.
- Stores one of two values, chosen by a condition under the name `state`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `in` means is contained in.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
  - `.start(...)` starts a thread or process.
  - The method `unfinished` of `second.checkpoints`.
- Stores the result of calling `approve_all` under the name `done`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
- Checks that `done.status is RunStatus.DONE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/application/test_tools_and_agent.py`, lines 274 to 287:

```python
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
```

- Checks that `event_count(calendar) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `event_count`, a function of this file.
  - `+` is add.
- Checks that `sum((line.outcome == 'written' for line in second.audit.lines('crash-run'))) ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `lines` of `second.audit`.
- Defines the function `test_a_crash_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume_without_a_duplicate`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the part of `calendar.active_events()` picked by `2` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `calendar`.
- Stores a text built from pieces (an f-string) under the name `task`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `build_kit` under the name `first`.
  - `build_kit` from the project's `tests.conftest`.
  - `RaiseAt` from the project's `tests.conftest` (A failpoint that raises `Crash` the first time execution reaches the named point.).
- A `with` block: it sets up `pytest.raises(Crash)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.) with 2 argument(s); the result is not kept.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
  - `.start(...)` starts a thread or process.
- Checks that `event.key() not in {e.key() for e in calendar.active_events()}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `calendar`.
- Stores the result of calling `build_kit` under the name `second`.
  - `build_kit` from the project's `tests.conftest`.
- Stores the result of calling `approve_all` under the name `done`.
  - `approve_all` from the project's `tests.conftest` (Play the person: approve every pending proposal of the run, resuming until the run stops waiting.).
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).

`tests/unit/application/test_tools_and_agent.py`, lines 288 to 292:

```python
    assert done.final_text.startswith(f"Moved {event.id}")
    moved = [
        e for e in calendar.active_events() if e.people == event.people and e.start.date().isoformat() >= "2026-11-09"
    ]
    assert len(moved) == 1
```

- Checks that `done.final_text.startswith(f'Moved {event.id}')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores a list built by looping under the name `moved`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `calendar`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - The method `date` of `e.start`.
- Checks that `len(moved) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).

### `tests/unit/domain/test_calendar_memory_budget.py`

148 non-blank lines; it defines `at`, `test_a_valid_slot_passes_and_each_rule_names_what_it_broke`, `test_overlap_is_half_open_so_back_to_back_meetings_do_not_collide`, `test_an_event_has_an_end_and_a_key_that_ignores_its_id`, `test_free_slots_skip_busy_time_weekends_and_respect_the_requested_hours`, `test_free_slots_can_skip_whole_weekdays`, `test_statements_a_person_makes_become_facts`, `test_a_sentence_that_states_nothing_we_keep_is_not_a_fact`, `test_a_changed_preference_replaces_the_old_fact_instead_of_sitting_beside_it`, `test_facts_about_different_topics_or_people_live_side_by_side`, `test_saying_a_day_is_fine_again_retracts_the_avoid_day_fact_and_stores_nothing`, `test_lapsed_facts_are_dropped_on_write_and_never_recalled`, ....

`tests/unit/domain/test_calendar_memory_budget.py`, lines 1 to 7:

```python
from datetime import date, datetime, time, timedelta

import pytest

from scheduling_agent.domain.budget import Budget
from scheduling_agent.domain.calendar import Event, free_slots, overlaps, validate_slot
from scheduling_agent.domain.errors import BudgetExceeded, InvalidSlot
```

- Brings in `date`, `datetime`, `time`, `timedelta` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `Budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.) from the project module `scheduling_agent.domain.budget`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.), `free_slots` (Start times, earliest first, at which every listed person is free for `minutes`.), `overlaps` (True when two half-open intervals share any time.), `validate_slot` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `BudgetExceeded` (A run hit one of its caps: steps, tokens or wall-clock time.), `InvalidSlot` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.) from the project module `scheduling_agent.domain.errors`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 8 to 19:

```python
from scheduling_agent.domain.memory import (
    Constraints,
    FactKind,
    compact,
    parse_statement,
    rank_facts,
    recall_score,
)
from scheduling_agent.domain.proposals import Action, Proposal, write_key

TODAY = date(2026, 10, 27)
MON = date(2026, 11, 2)
```

- Brings in `Constraints` (What recalled facts mean for a search: earliest start, latest end and weekdays to avoid.), `FactKind` (What a fact constrains.), `compact` (The facts to keep after writing `new`.), `parse_statement` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.), `rank_facts` (The `top` live facts with the best blended score, best first (ties broken by newer first, then text).), `recall_score` (Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`.) from the project module `scheduling_agent.domain.memory`.
- Brings in `Action` (The three writes.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.), `write_key` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.) from the project module `scheduling_agent.domain.proposals`.
- Stores the result of calling `date` under the name `TODAY`.
  - `date` from the standard library module `datetime`.
- Stores the result of calling `date` under the name `MON`.
  - `date` from the standard library module `datetime`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 22 to 28:

```python
def at(hour, minute=0, day=MON):
    return datetime.combine(day, time(hour, minute))


def test_a_valid_slot_passes_and_each_rule_names_what_it_broke():
    validate_slot(at(9), 30)
    validate_slot(at(16, 30), 30)
```

- Defines the function `at`.
- Its parameters:
    - `hour`.
    - `minute`; if the caller leaves it out it is the number `0`.
    - `day`; if the caller leaves it out it is the value named `MON`.
- Ends the function and gives back the result of calling `datetime.combine` to the caller.
  - `datetime.combine` from the standard library module `datetime`.
  - `time` from the standard library module `datetime`.
- Defines the function `test_a_valid_slot_passes_and_each_rule_names_what_it_broke`.
- It takes no parameters.
- Calls `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) with 2 argument(s); the result is not kept.
  - `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.).
  - `at`, a function of this file.
- Calls `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) with 2 argument(s); the result is not kept.
  - `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.).
  - `at`, a function of this file.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 29 to 42:

```python
    for start, minutes, message in [
        (at(9, 15), 30, "half hour"),
        (at(8, 30), 30, "outside working hours"),
        (at(16, 30), 60, "outside working hours"),
        (at(9, day=date(2026, 11, 7)), 30, "weekend"),
        (at(9), 45, "multiple of 30"),
        (at(9), 300, "multiple of 30"),
    ]:
        with pytest.raises(InvalidSlot, match=message):
            validate_slot(start, minutes)


def test_overlap_is_half_open_so_back_to_back_meetings_do_not_collide():
    assert overlaps(at(9), at(10), at(9, 30), at(10, 30))
```

- Loop: the indented lines below run once for each item of `[(at(9, 15), 30, 'half hour'), (at(8, 30), 30, 'outside w...`; `(start, minutes, message)` names the current item.
  - `at`, a function of this file.
  - `date` from the standard library module `datetime`.
- A `with` block: it sets up `pytest.raises(InvalidSlot, match=message)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.) with 2 argument(s); the result is not kept.
  - `validate_slot` from the project's `scheduling_agent.domain.calendar` (Raise `InvalidSlot` unless the slot is a weekday, on the half-hour grid, inside working hours.).
- Defines the function `test_overlap_is_half_open_so_back_to_back_meetings_do_not_collide`.
- It takes no parameters.
- Checks that `overlaps(at(9), at(10), at(9, 30), at(10, 30))` is true; if it is not, the test fails with an `AssertionError`.
  - `overlaps` from the project's `scheduling_agent.domain.calendar` (True when two half-open intervals share any time.).
  - `at`, a function of this file.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 43 to 56:

```python
    assert not overlaps(at(9), at(10), at(10), at(11))


def test_an_event_has_an_end_and_a_key_that_ignores_its_id():
    event = Event("ev-1", ("bob", "alice"), at(10), 60)
    assert event.end == at(11)
    assert event.key() == (("alice", "bob"), "2026-11-02T10:00", 60)
    assert event.key() == Event("ev-2", ("alice", "bob"), at(10), 60).key()


def test_free_slots_skip_busy_time_weekends_and_respect_the_requested_hours():
    busy = {"alice": [(at(9), at(10))], "bob": [(at(10), at(11))]}
    slots = free_slots(busy, ["alice", "bob"], MON, MON, 30)
    assert slots[0] == at(11)
```

- Checks that `not overlaps(at(9), at(10), at(10), at(11))` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - `overlaps` from the project's `scheduling_agent.domain.calendar` (True when two half-open intervals share any time.).
  - `at`, a function of this file.
- Defines the function `test_an_event_has_an_end_and_a_key_that_ignores_its_id`.
- It takes no parameters.
- Stores the result of calling `Event` under the name `event`.
  - `Event` from the project's `scheduling_agent.domain.calendar` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.).
  - `at`, a function of this file.
- Checks that `event.end == at(11)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `at`, a function of this file.
- Checks that `event.key() == (('alice', 'bob'), '2026-11-02T10:00', 60)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
- Checks that `event.key() == Event('ev-2', ('alice', 'bob'), at(10), 60).key()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - `Event` from the project's `scheduling_agent.domain.calendar` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.).
  - `at`, a function of this file.
- Defines the function `test_free_slots_skip_busy_time_weekends_and_respect_the_requested_hours`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `busy`.
  - `at`, a function of this file.
- Stores the result of calling `free_slots` under the name `slots`.
  - `free_slots` from the project's `scheduling_agent.domain.calendar` (Start times, earliest first, at which every listed person is free for `minutes`.).
- Checks that `slots[0] == at(11)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `at`, a function of this file.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 57 to 66:

```python
    assert at(9) not in slots
    assert at(10, 30) not in slots
    assert free_slots({}, ["alice"], date(2026, 11, 7), date(2026, 11, 8), 30) == []
    narrowed = free_slots({}, ["alice"], MON, MON, 60, not_before=time(13), not_after=time(15))
    assert narrowed == [at(13), at(13, 30), at(14)]


def test_free_slots_can_skip_whole_weekdays():
    slots = free_slots({}, ["alice"], MON, MON + timedelta(days=1), 30, avoid_weekdays={0})
    assert {s.date() for s in slots} == {MON + timedelta(days=1)}
```

- Checks that `at(9) not in slots` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `at`, a function of this file.
- Checks that `at(10, 30) not in slots` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `at`, a function of this file.
- Checks that `free_slots({}, ['alice'], date(2026, 11, 7), date(2026, 11, 8), 30) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `free_slots` from the project's `scheduling_agent.domain.calendar` (Start times, earliest first, at which every listed person is free for `minutes`.).
  - `date` from the standard library module `datetime`.
- Stores the result of calling `free_slots` under the name `narrowed`.
  - `free_slots` from the project's `scheduling_agent.domain.calendar` (Start times, earliest first, at which every listed person is free for `minutes`.).
  - `time` from the standard library module `datetime`.
- Checks that `narrowed == [at(13), at(13, 30), at(14)]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `at`, a function of this file.
- Defines the function `test_free_slots_can_skip_whole_weekdays`.
- It takes no parameters.
- Stores the result of calling `free_slots` under the name `slots`.
  - `free_slots` from the project's `scheduling_agent.domain.calendar` (Start times, earliest first, at which every listed person is free for `minutes`.).
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Checks that `{s.date() for s in slots} == {MON + timedelta(days=1)}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `date` of `s`.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 69 to 82:

```python
@pytest.mark.parametrize(
    ("statement", "kind", "value"),
    [
        ("I never want meetings before 10", FactKind.EARLIEST_START, "10:00"),
        ("No meetings before 10:30", FactKind.EARLIEST_START, "10:30"),
        ("nothing before 9am", FactKind.EARLIEST_START, "09:00"),
        ("No meetings after 4pm", FactKind.LATEST_END, "16:00"),
        ("nothing after 4", FactKind.LATEST_END, "16:00"),
        ("No meetings on Fridays", FactKind.AVOID_DAY, "4"),
        ("Mondays are off", FactKind.AVOID_DAY, "0"),
        ("Fridays are fine again", FactKind.ALLOW_DAY, "4"),
    ],
)
def test_statements_a_person_makes_become_facts(statement, kind, value):
```

- Defines the function `test_statements_a_person_makes_become_facts`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `statement`.
    - `kind`.
    - `value`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 83 to 96:

```python
    fact = parse_statement("alice", statement, "s1", TODAY)
    assert fact is not None
    assert (fact.kind, fact.value) == (kind, value)
    assert fact.expires_on == TODAY + timedelta(days=365)


def test_a_sentence_that_states_nothing_we_keep_is_not_a_fact():
    assert parse_statement("alice", "I like coffee", "s1", TODAY) is None


def test_a_changed_preference_replaces_the_old_fact_instead_of_sitting_beside_it():
    old = parse_statement("alice", "no meetings before 9", "s1", TODAY)
    new = parse_statement("alice", "actually nothing before 11", "s2", TODAY)
    assert old
```

- Stores the result of calling `parse_statement` under the name `fact`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `fact is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Checks that `(fact.kind, fact.value) == (kind, value)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `fact.expires_on == TODAY + timedelta(days=365)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Defines the function `test_a_sentence_that_states_nothing_we_keep_is_not_a_fact`.
- It takes no parameters.
- Checks that `parse_statement('alice', 'I like coffee', 's1', TODAY) is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Defines the function `test_a_changed_preference_replaces_the_old_fact_instead_of_sitting_beside_it`.
- It takes no parameters.
- Stores the result of calling `parse_statement` under the name `old`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Stores the result of calling `parse_statement` under the name `new`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `old` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 97 to 110:

```python
    assert new
    kept = compact([old], new, TODAY)
    assert kept == [new]
    assert compact(kept, new, TODAY) == [new]  # a repeat merges into one


def test_facts_about_different_topics_or_people_live_side_by_side():
    start = parse_statement("alice", "nothing before 10", "s1", TODAY)
    end = parse_statement("alice", "nothing after 4pm", "s1", TODAY)
    other = parse_statement("bob", "nothing before 11", "s1", TODAY)
    assert start
    assert end
    assert other
    assert len(compact(compact([start], end, TODAY), other, TODAY)) == 3
```

- Checks that `new` is true; if it is not, the test fails with an `AssertionError`.
- Stores the result of calling `compact` under the name `kept`.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
- Checks that `kept == [new]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `compact(kept, new, TODAY) == [new]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
- Defines the function `test_facts_about_different_topics_or_people_live_side_by_side`.
- It takes no parameters.
- Stores the result of calling `parse_statement` under the name `start`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Stores the result of calling `parse_statement` under the name `end`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Stores the result of calling `parse_statement` under the name `other`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `start` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `end` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `other` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `len(compact(compact([start], end, TODAY), other, TODAY)) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).

`tests/unit/domain/test_calendar_memory_budget.py`, lines 113 to 124:

```python
def test_saying_a_day_is_fine_again_retracts_the_avoid_day_fact_and_stores_nothing():
    avoid = parse_statement("carol", "No meetings on Fridays", "s1", TODAY)
    allow = parse_statement("carol", "Fridays are fine again", "s2", TODAY)
    assert avoid
    assert allow
    assert compact([avoid], allow, TODAY) == []


def test_lapsed_facts_are_dropped_on_write_and_never_recalled():
    old = parse_statement("alice", "nothing before 10", "s1", TODAY - timedelta(days=400))
    fresh = parse_statement("bob", "nothing before 11", "s2", TODAY)
    assert old
```

- Defines the function `test_saying_a_day_is_fine_again_retracts_the_avoid_day_fact_and_stores_nothing`.
- It takes no parameters.
- Stores the result of calling `parse_statement` under the name `avoid`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Stores the result of calling `parse_statement` under the name `allow`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `avoid` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `allow` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `compact([avoid], allow, TODAY) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
- Defines the function `test_lapsed_facts_are_dropped_on_write_and_never_recalled`.
- It takes no parameters.
- Stores the result of calling `parse_statement` under the name `old`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
  - `-` is subtract.
  - `timedelta` from the standard library module `datetime`.
- Stores the result of calling `parse_statement` under the name `fresh`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `old` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 125 to 138:

```python
    assert fresh
    assert not old.alive(TODAY)
    assert compact([old], fresh, TODAY) == [fresh]
    assert rank_facts([(old, 0.9), (fresh, 0.1)], TODAY) == [fresh]


def test_recall_blends_similarity_with_recency_and_returns_the_best_three():
    base = parse_statement("alice", "nothing before 10", "s", TODAY)
    assert base
    old = parse_statement("bob", "nothing before 10", "s", TODAY - timedelta(days=360))
    assert old
    assert recall_score(0.8, TODAY, TODAY) > recall_score(0.8, TODAY - timedelta(days=360), TODAY)
    assert recall_score(0.9, TODAY - timedelta(days=360), TODAY) > recall_score(0.1, TODAY, TODAY) - 1
    facts = [parse_statement("alice", f"nothing before {h}", "s", TODAY) for h in (9, 10, 11, 12)]
```

- Checks that `fresh` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `not old.alive(TODAY)` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
  - The method `alive` of `old`.
- Checks that `compact([old], fresh, TODAY) == [fresh]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
- Checks that `rank_facts([(old, 0.9), (fresh, 0.1)], TODAY) == [fresh]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `rank_facts` from the project's `scheduling_agent.domain.memory` (The `top` live facts with the best blended score, best first (ties broken by newer first, then text).).
- Defines the function `test_recall_blends_similarity_with_recency_and_returns_the_best_three`.
- It takes no parameters.
- Stores the result of calling `parse_statement` under the name `base`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Checks that `base` is true; if it is not, the test fails with an `AssertionError`.
- Stores the result of calling `parse_statement` under the name `old`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
  - `-` is subtract.
  - `timedelta` from the standard library module `datetime`.
- Checks that `old` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `recall_score(0.8, TODAY, TODAY) > recall_score(0.8, TODAY - timedelta(days=36...` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `recall_score` from the project's `scheduling_agent.domain.memory` (Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`.).
  - `-` is subtract.
  - `timedelta` from the standard library module `datetime`.
- Checks that `recall_score(0.9, TODAY - timedelta(days=360), TODAY) > recall_score(0.1, TOD...` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `recall_score` from the project's `scheduling_agent.domain.memory` (Embedding similarity blended with recency: a fact loses half its recency weight every `half_life_days`.).
  - `-` is subtract.
  - `timedelta` from the standard library module `datetime`.
- Stores a list built by looping under the name `facts`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 139 to 152:

```python
    ranked = rank_facts([(f, s) for f, s in zip(facts, (0.1, 0.4, 0.9, 0.6), strict=True) if f], TODAY)
    assert [f.value for f in ranked] == ["11:00", "12:00", "10:00"]


def test_constraints_take_the_strictest_value_among_the_people_in_the_meeting():
    facts = [
        parse_statement("alice", "nothing before 10", "s", TODAY),
        parse_statement("bob", "nothing before 11", "s", TODAY),
        parse_statement("bob", "nothing after 3pm", "s", TODAY),
        parse_statement("carol", "No meetings on Fridays", "s", TODAY),
        parse_statement("dave", "nothing before 13", "s", TODAY),
    ]
    c = Constraints.from_facts([f for f in facts if f], ["alice", "bob", "carol"])
    assert c == Constraints(time(11), time(15), frozenset({4}))
```

- Stores the result of calling `rank_facts` under the name `ranked`.
  - `rank_facts` from the project's `scheduling_agent.domain.memory` (The `top` live facts with the best blended score, best first (ties broken by newer first, then text).).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `zip` walks several collections side by side, item by item.
- Checks that `[f.value for f in ranked] == ['11:00', '12:00', '10:00']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_constraints_take_the_strictest_value_among_the_people_in_the_meeting`.
- It takes no parameters.
- Stores a list of 5 item(s) under the name `facts`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Stores the result of calling `Constraints.from_facts` under the name `c`.
  - The method `from_facts` of the project's `Constraints` (The strictest constraint of each kind among the facts of the people in the meeting.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `c == Constraints(time(11), time(15), frozenset({4}))` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `Constraints` from the project's `scheduling_agent.domain.memory` (What recalled facts mean for a search: earliest start, latest end and weekdays to avoid.).
  - `time` from the standard library module `datetime`.
  - `frozenset` makes a set that cannot be changed.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 153 to 166:

```python
    assert Constraints.from_facts([], ["alice"]) == Constraints()


def test_each_budget_cap_is_checked_on_its_own_and_names_itself():
    budget = Budget(max_steps=2, max_tokens=100, max_seconds=5.0, started_at=0.0)
    budget.check(1.0)
    budget.spend(10)
    budget.spend(10)
    with pytest.raises(BudgetExceeded, match=r"step cap reached: 2/2") as steps:
        budget.check(1.0)
    assert steps.value.cap == "steps"
    tokens = Budget(5, 50, 5.0, 0.0, steps=1, tokens=50)
    with pytest.raises(BudgetExceeded, match=r"token cap reached: 50/50"):
        tokens.check(1.0)
```

- Checks that `Constraints.from_facts([], ['alice']) == Constraints()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_facts` of the project's `Constraints` (The strictest constraint of each kind among the facts of the people in the meeting.).
  - `Constraints` from the project's `scheduling_agent.domain.memory` (What recalled facts mean for a search: earliest start, latest end and weekdays to avoid.).
- Defines the function `test_each_budget_cap_is_checked_on_its_own_and_names_itself`.
- It takes no parameters.
- Stores the result of calling `Budget` under the name `budget`.
  - `Budget` from the project's `scheduling_agent.domain.budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.).
- Calls the method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.) with 1 argument(s); the result is not kept.
  - The method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.).
- Calls the method `spend` of the project's `Budget` (Record one step and the tokens it used.) with 1 argument(s); the result is not kept.
  - The method `spend` of the project's `Budget` (Record one step and the tokens it used.).
- Calls the method `spend` of the project's `Budget` (Record one step and the tokens it used.) with 1 argument(s); the result is not kept.
  - The method `spend` of the project's `Budget` (Record one step and the tokens it used.).
- A `with` block: it sets up `pytest.raises(BudgetExceeded, match='step cap reached: 2/2')` as `steps`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.) with 1 argument(s); the result is not kept.
  - The method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.).
- Checks that `steps.value.cap == 'steps'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Stores the result of calling `Budget` under the name `tokens`.
  - `Budget` from the project's `scheduling_agent.domain.budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.).
- A `with` block: it sets up `pytest.raises(BudgetExceeded, match='token cap reached: 5...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.) with 1 argument(s); the result is not kept.
  - The method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.).

`tests/unit/domain/test_calendar_memory_budget.py`, lines 167 to 180:

```python
    with pytest.raises(BudgetExceeded, match=r"time cap reached") as late:
        Budget(5, 50, 5.0, 0.0).check(6.0)
    assert late.value.cap == "seconds"


def test_a_write_key_depends_only_on_run_and_step_and_a_move_gets_a_key_per_part():
    assert write_key("run-1", 4) == write_key("run-1", 4)
    assert write_key("run-1", 4) != write_key("run-1", 5)
    assert write_key("run-1", 4) != write_key("run-2", 4)
    assert len({write_key("run-1", 4), write_key("run-1", 4, "cancel"), write_key("run-1", 4, "book")}) == 3
    assert len(write_key("a", 1)) == 64


def test_the_same_proposal_has_the_same_digest_whatever_the_argument_order():
```

- A `with` block: it sets up `pytest.raises(BudgetExceeded, match='time cap reached')` as `late`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.) with 1 argument(s); the result is not kept.
  - The method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.).
  - `Budget` from the project's `scheduling_agent.domain.budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.).
- Checks that `late.value.cap == 'seconds'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_write_key_depends_only_on_run_and_step_and_a_move_gets_a_key_per_part`.
- It takes no parameters.
- Checks that `write_key('run-1', 4) == write_key('run-1', 4)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Checks that `write_key('run-1', 4) != write_key('run-1', 5)` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Checks that `write_key('run-1', 4) != write_key('run-2', 4)` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Checks that `len({write_key('run-1', 4), write_key('run-1', 4, 'cancel'), write_key('run-1...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Checks that `len(write_key('a', 1)) == 64` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Defines the function `test_the_same_proposal_has_the_same_digest_whatever_the_argument_order`.
- It takes no parameters.

`tests/unit/domain/test_calendar_memory_budget.py`, lines 181 to 185:

```python
    a = Proposal(Action.BOOK, {"people": ["a"], "start": "2026-11-02T10:00", "minutes": 30})
    b = Proposal(Action.BOOK, {"minutes": 30, "start": "2026-11-02T10:00", "people": ["a"]})
    c = Proposal(Action.BOOK, {"people": ["a"], "start": "2026-11-02T10:30", "minutes": 30})
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()
```

- Stores the result of calling `Proposal` under the name `a`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `b`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `Proposal` under the name `c`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Checks that `a.digest() == b.digest()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `digest` of `a`.
  - The method `digest` of `b`.
- Checks that `a.digest() != c.digest()` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `digest` of `a`.
  - The method `digest` of `c`.

### `tests/unit/domain/test_llm.py`

22 non-blank lines; it defines `request`, `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, `test_tools_and_schemas_change_the_fingerprint`, `test_a_response_survives_a_json_round_trip_with_tool_calls`.

`tests/unit/domain/test_llm.py`, lines 1 to 14:

```python
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, ToolCall, ToolSpec, Usage


def request(**changes):
    base = {"messages": (ChatMessage.user("hello"),), "max_output_tokens": 50, "tag": "a"}
    return ChatRequest(**{**base, **changes})


def test_the_same_request_always_has_the_same_fingerprint():
    assert request().fingerprint() == request().fingerprint()


def test_the_model_name_is_not_part_of_the_fingerprint():
    assert request(model="a-model").fingerprint() == request(model="another").fingerprint()
```

- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.
- Defines the function `request`.
- Its parameters:
    - `**changes` collects any extra named arguments into a dictionary.
- Stores a dictionary with 3 entries under the name `base`.
  - The method `user` of `ChatMessage`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- Defines the function `test_the_same_request_always_has_the_same_fingerprint`.
- It takes no parameters.
- Checks that `request().fingerprint() == request().fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_the_model_name_is_not_part_of_the_fingerprint`.
- It takes no parameters.
- Checks that `request(model='a-model').fingerprint() == request(model='another').fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.

`tests/unit/domain/test_llm.py`, lines 17 to 27:

```python
def test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint():
    base = request().fingerprint()
    assert request(tag="b").fingerprint() != base
    assert request(temperature=0.7).fingerprint() != base
    assert request(top_p=0.9).fingerprint() != base


def test_tools_and_schemas_change_the_fingerprint():
    base = request().fingerprint()
    assert request(response_schema={"type": "object"}).fingerprint() != base
    assert request(tools=(ToolSpec("t", "d", {"type": "object"}),)).fingerprint() != base
```

- Defines the function `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tag='b').fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(temperature=0.7).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(top_p=0.9).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_tools_and_schemas_change_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(response_schema={'type': 'object'}).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tools=(ToolSpec('t', 'd', {'type': 'object'}),)).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
  - `ToolSpec` from the project's `scheduling_agent.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).

`tests/unit/domain/test_llm.py`, lines 30 to 34:

```python
def test_a_response_survives_a_json_round_trip_with_tool_calls():
    response = ChatResponse(
        "text", StopReason.TOOL_CALLS, Usage(5, 7), 1.25, "m", (ToolCall("c1", "lookup", {"id": 4}),)
    )
    assert ChatResponse.from_json(response.to_json()) == response
```

- Defines the function `test_a_response_survives_a_json_round_trip_with_tool_calls`.
- It takes no parameters.
- Stores the result of calling `ChatResponse` under the name `response`.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Checks that `ChatResponse.from_json(response.to_json()) == response` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_json` of `ChatResponse`.
  - The method `to_json` of `response`.

### `tests/unit/domain/test_tasks.py`

60 non-blank lines; it defines `task`, `mix`, `test_the_lessons_mix_of_thirty_tasks_is_accepted`, `test_a_wrong_mix_duplicate_ids_and_an_impossible_task_that_changes_things_are_rejected`, `test_the_expected_end_state_is_the_seed_with_the_removals_and_additions_applied`, `test_a_task_is_read_from_json`.

`tests/unit/domain/test_tasks.py`, lines 1 to 13:

```python
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
```

- Brings in `datetime` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `InvalidTasks` (The task file breaks a rule of the lesson.), `TaskKind` (The five kinds of task in the set.), `TaskSpec` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.), `end_state` (The calendar's real state as comparable keys.), `expected_end_state` (The seeded calendar with the task's removals and additions applied, as comparable keys.), `validate_tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) from the project module `scheduling_agent.domain.tasks`.

`tests/unit/domain/test_tasks.py`, lines 16 to 21:

```python
def task(i, kind, add=(), remove=()):
    return TaskSpec(f"t{i}", kind, "text", (), tuple(add), tuple(remove))


def mix():
    out: list[TaskSpec] = []
```

- Defines the function `task`.
- Its parameters:
    - `i`.
    - `kind`.
    - `add`; if the caller leaves it out it is a tuple of 0 item(s).
    - `remove`; if the caller leaves it out it is a tuple of 0 item(s).
- Ends the function and gives back the result of calling `TaskSpec` to the caller.
  - `TaskSpec` from the project's `scheduling_agent.domain.tasks` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
- Defines the function `mix`.
- It takes no parameters.
- Declares `out` as a list of the project type `TaskSpec` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/domain/test_tasks.py`, lines 22 to 34:

```python
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
```

- Loop: the indented lines below run once for each item of `((TaskKind.BOOK, 12), (TaskKind.RESCHEDULE, 6), (TaskKind...`; `(kind, count)` names the current item.
- Updates `out` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `task`, a function of this file.
  - `+` is add.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the value named `out` to the caller.
- Defines the function `test_the_lessons_mix_of_thirty_tasks_is_accepted`.
- It takes no parameters.
- Calls `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) with 1 argument(s); the result is not kept.
  - `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.).
  - `mix`, a function of this file.

`tests/unit/domain/test_tasks.py`, lines 37 to 47:

```python
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
```

- Defines the function `test_a_wrong_mix_duplicate_ids_and_an_impossible_task_that_changes_things_are_rejected`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(InvalidTasks, match='expected')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) with 1 argument(s); the result is not kept.
  - `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.).
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `mix`, a function of this file.
- Stores the result of calling `mix` under the name `dup`.
  - `mix`, a function of this file.
- Stores the part of `dup` picked by `0` under the name `dup[1]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- A `with` block: it sets up `pytest.raises(InvalidTasks, match='unique')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) with 1 argument(s); the result is not kept.
  - `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.).
- Stores the result of calling `mix` under the name `bad`.
  - `mix`, a function of this file.
- Stores the result of calling `task` under the name `bad[-1]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `task`, a function of this file.
- A `with` block: it sets up `pytest.raises(InvalidTasks, match='changes nothing')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.) with 1 argument(s); the result is not kept.
  - `validate_tasks` from the project's `scheduling_agent.domain.tasks` (The lesson's mix: 12 bookings, 6 reschedules, 4 find-a-slot, 4 cancellations, 4 that must not complete.).

`tests/unit/domain/test_tasks.py`, lines 50 to 59:

```python
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
```

- Defines the function `test_the_expected_end_state_is_the_seed_with_the_removals_and_additions_applied`.
- It takes no parameters.
- Stores a list of 3 item(s) under the name `seed`.
  - `Event` from the project's `scheduling_agent.domain.calendar` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.).
  - `datetime` from the standard library module `datetime`.
- Stores a tuple of 3 item(s) under the name `added`.
- Stores the result of calling `expected_end_state` under the name `expected`.
  - `expected_end_state` from the project's `scheduling_agent.domain.tasks` (The seeded calendar with the task's removals and additions applied, as comparable keys.).
  - `task`, a function of this file.
- Checks that `expected == {seed[1].key(), added}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `end_state([seed[1]]) == {seed[1].key()}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `end_state` from the project's `scheduling_agent.domain.tasks` (The calendar's real state as comparable keys.).
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/domain/test_tasks.py`, lines 62 to 73:

```python
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
```

- Defines the function `test_a_task_is_read_from_json`.
- It takes no parameters.
- Stores a dictionary with 6 entries under the name `row`.
- Stores the result of calling `TaskSpec.from_json` under the name `parsed`.
  - The method `from_json` of `TaskSpec`.
- Checks that `parsed.facts == (('alice', 'nothing before 10'),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `parsed.add == ((('a', 'b'), '2026-11-02T10:00', 30),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/domain/test_tasks.py`, lines 74 to 74:

```python
    assert parsed.remove == ("ev-9",)
```

- Checks that `parsed.remove == ('ev-9',)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

### `tests/unit/infrastructure/test_agent_db_policy_misc.py`

188 non-blank lines; it defines `db`, `state`, `test_a_run_state_survives_a_round_trip_with_messages_tool_calls_and_a_pending_write`, `test_saving_a_run_twice_updates_it_and_load_returns_the_latest_state`, `test_approvals_are_created_once_per_step_decided_once_and_listed_while_pending`, `test_the_audit_log_keeps_a_replayed_line_once_and_filters_by_run`, `test_facts_are_stored_one_per_person_and_topic_and_replaced_as_a_set`, `messages`, `decide`, `test_the_policy_searches_first_then_proposes_the_first_slot_then_reports`, `test_the_policy_applies_remembered_preferences_to_its_search`, `test_the_policy_gives_up_politely_on_an_error_or_an_empty_search_and_a_persistent_one_keeps_searching`, ....

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 1 to 14:

```python
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
```

- Makes the module `json` (standard library) available.
- Makes the module `os` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `subprocess` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `date`, `datetime`, `timedelta` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `AuditLine` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).) from the project module `scheduling_agent.domain.approvals`.
- Brings in `ApprovalError` (An approval is missing, not approved, or was granted for a different proposal.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `ToolCall` (A tool call the model asked for.) from the project module `scheduling_agent.domain.llm`.
- Brings in `parse_statement` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.) from the project module `scheduling_agent.domain.memory`.
- Brings in `Action` (The three writes.), `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 15 to 28:

```python
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
```

- Brings in `PendingWrite` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.), `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.), `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Brings in `failpoints`, `state_codec` from the project module `scheduling_agent.infrastructure`.
- Brings in `AgentDb` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.) from the project module `scheduling_agent.infrastructure.agent_db`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `scheduling_agent.infrastructure.model_factory`.
- Brings in `ScriptedPolicyModel` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.) from the project module `scheduling_agent.infrastructure.scripted_policy`.
- Brings in `AgentSettings` (Where things live and how a run is capped. See env.example for each variable.) from the project module `scheduling_agent.infrastructure.settings`.
- Brings in `apply_sql` (Run SQL script files in the order given (the numbered files under sql/).), `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Brings in `REPO`, `FixedClock` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.) from the project module `tests.conftest`.
- Defines the function `db`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Stores the result of calling `connect` under the name `connection`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 29 to 33:

```python
    apply_sql(connection, REPO / "sql/agent/001_schema.sql")
    return AgentDb(connection, new_id=iter(f"{i:04d}" for i in range(1, 99)).__next__)


def state(**changes):
```

- Calls `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).) with 2 argument(s); the result is not kept.
  - `apply_sql` from the project's `scheduling_agent.infrastructure.sqlite` (Run SQL script files in the order given (the numbered files under sql/).).
  - `/` is divide.
- Ends the function and gives back the result of calling `AgentDb` to the caller.
  - `AgentDb` from the project's `scheduling_agent.infrastructure.agent_db` (Implements the checkpoint, approval, audit and memory ports on one SQLite connection.).
  - `iter` makes an iterator over a collection.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `range` makes the numbers from 0 up to (not including) the given one.
- Defines the function `state`.
- Its parameters:
    - `**changes` collects any extra named arguments into a dictionary.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 34 to 47:

```python
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
```

- Stores the result of calling `RunState` under the name `base`.
  - `RunState` from the project's `scheduling_agent.domain.run` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.).
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Ends the function and gives back the result of calling `base.with_` to the caller.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
  - `**name` inside a call passes every entry of a dictionary as a named argument.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 50 to 61:

```python
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
```

- Defines the function `test_a_run_state_survives_a_round_trip_with_messages_tool_calls_and_a_pending_write`.
- It takes no parameters.
- Stores the result of calling `PendingWrite` under the name `pending`.
  - `PendingWrite` from the project's `scheduling_agent.domain.run` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.).
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `state` under the name `original`.
  - `state`, a function of this file.
  - `datetime` from the standard library module `datetime`.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 62 to 75:

```python
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
```

- Checks that `state_codec.decode(state_codec.encode(original)) == original` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.decode(...)` turns bytes into text.
  - `.encode(...)` turns text into bytes.
- Checks that `state_codec.decode(state_codec.encode(state())).pending is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `.decode(...)` turns bytes into text.
  - `.encode(...)` turns text into bytes.
  - `state`, a function of this file.
- Defines the function `test_saving_a_run_twice_updates_it_and_load_returns_the_latest_state`.
- Its parameters:
    - `db`.
- Stores the result of calling `FixedClock().now` under the name `now`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Calls the method `save` of `db` with 2 argument(s); the result is not kept.
  - The method `save` of `db`.
  - `state`, a function of this file.
- Calls the method `save` of `db` with 2 argument(s); the result is not kept.
  - The method `save` of `db`.
  - `state`, a function of this file.
  - `+` is add.
  - `timedelta` from the standard library module `datetime`.
- Stores the result of calling `db.load` under the name `loaded`.
  - The method `load` of `db`.
- Checks that `loaded is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Checks that `(loaded.steps, loaded.status) == (3, RunStatus.AWAITING_APPROVAL)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `db.load('nope') is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `load` of `db`.
- Checks that `db.unfinished() == ['run-1']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `unfinished` of `db`.
- Calls the method `save` of `db` with 2 argument(s); the result is not kept.
  - The method `save` of `db`.
  - `state`, a function of this file.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 76 to 89:

```python
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
```

- Checks that `db.unfinished() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `unfinished` of `db`.
- Defines the function `test_approvals_are_created_once_per_step_decided_once_and_listed_while_pending`.
- Its parameters:
    - `db`.
- Stores the result of calling `FixedClock().now` under the name `now`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `Proposal` under the name `proposal`.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `db.request` under the name `first`.
  - The method `request` of `db`.
- Checks that `db.request('run-1', 4, proposal, now).id == first.id` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `request` of `db`.
- Checks that `[a.id for a in db.pending()] == [first.id]` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `pending` of `db`.
- Stores the result of calling `db.decide` under the name `decided`.
  - The method `decide` of `db`.
- Checks that `(decided.status, decided.decided_by) == (ApprovalStatus.APPROVED, 'me')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `db.pending() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `pending` of `db`.
- Checks that `db.get(first.id) == decided` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Checks that `db.get('ap-none') is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 90 to 101:

```python
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
```

- A `with` block: it sets up `pytest.raises(ApprovalError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `decide` of `db` with 4 argument(s); the result is not kept.
  - The method `decide` of `db`.
- Defines the function `test_the_audit_log_keeps_a_replayed_line_once_and_filters_by_run`.
- Its parameters:
    - `db`.
- Stores the result of calling `FixedClock().now` under the name `at`.
  - The method `now` of `FixedClock()`.
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Stores the result of calling `AuditLine` under the name `line`.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
- Checks that `len(db.lines()) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `lines` of `db`.
- Checks that `[entry.run_id for entry in db.lines('run-2')] == ['run-2']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `lines` of `db`.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 104 to 113:

```python
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
```

- Defines the function `test_facts_are_stored_one_per_person_and_topic_and_replaced_as_a_set`.
- Its parameters:
    - `db`.
- Stores the result of calling `date` under the name `today`.
  - `date` from the standard library module `datetime`.
- Stores a list of 2 item(s) under the name `facts`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Calls `.replace(...)` replaces every occurrence of one piece of text with another with 1 argument(s); the result is not kept.
  - `.replace(...)` replaces every occurrence of one piece of text with another.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `sorted(((f.person, f.value) for f in db.facts())) == [('alice', '10:00'), ('c...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `db`.
- Calls `.replace(...)` replaces every occurrence of one piece of text with another with 1 argument(s); the result is not kept.
  - `.replace(...)` replaces every occurrence of one piece of text with another.
- Checks that `db.facts() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `facts` of `db`.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 116 to 126:

```python
def messages(task, *results):
    out = [ChatMessage.user(task)]
    for index, result in enumerate(results, start=1):
        out.append(ChatMessage(Role.ASSISTANT, "", (ToolCall(f"c{index}", "x", {}),)))
        out.append(ChatMessage(Role.TOOL, json.dumps(result), tool_call_id=f"c{index}"))
    return tuple(out)


def decide(task, *results):
    response = ScriptedPolicyModel().complete(ChatRequest(messages(task, *results)))
    return response.tool_calls[0] if response.tool_calls else response.text
```

- Defines the function `messages`.
- Its parameters:
    - `task`.
    - `*results` collects any extra positional arguments into a tuple.
- Stores a list of 1 item(s) under the name `out`.
  - The method `user` of `ChatMessage`.
- Loop: the indented lines below run once for each item of `enumerate(results, start=1)`; `(index, result)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `json.dumps` turns Python data into JSON text.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `tuple` to the caller.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
- Defines the function `decide`.
- Its parameters:
    - `task`.
    - `*results` collects any extra positional arguments into a tuple.
- Stores the result of calling `ScriptedPolicyModel().complete` under the name `response`.
  - The method `complete` of `ScriptedPolicyModel()`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `ScriptedPolicyModel` from the project's `scheduling_agent.infrastructure.scripted_policy` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.).
  - `messages`, a function of this file.
  - `*name` inside a call passes every item of a collection as a separate argument.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 129 to 138:

```python
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
```

- Defines the function `test_the_policy_searches_first_then_proposes_the_first_slot_then_reports`.
- It takes no parameters.
- Stores the text `Book a 30-minute meeting with alice and bob on ...` under the name `task`.
- Stores the result of calling `decide` under the name `search`.
  - `decide`, a function of this file.
- Checks that `(search.name, search.arguments['not_before'], search.arguments['people']) == ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `decide` under the name `book`.
  - `decide`, a function of this file.
- Checks that `(book.name, book.arguments['start']) == ('book_meeting', '2026-11-03T13:30')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 139 to 152:

```python
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
```

- Checks that `decide(task, {'slots': ['2026-11-03T13:30']}, {'status': 'booked', 'event_id'...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Defines the function `test_the_policy_applies_remembered_preferences_to_its_search`.
- It takes no parameters.
- Stores the text `Book a 30-minute meeting with alice on 2026-11-...` under the name `task`.
- Checks that `decide(task).arguments['not_before'] == '10:00'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `decide`, a function of this file.
- Defines the function `test_the_policy_gives_up_politely_on_an_error_or_an_empty_search_and_a_persistent_one_keeps_searching`.
- It takes no parameters.
- Stores the text `Book a 30-minute meeting with zed on 2026-11-03.` under the name `task`.
- Checks that `'changed nothing' in decide(task, {'error': 'UnknownPerson: zed'})` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 153 to 165:

```python
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
```

- Checks that `'no free slot' in decide(task, {'slots': []})` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.
- Stores the text `Book a 30-minute meeting with bob on 2026-11-06...` under the name `persistent`.
- Stores the result of calling `decide` under the name `again`.
  - `decide`, a function of this file.
- Checks that `again.name == 'find_free_slots'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `again.arguments['first_day'] == '2026-11-13'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'did not happen' in decide(task, {'slots': ['2026-11-03T10:00']}, {'status': ...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.
- Defines the function `test_the_policy_handles_move_and_cancel_and_says_when_it_does_not_understand`.
- It takes no parameters.
- Stores the text `Move event ev-0005 to the earliest free slot be...` under the name `move`.
- Checks that `decide(move).name == 'get_event'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Stores a dictionary with 4 entries under the name `event`.
- Stores the result of calling `decide` under the name `search`.
  - `decide`, a function of this file.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 166 to 179:

```python
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
```

- Checks that `(search.name, search.arguments['minutes'], search.arguments['not_before']) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `decide(move, event, {'slots': ['2026-11-09T13:00']}).name == 'move_meeting'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Checks that `decide(move, event, {'slots': []}) == 'There is no free slot that fits, so I ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Checks that `'Moved ev-0005' in decide(move, event, {'slots': ['x']}, {'status': 'moved', ...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.
- Checks that `'could not find' in decide(move, {'error': 'UnknownEvent'})` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.
- Stores the text `Cancel event ev-0007.` under the name `cancel`.
- Checks that `decide(cancel).name == 'get_event'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Checks that `decide(cancel, event).name == 'cancel_meeting'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Checks that `decide(cancel, event, {'status': 'cancelled'}) == 'Cancelled ev-0007.'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `decide`, a function of this file.
- Checks that `'could not find' in decide(cancel, {'error': 'UnknownEvent'})` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 180 to 193:

```python
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
```

- Checks that `'did not understand' in decide('Sing me a song')` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `decide`, a function of this file.
- Defines the function `test_the_policy_reports_what_it_is_and_counts_tokens_from_the_conversation`.
- It takes no parameters.
- Stores the result of calling `ScriptedPolicyModel` under the name `policy`.
  - `ScriptedPolicyModel` from the project's `scheduling_agent.infrastructure.scripted_policy` (Reads the task and the tool results in the conversation and decides the next tool call or the final answer.).
- Stores the result of calling `policy.complete` under the name `response`.
  - The method `complete` of `policy`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `messages`, a function of this file.
- Checks that `(policy.name, policy.supports_sampling) == ('scripted-policy', True)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.usage.input_tokens > 30` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `response.model == 'scripted-policy'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_the_scripted_provider_is_the_default_and_other_providers_are_still_available`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Checks that `settings.provider == 'scripted'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 194 to 207:

```python
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
```

- Checks that `isinstance(build_chat_model(settings, FixedClock(), {}), ScriptedPolicyModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Checks that `ModelSettings.from_env({'MODEL_PROVIDER': 'openai-compatible'}).model == 'qwe...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_env` of `ModelSettings`.
- Defines the function `test_failpoints_are_off_unless_named_and_a_named_one_kills_with_sigkill`.
- It takes no parameters.
- Checks that `isinstance(failpoints.from_env({}), failpoints.NoFailPoints)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - The method `from_env` of `failpoints`.
- Calls the method `hit` of `failpoints.NoFailPoints()` with 1 argument(s); the result is not kept.
  - The method `hit` of `failpoints.NoFailPoints()`.
  - The method `NoFailPoints` of `failpoints`.
- Stores the result of calling `failpoints.from_env` under the name `named`.
  - The method `from_env` of `failpoints`.
- Checks that `isinstance(named, failpoints.SigkillAt)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Calls the method `hit` of `named` with 1 argument(s); the result is not kept.
  - The method `hit` of `named`.
- Stores the text `from scheduling_agent.infrastructure.failpoints...` under the name `code`.
- Stores the result of calling `subprocess.run` under the name `done`.
  - `subprocess.run` runs another program and waits for it.
- Checks that `done.returncode == -signal.SIGKILL` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'alive' not in done.stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 210 to 215:

```python
def test_settings_have_defaults_and_validate_each_value():
    settings = AgentSettings.from_env({})
    assert (settings.max_steps, settings.max_tokens, settings.max_seconds) == (12, 4000, 30.0)
    assert settings.people == ("alice", "bob", "carol", "dave", "erin")
    assert not settings.allow_reset
    assert AgentSettings.from_env({"PEOPLE": "Zoe, Yan", "CALENDAR_ALLOW_RESET": "on"}).people == ("zoe", "yan")
```

- Defines the function `test_settings_have_defaults_and_validate_each_value`.
- It takes no parameters.
- Stores the result of calling `AgentSettings.from_env` under the name `settings`.
  - The method `from_env` of `AgentSettings`.
- Checks that `(settings.max_steps, settings.max_tokens, settings.max_seconds) == (12, 4000,...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.people == ('alice', 'bob', 'carol', 'dave', 'erin')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `not settings.allow_reset` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Checks that `AgentSettings.from_env({'PEOPLE': 'Zoe, Yan', 'CALENDAR_ALLOW_RESET': 'on'})....` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_env` of `AgentSettings`.

`tests/unit/infrastructure/test_agent_db_policy_misc.py`, lines 216 to 224:

```python
    for bad, name in (
        ({"MAX_STEPS": "0"}, "MAX_STEPS"),
        ({"PEOPLE": " , "}, "PEOPLE"),
        ({"CALENDAR_ALLOW_RESET": "yes"}, "CALENDAR_ALLOW_RESET"),
        ({"MAX_SECONDS": "-1"}, "MAX_SECONDS"),
        ({"LOG_LEVEL": "loud"}, "LOG_LEVEL"),
    ):
        with pytest.raises(ConfigurationError, match=name):
            AgentSettings.from_env(bad)
```

- Loop: the indented lines below run once for each item of `(({'MAX_STEPS': '0'}, 'MAX_STEPS'), ({'PEOPLE': ' , '}, '...`; `(bad, name)` names the current item.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match=name)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `from_env` of `AgentSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `AgentSettings`.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/unit --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/infrastructure/test_resilience_logging_factory.py::test_info_logs_of_a_failed_call_never_carry_the_prompt_text

154 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/unit -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/unit/application/test_memory_and_task_runner.py::test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten
tests/unit/application/test_memory_and_task_runner.py::test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first
tests/unit/application/test_memory_and_task_runner.py::test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects
tests/unit/application/test_memory_and_task_runner.py::test_the_task_file_has_the_lessons_mix_and_each_expected_state_is_what_the_calendar_search_finds
tests/unit/application/test_memory_and_task_runner.py::test_all_thirty_tasks_reach_their_expected_end_state_with_no_write_lacking_an_approval
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/unit/application/test_memory_and_task_runner.py` test?

   *Answer:* It holds the tests for `memory and task runner`.

2. What does `tests/unit/application/test_tools_and_agent.py` test?

   *Answer:* It holds the tests for `tools and agent`.

3. What does `tests/unit/domain/test_calendar_memory_budget.py` test?

   *Answer:* It holds the tests for `calendar memory budget`.

4. What does `tests/unit/domain/test_llm.py` test?

   *Answer:* It holds the tests for `llm`.

5. What does `tests/unit/domain/test_tasks.py` test?

   *Answer:* It holds the tests for `tasks`.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
