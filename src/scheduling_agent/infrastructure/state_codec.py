"""Run state to JSON and back, for the checkpoint table."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from scheduling_agent.domain.llm import ChatMessage, Role, ToolCall
from scheduling_agent.domain.proposals import Action, Proposal
from scheduling_agent.domain.run import PendingWrite, RunState, RunStatus


def encode(state: RunState) -> str:
    """The whole run state as one JSON document."""
    pending = state.pending
    return json.dumps(
        {
            "run_id": state.run_id,
            "task": state.task,
            "session": state.session,
            "status": state.status.value,
            "steps": state.steps,
            "tokens": state.tokens,
            "final_text": state.final_text,
            "stop_reason": state.stop_reason,
            "writes_done": list(state.writes_done),
            "created_at": state.created_at.isoformat() if state.created_at else None,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_call_id": m.tool_call_id,
                    "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in m.tool_calls],
                }
                for m in state.messages
            ],
            "pending": None
            if pending is None
            else {
                "step": pending.step,
                "tool_call_id": pending.tool_call_id,
                "tool_name": pending.tool_name,
                "proposal": {"action": pending.proposal.action.value, "args": dict(pending.proposal.args)},
                "approval_id": pending.approval_id,
                "skipped_ids": list(pending.skipped_ids),
            },
        },
        sort_keys=True,
    )


def decode(text: str) -> RunState:
    """The inverse of `encode`."""
    data: dict[str, Any] = json.loads(text)
    pending = data["pending"]
    return RunState(
        run_id=data["run_id"],
        task=data["task"],
        session=data["session"],
        status=RunStatus(data["status"]),
        steps=data["steps"],
        tokens=data["tokens"],
        messages=tuple(
            ChatMessage(
                Role(m["role"]),
                m["content"],
                tuple(ToolCall(c["id"], c["name"], c["arguments"]) for c in m["tool_calls"]),
                m["tool_call_id"],
            )
            for m in data["messages"]
        ),
        pending=None
        if pending is None
        else PendingWrite(
            pending["step"],
            pending["tool_call_id"],
            pending["tool_name"],
            Proposal(Action(pending["proposal"]["action"]), pending["proposal"]["args"]),
            pending["approval_id"],
            tuple(pending["skipped_ids"]),
        ),
        final_text=data["final_text"],
        stop_reason=data["stop_reason"],
        writes_done=tuple(data["writes_done"]),
        created_at=datetime.fromisoformat(data["created_at"]) if data["created_at"] else None,
    )
