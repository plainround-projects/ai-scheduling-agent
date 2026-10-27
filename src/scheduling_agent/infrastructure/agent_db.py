"""The agent's own SQLite database: saved runs, approvals, the audit log and memory facts."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Callable, Sequence
from datetime import date, datetime

from scheduling_agent.domain.approvals import Approval, AuditLine
from scheduling_agent.domain.errors import ApprovalError
from scheduling_agent.domain.memory import Fact, FactKind
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
from scheduling_agent.domain.run import RunState
from scheduling_agent.infrastructure import state_codec
from scheduling_agent.infrastructure.sqlite import transaction


def _approval(row: sqlite3.Row) -> Approval:
    proposal = json.loads(row["proposal_json"])
    return Approval(
        row["id"],
        row["run_id"],
        row["step"],
        Proposal(Action(proposal["action"]), proposal["args"]),
        ApprovalStatus(row["status"]),
        datetime.fromisoformat(row["created_at"]),
        datetime.fromisoformat(row["decided_at"]) if row["decided_at"] else None,
        row["decided_by"],
    )


class AgentDb:
    """Implements the checkpoint, approval, audit and memory ports on one SQLite connection."""

    def __init__(
        self, connection: sqlite3.Connection, new_id: Callable[[], str] = lambda: uuid.uuid4().hex[:10]
    ) -> None:
        self._db = connection
        self._new_id = new_id
        self._lock = threading.RLock()

    # --- checkpoints

    def save(self, state: RunState, now: datetime) -> None:
        """The run row and the step row, in one transaction."""
        with self._lock, transaction(self._db):
            created = state.created_at or now
            self._db.execute(
                "INSERT INTO runs (run_id, task, session, status, steps, tokens, state_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (run_id) DO UPDATE SET status = excluded.status, "
                "steps = excluded.steps, tokens = excluded.tokens, state_json = excluded.state_json, "
                "updated_at = excluded.updated_at",
                (
                    state.run_id,
                    state.task,
                    state.session,
                    state.status.value,
                    state.steps,
                    state.tokens,
                    state_codec.encode(state.with_(created_at=created)),
                    created.isoformat(),
                    now.isoformat(),
                ),
            )
            self._db.execute(
                "INSERT INTO run_steps (run_id, step, status, pending_approval_id, saved_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT (run_id, step) DO UPDATE SET status = excluded.status, "
                "pending_approval_id = excluded.pending_approval_id, saved_at = excluded.saved_at",
                (
                    state.run_id,
                    state.steps,
                    state.status.value,
                    state.pending.approval_id if state.pending else None,
                    now.isoformat(),
                ),
            )

    def load(self, run_id: str) -> RunState | None:
        with self._lock:
            row = self._db.execute("SELECT state_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return state_codec.decode(row["state_json"]) if row else None

    def unfinished(self) -> list[str]:
        with self._lock:
            rows = self._db.execute(
                "SELECT run_id FROM runs WHERE status IN ('running', 'awaiting_approval') ORDER BY created_at, run_id"
            )
            return [r[0] for r in rows]

    # --- approvals

    def request(self, run_id: str, step: int, proposal: Proposal, now: datetime) -> Approval:
        with self._lock, transaction(self._db):
            row = self._db.execute("SELECT * FROM approvals WHERE run_id = ? AND step = ?", (run_id, step)).fetchone()
            if row is not None:
                return _approval(row)
            approval_id = f"ap-{self._new_id()}"
            self._db.execute(
                "INSERT INTO approvals (id, run_id, step, proposal_json, status, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', ?)",
                (approval_id, run_id, step, proposal.canonical(), now.isoformat()),
            )
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            return _approval(row)

    def get(self, approval_id: str) -> Approval | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        return _approval(row) if row else None

    def decide(self, approval_id: str, approved: bool, by: str, now: datetime) -> Approval:
        with self._lock, transaction(self._db):
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            if row is None:
                raise ApprovalError(f"unknown approval {approval_id}")
            if row["status"] != "pending":
                raise ApprovalError(f"approval {approval_id} was already {row['status']}")
            self._db.execute(
                "UPDATE approvals SET status = ?, decided_at = ?, decided_by = ? WHERE id = ?",
                ("approved" if approved else "rejected", now.isoformat(), by, approval_id),
            )
            return _approval(self._db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone())

    def pending(self) -> list[Approval]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM approvals WHERE status = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return [_approval(r) for r in rows]

    # --- audit

    def append(self, line: AuditLine) -> None:
        with self._lock, transaction(self._db):
            self._db.execute(
                "INSERT OR IGNORE INTO audit_log (at, run_id, step, action, outcome, approval_id, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (line.at.isoformat(), line.run_id, line.step, line.action, line.outcome, line.approval_id, line.detail),
            )

    def lines(self, run_id: str | None = None) -> list[AuditLine]:
        with self._lock:
            if run_id is None:
                rows = self._db.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
            else:
                rows = self._db.execute("SELECT * FROM audit_log WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
        return [
            AuditLine(
                datetime.fromisoformat(r["at"]),
                r["run_id"],
                r["step"],
                r["action"],
                r["outcome"],
                r["approval_id"],
                r["detail"],
            )
            for r in rows
        ]

    # --- memory

    def facts(self) -> list[Fact]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM memory_facts ORDER BY person, topic").fetchall()
        return [
            Fact(
                r["person"],
                FactKind(r["kind"]),
                r["value"],
                r["text"],
                r["session"],
                date.fromisoformat(r["stated_on"]),
                date.fromisoformat(r["expires_on"]) if r["expires_on"] else None,
            )
            for r in rows
        ]

    def replace(self, facts: Sequence[Fact]) -> None:
        with self._lock, transaction(self._db):
            self._db.execute("DELETE FROM memory_facts")
            self._db.executemany(
                "INSERT INTO memory_facts (person, topic, kind, value, text, session, stated_on, expires_on) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        f.person,
                        ":".join(f.topic[1:]).rstrip(":"),
                        f.kind.value,
                        f.value,
                        f.text,
                        f.session,
                        f.stated_on.isoformat(),
                        f.expires_on.isoformat() if f.expires_on else None,
                    )
                    for f in facts
                ],
            )
