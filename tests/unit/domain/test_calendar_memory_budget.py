from datetime import date, datetime, time, timedelta

import pytest

from scheduling_agent.domain.budget import Budget
from scheduling_agent.domain.calendar import Event, free_slots, overlaps, validate_slot
from scheduling_agent.domain.errors import BudgetExceeded, InvalidSlot
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


def at(hour, minute=0, day=MON):
    return datetime.combine(day, time(hour, minute))


def test_a_valid_slot_passes_and_each_rule_names_what_it_broke():
    validate_slot(at(9), 30)
    validate_slot(at(16, 30), 30)
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
    assert at(9) not in slots
    assert at(10, 30) not in slots
    assert free_slots({}, ["alice"], date(2026, 11, 7), date(2026, 11, 8), 30) == []
    narrowed = free_slots({}, ["alice"], MON, MON, 60, not_before=time(13), not_after=time(15))
    assert narrowed == [at(13), at(13, 30), at(14)]


def test_free_slots_can_skip_whole_weekdays():
    slots = free_slots({}, ["alice"], MON, MON + timedelta(days=1), 30, avoid_weekdays={0})
    assert {s.date() for s in slots} == {MON + timedelta(days=1)}


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
    a = Proposal(Action.BOOK, {"people": ["a"], "start": "2026-11-02T10:00", "minutes": 30})
    b = Proposal(Action.BOOK, {"minutes": 30, "start": "2026-11-02T10:00", "people": ["a"]})
    c = Proposal(Action.BOOK, {"people": ["a"], "start": "2026-11-02T10:30", "minutes": 30})
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()
