"""Write proposals, approvals and the idempotency key that makes a replayed write harmless."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Action(StrEnum):
    """The three writes."""

    BOOK = "book"
    MOVE = "move"
    CANCEL = "cancel"


class ApprovalStatus(StrEnum):
    """Where an approval is: waiting for a person, approved or rejected."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Proposal:
    """A write the agent wants to make. An approval is for exactly this content, not for a tool name."""

    action: Action
    args: Mapping[str, Any]

    def canonical(self) -> str:
        """Stable JSON: sorted keys, no spaces. The same proposal always gives the same text."""
        return json.dumps({"action": self.action.value, "args": dict(self.args)}, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()


def write_key(run_id: str, step: int, part: str = "") -> str:
    """The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.

    The same step gets the same key before and after a crash. A move is two writes (cancel, then book), so each part
    gets its own suffix.
    """
    material = f"{run_id}:{step}" + (f":{part}" if part else "")
    return hashlib.sha256(material.encode()).hexdigest()
