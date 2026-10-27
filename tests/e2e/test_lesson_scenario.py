"""The lesson's step 6 through the real HTTP service: 30 tasks, three runs each, judged by the calendar's end state."""

import httpx
import pytest

from scheduling_agent.application.task_runner import ExpectedWritesApprover, TaskRunner
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.files import load_tasks
from tests.conftest import REPO, build_kit
from tests.integration.conftest import Service
from tests.integration.test_processes import double_bookings

pytestmark = pytest.mark.e2e


def test_the_thirty_tasks_three_times_each_through_the_real_http_service_all_reach_their_end_state(service: Service):
    tasks = load_tasks(REPO / "data" / "tasks.jsonl")
    calendar = HttpCalendar(httpx.Client(timeout=10), service.url)
    runner = TaskRunner(calendar, lambda: build_kit(calendar=calendar), ExpectedWritesApprover(), SystemClock())
    results = runner.run_all(tasks, repeats=3)
    assert len(results) == 90
    assert [r.task_id for r in results if not r.passed] == []
    assert sum(r.writes_without_approval for r in results) == 0
    assert double_bookings(service) == 0
