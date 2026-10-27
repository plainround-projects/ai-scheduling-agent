"""Value objects for approvals, audit lines and the result of a calendar write."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.proposals import ApprovalStatus, Proposal


@dataclass(frozen=True, slots=True)
class Approval:
    """A proposal and what a person decided about it."""

    id: str
    run_id: str
    step: int
    proposal: Proposal
    status: ApprovalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None


@dataclass(frozen=True, slots=True)
class AuditLine:
    """One write attempt: refused (no valid approval) or written (with the approval that allowed it)."""

    at: datetime
    run_id: str
    step: int
    action: str
    outcome: str
    approval_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class BookingResult:
    """What the calendar answered to a write: the event and whether the answer was a replay of an earlier key."""

    event: Event
    replayed: bool
