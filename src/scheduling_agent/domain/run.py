"""A run of the agent: its status, its saved messages and the write it may be waiting on."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from scheduling_agent.domain.llm import ChatMessage
from scheduling_agent.domain.proposals import Proposal


class RunStatus(StrEnum):
    """Where a run is."""

    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PendingWrite:
    """The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch."""

    step: int
    tool_call_id: str
    tool_name: str
    proposal: Proposal
    approval_id: str
    skipped_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RunState:
    """Everything needed to continue a run after a crash: it is saved after every step, in one transaction."""

    run_id: str
    task: str
    session: str
    status: RunStatus
    steps: int
    tokens: int
    messages: tuple[ChatMessage, ...]
    pending: PendingWrite | None = None
    final_text: str = ""
    stop_reason: str = ""
    writes_done: tuple[str, ...] = ()
    created_at: datetime | None = None
    notes: dict[str, Any] = field(default_factory=dict)

    def with_(self, **changes: Any) -> RunState:
        """A copy with some fields changed (the dataclass is frozen)."""
        return replace(self, **changes)
