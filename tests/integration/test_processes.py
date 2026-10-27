"""The calendar service and the agent as real processes: SIGKILL at five points, SIGTERM, parallel writes."""

import signal
import sqlite3
import threading

import httpx
import pytest

from tests.conftest import REPO
from tests.integration.conftest import Service, agent, events

pytestmark = pytest.mark.integration

# five booking tasks, one per crash point plus one clean run, all on different days so they never collide
CRASH_CASES = [
    ("run_created", "Book a 30-minute meeting with alice and bob on 2026-11-02."),
    ("after_step", "Book a 30-minute meeting with carol and dave on 2026-11-03."),
    ("after_proposal", "Book a 30-minute meeting with erin and alice on 2026-11-04."),
    ("after_write_before_checkpoint", "Book a 30-minute meeting with bob and carol on 2026-11-05."),
    (None, "Book a 30-minute meeting with dave and erin on 2026-11-06."),
]


def reset(service: Service) -> None:
    assert httpx.post(f"{service.url}/admin/reset", timeout=10).status_code == 200


def double_bookings(service: Service) -> int:
    """The overlap query from sql/calendar/003_queries.sql: two active events sharing a person and time."""
    sql = (REPO / "sql/calendar/003_queries.sql").read_text().split(";")[1] + ";"
    with sqlite3.connect(service.db) as db:
        return len(db.execute(sql).fetchall())


def test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice(service, tmp_path):
    reset(service)
    baseline = len(events(service))
    for index, (point, task) in enumerate(CRASH_CASES, start=1):
        run_id = f"crash-{index}"
        killed = agent(service, tmp_path, "run", task, "--run-id", run_id, "--auto-approve", failpoint=point)
        if point is None:
            assert killed.returncode == 0, killed.stderr
        else:
            assert killed.returncode == -signal.SIGKILL, (point, killed.returncode, killed.stderr)
            resumed = agent(service, tmp_path, "resume", run_id, "--auto-approve")
            assert resumed.returncode == 0, resumed.stderr
            assert "done after" in resumed.stdout
            assert "Booked event" in resumed.stdout
        written = agent(service, tmp_path, "audit", "--run", run_id).stdout.count(" written ")
        assert written == 1, (point, written)
    after = events(service)
    assert len(after) == baseline + 5
    keys = [(tuple(e["people"]), e["start"], e["minutes"]) for e in after]  # type: ignore[arg-type,var-annotated]
    assert len(keys) == len(set(keys))
    assert double_bookings(service) == 0


def test_a_kill_between_the_cancel_and_the_book_of_a_move_is_finished_by_the_resume(service, tmp_path):
    reset(service)
    before = events(service)
    victim = before[3]
    task = f"Move event {victim['id']} to the earliest free slot between 2026-11-09 and 2026-11-10."
    killed = agent(
        service, tmp_path, "run", task, "--run-id", "move-1", "--auto-approve", failpoint="between_move_cancel_and_book"
    )
    assert killed.returncode == -signal.SIGKILL
    assert victim["id"] not in {e["id"] for e in events(service)}
    resumed = agent(service, tmp_path, "resume", "move-1", "--auto-approve")
    assert resumed.returncode == 0, resumed.stderr
    after = events(service)
    assert len(after) == len(before)
    assert double_bookings(service) == 0


def test_the_unfinished_run_a_crash_left_is_listed_and_a_pending_proposal_waits_for_a_person(service, tmp_path):
    reset(service)
    task = "Book a 30-minute meeting with alice and bob on 2026-11-09."
    first = agent(service, tmp_path, "run", task, "--run-id", "wait-1")
    assert first.returncode == 5
    assert "waiting for approval" in first.stdout
    assert "wait-1" in agent(service, tmp_path, "unfinished").stdout
    pending = agent(service, tmp_path, "pending").stdout
    approval_id = pending.split()[0]
    assert approval_id.startswith("ap-")
    before = len(events(service))
    decided = agent(service, tmp_path, "approve", approval_id, "--resume")
    assert decided.returncode == 0, decided.stderr
    assert len(events(service)) == before + 1


def test_a_rejected_proposal_over_the_command_line_writes_nothing(service, tmp_path):
    reset(service)
    before = len(events(service))
    task = "Book a 30-minute meeting with alice and bob on 2026-11-10."
    agent(service, tmp_path, "run", task, "--run-id", "no-1")
    approval_id = agent(service, tmp_path, "pending").stdout.split()[0]
    done = agent(service, tmp_path, "reject", approval_id, "--resume")
    assert done.returncode == 0
    assert "rejected" in done.stdout
    assert len(events(service)) == before
    assert " written " not in agent(service, tmp_path, "audit", "--run", "no-1").stdout


def test_parallel_requests_with_one_key_over_http_create_one_event_and_other_keys_conflict(service):
    reset(service)
    before = len(events(service))
    body = {"people": ["alice", "bob"], "start": "2026-11-02T16:00", "minutes": 30}
    statuses: list[int] = []

    def post(key: str) -> None:
        statuses.append(
            httpx.post(f"{service.url}/events", json=body, headers={"Idempotency-Key": key}, timeout=10).status_code
        )

    threads = [threading.Thread(target=post, args=("parallel-key-1",)) for _ in range(8)]
    threads += [threading.Thread(target=post, args=("parallel-key-2",)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert statuses.count(409) == 2
    assert sorted(set(statuses) - {409}) == [200, 201]
    assert len(events(service)) == before + 1
    assert double_bookings(service) == 0


def test_sigterm_lets_the_service_finish_and_exit_cleanly(service):
    assert httpx.get(f"{service.url}/health", timeout=5).status_code == 200
    service.process.send_signal(signal.SIGTERM)
    # uvicorn finishes in-flight requests, closes, then re-raises the signal so the exit status says why it stopped
    assert service.process.wait(timeout=30) in (0, -signal.SIGTERM)
