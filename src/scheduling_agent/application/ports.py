"""The boundaries the use cases depend on. Adapters in `infrastructure` implement them."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time
from typing import Protocol

from scheduling_agent.domain.approvals import Approval, AuditLine, BookingResult
from scheduling_agent.domain.calendar import Event
from scheduling_agent.domain.llm import ChatRequest, ChatResponse
from scheduling_agent.domain.memory import Fact
from scheduling_agent.domain.proposals import Proposal
from scheduling_agent.domain.run import RunState


class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""

    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...

    @property
    def supports_sampling(self) -> bool:
        """False when the provider rejects `temperature` and `top_p` (the request then says so)."""
        ...

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...


class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
        ...


class Clock(Protocol):
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class CalendarPort(Protocol):
    """The calendar service. Writes take an idempotency key; a repeated key returns the first result."""

    def free_slots(
        self,
        people: Sequence[str],
        first_day: date,
        last_day: date,
        minutes: int,
        not_before: time | None = None,
        not_after: time | None = None,
    ) -> list[datetime]: ...

    def get_event(self, event_id: str) -> Event:
        """The event, cancelled or not; raises `UnknownEvent`."""
        ...

    def book(self, people: Sequence[str], start: datetime, minutes: int, idempotency_key: str) -> BookingResult: ...

    def cancel(self, event_id: str, idempotency_key: str) -> BookingResult: ...

    def active_events(self) -> list[Event]:
        """Every event that is not cancelled (used to judge a run by the calendar's real end state)."""
        ...


class ApprovalStore(Protocol):
    """Proposals waiting for a person, and what the person decided."""

    def request(self, run_id: str, step: int, proposal: Proposal, now: datetime) -> Approval:
        """Create the approval for this run and step, or return the one that exists (idempotent)."""
        ...

    def get(self, approval_id: str) -> Approval | None: ...

    def decide(self, approval_id: str, approved: bool, by: str, now: datetime) -> Approval: ...

    def pending(self) -> list[Approval]: ...


class CheckpointStore(Protocol):
    """Saved run state."""

    def save(self, state: RunState, now: datetime) -> None:
        """Write the whole run state in one transaction."""
        ...

    def load(self, run_id: str) -> RunState | None: ...

    def unfinished(self) -> list[str]:
        """Ids of runs that are running or waiting for an approval."""
        ...


class AuditLog(Protocol):
    """Append-only record of every write attempt."""

    def append(self, line: AuditLine) -> None: ...

    def lines(self, run_id: str | None = None) -> list[AuditLine]: ...


class MemoryStore(Protocol):
    """Facts people stated about themselves."""

    def facts(self) -> list[Fact]: ...

    def replace(self, facts: Sequence[Fact]) -> None:
        """Replace the whole set of facts (after compaction)."""
        ...


class FailPoints(Protocol):
    """Named places where a test can kill the process, to prove a crash there is survivable."""

    def hit(self, name: str) -> None: ...
