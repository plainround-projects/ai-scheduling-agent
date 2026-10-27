"""The agent loop: model step, tool calls, a checkpoint after every step, writes only after a person approves."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import ApprovalStore, AuditLog, ChatModel, CheckpointStore, Clock, FailPoints
from scheduling_agent.application.tools import ToolBox, dump, tool_specs
from scheduling_agent.domain.budget import Budget
from scheduling_agent.domain.errors import BudgetExceeded, DomainError
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, Role, ToolCall
from scheduling_agent.domain.memory import Fact
from scheduling_agent.domain.prompts import Prompt
from scheduling_agent.domain.proposals import ApprovalStatus, Proposal
from scheduling_agent.domain.run import PendingWrite, RunState, RunStatus

_log = logging.getLogger(__name__)


class UnknownRun(DomainError):
    """No saved run with that id."""


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """The caps of a run and the size of one model answer."""

    max_steps: int = 12
    max_tokens: int = 4000
    max_seconds: float = 30.0
    max_output_tokens: int = 400


def memory_block(facts: list[Fact]) -> str:
    """The recalled facts as lines of the first message, with who said them and when."""
    if not facts:
        return ""
    lines = [f"- {f.person}: {f.text} (said {f.stated_on}, session {f.session})" for f in facts]
    return "\n\nWhat people told you earlier (use it):\n" + "\n".join(lines)


class SchedulingAgent:
    """Books, moves and cancels meetings through tools, inside budgets, saving its state after every step."""

    def __init__(
        self,
        model: ChatModel,
        tools: ToolBox,
        checkpoints: CheckpointStore,
        approvals: ApprovalStore,
        audit: AuditLog,
        memory: MemoryService,
        clock: Clock,
        prompt: Prompt,
        config: AgentConfig,
        failpoints: FailPoints,
        new_run_id: Callable[[], str] = lambda: uuid.uuid4().hex[:12],
    ) -> None:
        self._model = model
        self._tools = tools
        self._checkpoints = checkpoints
        self._approvals = approvals
        self._audit = audit
        self._memory = memory
        self._clock = clock
        self._prompt = prompt
        self._config = config
        self._failpoints = failpoints
        self._new_run_id = new_run_id

    def start(self, task: str, session: str, run_id: str | None = None) -> RunState:
        """Begin a run: recall what people said, save the new run, then drive it until it stops or waits."""
        facts = self._memory.recall(task)
        first = ChatMessage.user(task + memory_block(facts))
        state = RunState(
            run_id or self._new_run_id(), task, session, RunStatus.RUNNING, 0, 0, (first,), created_at=self._clock.now()
        )
        self._checkpoints.save(state, self._clock.now())
        _log.info("run started", extra={"fields": {"run_id": state.run_id, "recalled_facts": len(facts)}})
        self._failpoints.hit("run_created")
        return self._drive(state)

    def resume(self, run_id: str) -> RunState:
        """Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys."""
        state = self._checkpoints.load(run_id)
        if state is None:
            raise UnknownRun(f"no run {run_id}")
        if state.status in (RunStatus.DONE, RunStatus.STOPPED, RunStatus.FAILED):
            return state
        _log.info("run resumed", extra={"fields": {"run_id": run_id, "step": state.steps}})
        return self._drive(state.with_(status=RunStatus.RUNNING))

    def _save(self, state: RunState) -> None:
        self._checkpoints.save(state, self._clock.now())

    def _drive(self, state: RunState) -> RunState:
        cfg = self._config
        budget = Budget(
            cfg.max_steps, cfg.max_tokens, cfg.max_seconds, self._clock.monotonic(), state.steps, state.tokens
        )
        while True:
            if state.pending is not None:
                state = self._settle(state)
                if state.status is RunStatus.AWAITING_APPROVAL:
                    return state
                continue
            try:
                budget.check(self._clock.monotonic())
            except BudgetExceeded as stop:
                return self._stop(state, stop)
            response = self._model.complete(
                ChatRequest(
                    messages=state.messages,
                    system=self._prompt.text,
                    max_output_tokens=cfg.max_output_tokens,
                    temperature=0.0 if self._model.supports_sampling else None,
                    tools=tool_specs(),
                    tag=f"{state.run_id}|step{state.steps + 1}",
                )
            )
            budget.spend(response.usage.input_tokens + response.usage.output_tokens)
            assistant = ChatMessage(Role.ASSISTANT, response.text, response.tool_calls)
            state = state.with_(steps=budget.steps, tokens=budget.tokens, messages=(*state.messages, assistant))
            if not response.tool_calls:
                state = state.with_(status=RunStatus.DONE, final_text=response.text.strip())
                self._save(state)
                self._failpoints.hit("run_done")
                return state
            state = self._run_calls(state, response.tool_calls)
            if state.status is RunStatus.AWAITING_APPROVAL:
                return state

    def _run_calls(self, state: RunState, calls: tuple[ToolCall, ...]) -> RunState:
        """Run the calls of one model answer in order. The first write stops the turn: it becomes a pending proposal."""
        results: list[ChatMessage] = []
        for index, call in enumerate(calls):
            if not self._tools.is_write(call.name):
                results.append(
                    ChatMessage(Role.TOOL, dump(self._tools.read(call.name, call.arguments)), tool_call_id=call.id)
                )
                continue
            proposal = self._tools.propose(call.name, call.arguments)
            if not isinstance(proposal, Proposal):
                results.append(ChatMessage(Role.TOOL, dump(proposal), tool_call_id=call.id))
                continue
            outcome = self._tools.request_approval(state.run_id, state.steps, proposal)
            pending = PendingWrite(
                state.steps,
                call.id,
                call.name,
                proposal,
                outcome["approval_id"],
                tuple(c.id for c in calls[index + 1 :]),
            )
            state = state.with_(
                status=RunStatus.AWAITING_APPROVAL, messages=(*state.messages, *results), pending=pending
            )
            self._save(state)
            self._failpoints.hit("after_proposal")
            return state
        state = state.with_(messages=(*state.messages, *results))
        self._save(state)
        self._failpoints.hit("after_step")
        return state

    def _settle(self, state: RunState) -> RunState:
        """Resolve the pending write: wait, reject, or (approved) execute it with its idempotency key."""
        pending = state.pending
        assert pending is not None
        approval = self._approvals.get(pending.approval_id)
        if approval is None or approval.status is ApprovalStatus.PENDING:
            return state.with_(status=RunStatus.AWAITING_APPROVAL)
        if approval.status is ApprovalStatus.REJECTED:
            result = {"status": "rejected", "detail": "a person rejected this proposal; do not repeat it"}
        else:
            self._failpoints.hit("before_write")
            result = self._tools.execute_write(state.run_id, pending.step, pending.proposal, pending.approval_id)
            self._failpoints.hit("after_write_before_checkpoint")
        tool_messages = [ChatMessage(Role.TOOL, dump(result), tool_call_id=pending.tool_call_id)]
        tool_messages += [
            ChatMessage(
                Role.TOOL,
                dump({"status": "skipped", "detail": "another write was waiting for approval"}),
                tool_call_id=i,
            )
            for i in pending.skipped_ids
        ]
        done = (
            (*state.writes_done, pending.proposal.digest())
            if result.get("status") in ("booked", "cancelled", "moved")
            else state.writes_done
        )
        state = state.with_(
            status=RunStatus.RUNNING, messages=(*state.messages, *tool_messages), pending=None, writes_done=done
        )
        self._save(state)
        self._failpoints.hit("after_write_checkpoint")
        return state

    def _stop(self, state: RunState, stop: BudgetExceeded) -> RunState:
        """A cap fired: say which one, what was done and what was not, and save the run as stopped."""
        done = f"{len(state.writes_done)} write(s) made" if state.writes_done else "no write was made"
        text = f"Stopped: {stop}. Done so far: {state.steps} step(s), {done}. Not done: the task was not completed."
        _log.warning(
            "run stopped",
            extra={"fields": {"run_id": state.run_id, "cap": stop.cap, "steps": state.steps, "tokens": state.tokens}},
        )
        state = state.with_(status=RunStatus.STOPPED, final_text=text, stop_reason=stop.cap)
        self._save(state)
        return state
