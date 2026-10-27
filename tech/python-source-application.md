# Python source, the application layer

## What it is

This note walks through every Python file of the `application` layer of `scheduling_agent`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **application** layer holds the *use cases*: the steps that combine domain objects to do one job (run the meter, answer a question, resume an agent run). It talks to the outside only through *ports*, small interfaces (protocols) that the infrastructure layer implements.

## Why this repository uses it

Because use cases depend on ports and not on real services, the tests can run them with in-memory fakes, and the same use case works with a recorded model, a local model or Claude.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/application/__init__.py` | 1 non-blank lines |
| `src/scheduling_agent/application/agent.py` | 193 non-blank lines |
| `src/scheduling_agent/application/memory_service.py` | 52 non-blank lines |
| `src/scheduling_agent/application/ports.py` | 85 non-blank lines |
| `src/scheduling_agent/application/task_runner.py` | 128 non-blank lines |
| `src/scheduling_agent/application/tools.py` | 224 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/scheduling_agent/application/__init__.py`

In its own words: "Use cases and the ports they need. Depends on the domain only."

1 non-blank lines.

`src/scheduling_agent/application/__init__.py`, lines 1 to 1:

```python
"""Use cases and the ports they need. Depends on the domain only."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/scheduling_agent/application/agent.py`

In its own words: "The agent loop: model step, tool calls, a checkpoint after every step, writes only after a person approves."

193 non-blank lines; it defines `UnknownRun`, `AgentConfig`, `memory_block`, `SchedulingAgent`.

`src/scheduling_agent/application/agent.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Makes the module `uuid` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `MemoryService` (Remember what people say, recall the three most relevant facts for a task, forget on request.) from the project module `scheduling_agent.application.memory_service`.
- Brings in `ApprovalStore` (Proposals waiting for a person, and what the person decided.), `AuditLog` (Append-only record of every write attempt.), `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `CheckpointStore` (Saved run state.), `Clock` (Time, injected so tests are deterministic.), `FailPoints` (Named places where a test can kill the process, to prove a crash there is survivable.) from the project module `scheduling_agent.application.ports`.
- Brings in `ToolBox` (Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly.), `dump` (Tool results are compact, sorted JSON.), `tool_specs` (The tool definitions as the model sees them.) from the project module `scheduling_agent.application.tools`.
- Brings in `Budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.) from the project module `scheduling_agent.domain.budget`.
- Brings in `BudgetExceeded` (A run hit one of its caps: steps, tokens or wall-clock time.), `DomainError` (Base class for every error this package raises on purpose.) from the project module `scheduling_agent.domain.errors`.

`src/scheduling_agent/application/agent.py`, lines 15 to 25:

```python
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, Role, ToolCall
from scheduling_agent.domain.memory import Fact
from scheduling_agent.domain.prompts import Prompt
from scheduling_agent.domain.proposals import ApprovalStatus, Proposal
from scheduling_agent.domain.run import PendingWrite, RunState, RunStatus

_log = logging.getLogger(__name__)


class UnknownRun(DomainError):
    """No saved run with that id."""
```

- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `ToolCall` (A tool call the model asked for.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Fact` (Something a person said about their own calendar, with where and when they said it and when it lapses.) from the project module `scheduling_agent.domain.memory`.
- Brings in `Prompt` (A prompt as sent to the model, with the version that produced a given result.) from the project module `scheduling_agent.domain.prompts`.
- Brings in `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `PendingWrite` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.), `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.), `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `UnknownRun`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "No saved run with that id."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/agent.py`, lines 28 to 39:

```python
@dataclass(frozen=True, slots=True)
class AgentConfig:
    """The caps of a run and the size of one model answer."""

    max_steps: int = 12
    max_tokens: int = 4000
    max_seconds: float = 30.0
    max_output_tokens: int = 400


def memory_block(facts: list[Fact]) -> str:
    """The recalled facts as lines of the first message, with who said them and when."""
```

- Defines the class `AgentConfig`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The caps of a run and the size of one model answer."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `max_steps` as a whole number and sets it to the number `12`.
- Declares `max_tokens` as a whole number and sets it to the number `4000`.
- Declares `max_seconds` as a decimal number and sets it to the number `30.0`.
- Declares `max_output_tokens` as a whole number and sets it to the number `400`.
- Defines the function `memory_block`. It returns text. The author's own description: "The recalled facts as lines of the first message, with who said them and when."
- Its parameters:
    - `facts` holds a list of the project type `Fact`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/agent.py`, lines 40 to 47:

```python
    if not facts:
        return ""
    lines = [f"- {f.person}: {f.text} (said {f.stated_on}, session {f.session})" for f in facts]
    return "\n\nWhat people told you earlier (use it):\n" + "\n".join(lines)


class SchedulingAgent:
    """Books, moves and cancels meetings through tools, inside budgets, saving its state after every step."""
```

- Decision: the indented lines below run only when `not facts` is true.
  - `not` flips true and false.
- Ends the function and gives back empty text to the caller.
- Stores a list built by looping under the name `lines`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of `'\n\nWhat people told you earlier (use it):\n' + '\n'.joi...` to the caller.
  - `+` is add.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the class `SchedulingAgent`. The author's own description: "Books, moves and cancels meetings through tools, inside budgets, saving its state after every step."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/agent.py`, lines 49 to 62:

```python
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
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `model` holds the project type `ChatModel`.
    - `tools` holds the project type `ToolBox`.
    - `checkpoints` holds the project type `CheckpointStore`.
    - `approvals` holds the project type `ApprovalStore`.
    - `audit` holds the project type `AuditLog`.
    - `memory` holds the project type `MemoryService`.
    - `clock` holds the project type `Clock`.
    - `prompt` holds the project type `Prompt`.
    - `config` holds the project type `AgentConfig`.
    - `failpoints` holds the project type `FailPoints`.
    - `new_run_id` holds a function; if the caller leaves it out it is a small function.

`src/scheduling_agent/application/agent.py`, lines 63 to 76:

```python
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
```

- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `tools` under the name `self._tools` (as an attribute of this object, so other methods can use it).
- Stores the value named `checkpoints` under the name `self._checkpoints` (as an attribute of this object, so other methods can use it).
- Stores the value named `approvals` under the name `self._approvals` (as an attribute of this object, so other methods can use it).
- Stores the value named `audit` under the name `self._audit` (as an attribute of this object, so other methods can use it).
- Stores the value named `memory` under the name `self._memory` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores the value named `prompt` under the name `self._prompt` (as an attribute of this object, so other methods can use it).
- Stores the value named `config` under the name `self._config` (as an attribute of this object, so other methods can use it).
- Stores the value named `failpoints` under the name `self._failpoints` (as an attribute of this object, so other methods can use it).
- Stores the value named `new_run_id` under the name `self._new_run_id` (as an attribute of this object, so other methods can use it).
- Defines the method `start`. It returns the project type `RunState`. The author's own description: "Begin a run: recall what people said, save the new run, then drive it until it stops or waits."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds text.
    - `session` holds text.
    - `run_id` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/agent.py`, lines 77 to 90:

```python
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
```

- Stores the result of calling `self._memory.recall` under the name `facts`.
  - The method `recall` of the project's `MemoryService` (The most relevant live facts for a task: those of the people it names, ranked by similarity and recency.).
- Stores the result of calling `ChatMessage.user` under the name `first`.
  - The method `user` of `ChatMessage`.
  - `+` is add.
  - `memory_block`, a function defined in this file or passed in.
- Stores the result of calling `RunState` under the name `state`.
  - `RunState` from the project's `scheduling_agent.domain.run` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - The method `_new_run_id` of `self`.
  - The method `now` of `self._clock`.
- Calls the method `save` of `self._checkpoints` with 2 argument(s); the result is not kept.
  - The method `save` of `self._checkpoints`.
  - The method `now` of `self._clock`.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
  - `len` counts the items in a collection (or the characters in text).
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Ends the function and gives back the result of calling `self._drive` to the caller.
  - The method `_drive` of this object.
- Defines the method `resume`. It returns the project type `RunState`. The author's own description: "Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._checkpoints.load` under the name `state`.
  - The method `load` of `self._checkpoints`.
- Decision: the indented lines below run only when `state is None` is true.
  - `is` means the very same object.

`src/scheduling_agent/application/agent.py`, lines 91 to 104:

```python
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
```

- Raises an error: the result of calling `UnknownRun`. Execution jumps out to the nearest matching `except`.
  - `UnknownRun`, a class of this project (No saved run with that id.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `state.status in (RunStatus.DONE, RunStatus.STOPPED, RunStatus.FAILED)` is true.
  - `in` means is contained in.
- Ends the function and gives back the value named `state` to the caller.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back the result of calling `self._drive` to the caller.
  - The method `_drive` of this object.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Defines the method `_save`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
- Calls the method `save` of `self._checkpoints` with 2 argument(s); the result is not kept.
  - The method `save` of `self._checkpoints`.
  - The method `now` of `self._clock`.
- Defines the method `_drive`. It returns the project type `RunState`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
- Stores the attribute `_config` of this object under the name `cfg`.
- Stores the result of calling `Budget` under the name `budget`.
  - `Budget` from the project's `scheduling_agent.domain.budget` (Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired.).
  - The method `monotonic` of `self._clock`.

`src/scheduling_agent/application/agent.py`, lines 105 to 114:

```python
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
```

- Loop: the indented lines below repeat as long as `True` is true.
- Decision: the indented lines below run only when `state.pending is not None` is true.
  - `is not` means not the same object.
- Stores the result of calling `self._settle` under the name `state`.
  - The method `_settle` of this object (Resolve the pending write: wait, reject, or (approved) execute it with its idempotency key.).
- Decision: the indented lines below run only when `state.status is RunStatus.AWAITING_APPROVAL` is true.
  - `is` means the very same object.
- Ends the function and gives back the value named `state` to the caller.
- Skips the rest of this round of the loop and starts the next.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Calls the method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.) with 1 argument(s); the result is not kept.
  - The method `check` of the project's `Budget` (Called before every action: a long tool call between checks can blow the time cap on its own.).
  - The method `monotonic` of `self._clock`.
- `except` handler: it runs when the `try` block raised the project type `BudgetExceeded`; `stop` names the error object.
- Ends the function and gives back the result of calling `self._stop` to the caller.
  - The method `_stop` of this object (A cap fired: say which one, what was done and what was not, and save the run as stopped.).

`src/scheduling_agent/application/agent.py`, lines 115 to 128:

```python
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
```

- Stores the result of calling `self._model.complete` under the name `response`.
  - The method `complete` of `self._model`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `tool_specs` from the project's `scheduling_agent.application.tools` (The tool definitions as the model sees them.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `+` is add.
- Calls the method `spend` of the project's `Budget` (Record one step and the tokens it used.) with 1 argument(s); the result is not kept.
  - The method `spend` of the project's `Budget` (Record one step and the tokens it used.).
  - `+` is add.
- Stores the result of calling `ChatMessage` under the name `assistant`.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Decision: the indented lines below run only when `not response.tool_calls` is true.
  - `not` flips true and false.

`src/scheduling_agent/application/agent.py`, lines 129 to 141:

```python
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
```

- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Calls the method `_save` of this object with 1 argument(s); the result is not kept.
  - The method `_save` of this object.
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Ends the function and gives back the value named `state` to the caller.
- Stores the result of calling `self._run_calls` under the name `state`.
  - The method `_run_calls` of this object (Run the calls of one model answer in order. The first write stops the turn: it becomes a pending proposal.).
- Decision: the indented lines below run only when `state.status is RunStatus.AWAITING_APPROVAL` is true.
  - `is` means the very same object.
- Ends the function and gives back the value named `state` to the caller.
- Defines the method `_run_calls`. It returns the project type `RunState`. The author's own description: "Run the calls of one model answer in order. The first write stops the turn: it becomes a pending proposal."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
    - `calls` holds a fixed list of the project type `ToolCall` (any length).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `results` as a list of the project type `ChatMessage` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `enumerate(calls)`; `(index, call)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Decision: the indented lines below run only when `not self._tools.is_write(call.name)` is true.
  - `not` flips true and false.
  - The method `is_write` of `self._tools`.

`src/scheduling_agent/application/agent.py`, lines 142 to 150:

```python
                results.append(
                    ChatMessage(Role.TOOL, dump(self._tools.read(call.name, call.arguments)), tool_call_id=call.id)
                )
                continue
            proposal = self._tools.propose(call.name, call.arguments)
            if not isinstance(proposal, Proposal):
                results.append(ChatMessage(Role.TOOL, dump(proposal), tool_call_id=call.id))
                continue
            outcome = self._tools.request_approval(state.run_id, state.steps, proposal)
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `dump` from the project's `scheduling_agent.application.tools` (Tool results are compact, sorted JSON.).
  - `read` on the stored object `self._tools`: it reads from an open file.
- Skips the rest of this round of the loop and starts the next.
- Stores the result of calling `self._tools.propose` under the name `proposal`.
  - The method `propose` of the project's `ToolBox` (Build the proposal for a write tool call, or an error result when the arguments or the target are bad.).
- Decision: the indented lines below run only when `not isinstance(proposal, Proposal)` is true.
  - `not` flips true and false.
  - `isinstance` asks whether a value is of a given type.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `dump` from the project's `scheduling_agent.application.tools` (Tool results are compact, sorted JSON.).
- Skips the rest of this round of the loop and starts the next.
- Stores the result of calling `self._tools.request_approval` under the name `outcome`.
  - The method `request_approval` of the project's `ToolBox` (Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write.).

`src/scheduling_agent/application/agent.py`, lines 151 to 164:

```python
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
```

- Stores the result of calling `PendingWrite` under the name `pending`.
  - `PendingWrite` from the project's `scheduling_agent.domain.run` (The write a run is waiting on: which step proposed it, the tool call to answer and the approval to watch.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `+` is add.
- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Calls the method `_save` of this object with 1 argument(s); the result is not kept.
  - The method `_save` of this object.
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Ends the function and gives back the value named `state` to the caller.

`src/scheduling_agent/application/agent.py`, lines 165 to 178:

```python
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
```

- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Calls the method `_save` of this object with 1 argument(s); the result is not kept.
  - The method `_save` of this object.
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Ends the function and gives back the value named `state` to the caller.
- Defines the method `_settle`. It returns the project type `RunState`. The author's own description: "Resolve the pending write: wait, reject, or (approved) execute it with its idempotency key."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the `pending` of `state` under the name `pending`.
- Checks that `pending is not None` is true; if it is not, the test fails with an `AssertionError`.
  - `is not` means not the same object.
- Stores the result of calling `self._approvals.get` under the name `approval`.
  - `get` on the stored object `self._approvals`: it reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `approval is None or approval.status is ApprovalStatus.PENDING` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
- Ends the function and gives back the result of calling `state.with_` to the caller.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Decision: the indented lines below run only when `approval.status is ApprovalStatus.REJECTED` is true.
  - `is` means the very same object.
- Stores a dictionary with 2 entries under the name `result`.

`src/scheduling_agent/application/agent.py`, lines 179 to 191:

```python
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
```

- `else:` — the indented lines below run when none of the conditions above were true.
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Stores the result of calling `self._tools.execute_write` under the name `result`.
  - The method `execute_write` of the project's `ToolBox` (Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.).
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Stores a list of 1 item(s) under the name `tool_messages`.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `dump` from the project's `scheduling_agent.application.tools` (Tool results are compact, sorted JSON.).
- Updates `tool_messages` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `dump` from the project's `scheduling_agent.application.tools` (Tool results are compact, sorted JSON.).

`src/scheduling_agent/application/agent.py`, lines 192 to 205:

```python
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
```

- Stores one of two values, chosen by a condition under the name `done`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `in` means is contained in.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - The method `digest` of `pending.proposal`.
- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Calls the method `_save` of this object with 1 argument(s); the result is not kept.
  - The method `_save` of this object.
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.
- Ends the function and gives back the value named `state` to the caller.
- Defines the method `_stop`. It returns the project type `RunState`. The author's own description: "A cap fired: say which one, what was done and what was not, and save the run as stopped."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
    - `stop` holds the project type `BudgetExceeded`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/agent.py`, lines 206 to 214:

```python
        done = f"{len(state.writes_done)} write(s) made" if state.writes_done else "no write was made"
        text = f"Stopped: {stop}. Done so far: {state.steps} step(s), {done}. Not done: the task was not completed."
        _log.warning(
            "run stopped",
            extra={"fields": {"run_id": state.run_id, "cap": stop.cap, "steps": state.steps, "tokens": state.tokens}},
        )
        state = state.with_(status=RunStatus.STOPPED, final_text=text, stop_reason=stop.cap)
        self._save(state)
        return state
```

- Stores one of two values, chosen by a condition under the name `done`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Stores a text built from pieces (an f-string) under the name `text`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls the method `warning` of `_log` with 2 argument(s); the result is not kept.
  - The method `warning` of `_log`.
- Stores the result of calling `state.with_` under the name `state`.
  - The method `with_` of the project's `RunState` (A copy with some fields changed (the dataclass is frozen).).
- Calls the method `_save` of this object with 1 argument(s); the result is not kept.
  - The method `_save` of this object.
- Ends the function and gives back the value named `state` to the caller.

### `src/scheduling_agent/application/memory_service.py`

In its own words: "Long-term memory with a write policy: only what a person states about themselves, one fact per topic."

52 non-blank lines; it defines `MemoryService`.

`src/scheduling_agent/application/memory_service.py`, lines 1 to 12:

```python
"""Long-term memory with a write policy: only what a person states about themselves, one fact per topic."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from scheduling_agent.application.ports import Clock, Embedder, MemoryStore
from scheduling_agent.domain.memory import Fact, compact, parse_statement, rank_facts
from scheduling_agent.domain.retrieval import cosine

_log = logging.getLogger(__name__)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Clock` (Time, injected so tests are deterministic.), `Embedder` (Turns texts into vectors.), `MemoryStore` (Facts people stated about themselves.) from the project module `scheduling_agent.application.ports`.
- Brings in `Fact` (Something a person said about their own calendar, with where and when they said it and when it lapses.), `compact` (The facts to keep after writing `new`.), `parse_statement` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.), `rank_facts` (The `top` live facts with the best blended score, best first (ties broken by newer first, then text).) from the project module `scheduling_agent.domain.memory`.
- Brings in `cosine` (Cosine similarity of two vectors (0.0 if either is all zeros).) from the project module `scheduling_agent.domain.retrieval`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.

`src/scheduling_agent/application/memory_service.py`, lines 15 to 25:

```python
class MemoryService:
    """Remember what people say, recall the three most relevant facts for a task, forget on request."""

    def __init__(
        self, store: MemoryStore, embedder: Embedder, clock: Clock, people: Sequence[str], top: int = 3
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._clock = clock
        self._people = tuple(people)
        self._top = top
```

- Defines the class `MemoryService`. The author's own description: "Remember what people say, recall the three most relevant facts for a task, forget on request."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `MemoryStore`.
    - `embedder` holds the project type `Embedder`.
    - `clock` holds the project type `Clock`.
    - `people` holds anything that behaves like a list of text.
    - `top` holds a whole number; if the caller leaves it out it is the number `3`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Stores the value named `embedder` under the name `self._embedder` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `tuple` under the name `self._people` (as an attribute of this object, so other methods can use it).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
- Stores the value named `top` under the name `self._top` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/application/memory_service.py`, lines 27 to 39:

```python
    def remember(self, person: str, statement: str, session: str) -> Fact | None:
        """Store a statement a person made about themselves. A sentence that states no usable fact is not kept.

        A fact about the same person and topic replaces the old one, so a changed preference leaves no trace of the
        old value in recall or in storage.
        """
        today = self._clock.today()
        fact = parse_statement(person, statement, session, today)
        if fact is None:
            _log.info("statement not kept", extra={"fields": {"person": person, "session": session}})
            return None
        existing = [f for f in self._store.facts() if f.person == person]
        others = [f for f in self._store.facts() if f.person != person]
```

- Defines the method `remember`. It returns the project type `Fact`, or nothing (None). The author's own description: "Store a statement a person made about themselves. A sentence that states no usable fact is not kept."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `person` holds text.
    - `statement` holds text.
    - `session` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._clock.today` under the name `today`.
  - The method `today` of `self._clock`.
- Stores the result of calling `parse_statement` under the name `fact`.
  - `parse_statement` from the project's `scheduling_agent.domain.memory` (Turn a sentence a person said about themselves into a fact, or None if it states nothing we keep.).
- Decision: the indented lines below run only when `fact is None` is true.
  - `is` means the very same object.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back nothing (`None`) to the caller.
- Stores a list built by looping under the name `existing`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `self._store`.
  - `==` means equal.
- Stores a list built by looping under the name `others`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `self._store`.
  - `!=` means not equal.

`src/scheduling_agent/application/memory_service.py`, lines 40 to 53:

```python
        self._store.replace([*others, *compact(existing, fact, today)])
        _log.info("fact stored", extra={"fields": {"person": person, "kind": fact.kind.value, "session": session}})
        return fact

    def recall(self, task: str) -> list[Fact]:
        """The most relevant live facts for a task: those of the people it names, ranked by similarity and recency."""
        today = self._clock.today()
        named = [p for p in self._people if p in task.lower()]
        candidates = [f for f in self._store.facts() if f.alive(today) and (not named or f.person in named)]
        if not candidates:
            return []
        vectors = self._embedder.embed([task, *[f.text for f in candidates]])
        scored = [(fact, cosine(vectors[0], vector)) for fact, vector in zip(candidates, vectors[1:], strict=True)]
        return rank_facts(scored, today, self._top)
```

- Calls `replace` on the stored object `self._store`: it replaces every occurrence of one piece of text with another with 1 argument(s); the result is not kept.
  - `replace` on the stored object `self._store`: it replaces every occurrence of one piece of text with another.
  - `compact` from the project's `scheduling_agent.domain.memory` (The facts to keep after writing `new`.).
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back the value named `fact` to the caller.
- Defines the method `recall`. It returns a list of the project type `Fact`. The author's own description: "The most relevant live facts for a task: those of the people it names, ranked by similarity and recency."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._clock.today` under the name `today`.
  - The method `today` of `self._clock`.
- Stores a list built by looping under the name `named`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.
  - `.lower(...)` turns text into lower case.
- Stores a list built by looping under the name `candidates`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `facts` of `self._store`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - The method `alive` of `f`.
  - `not` flips true and false.
  - `in` means is contained in.
- Decision: the indented lines below run only when `not candidates` is true.
  - `not` flips true and false.
- Ends the function and gives back an empty list to the caller.
- Stores the result of calling `self._embedder.embed` under the name `vectors`.
  - The method `embed` of `self._embedder`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores a list built by looping under the name `scored`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `cosine` from the project's `scheduling_agent.domain.retrieval` (Cosine similarity of two vectors (0.0 if either is all zeros).).
  - `zip` walks several collections side by side, item by item.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Ends the function and gives back the result of calling `rank_facts` to the caller.
  - `rank_facts` from the project's `scheduling_agent.domain.memory` (The `top` live facts with the best blended score, best first (ties broken by newer first, then text).).

`src/scheduling_agent/application/memory_service.py`, lines 55 to 64:

```python
    def facts(self) -> list[Fact]:
        """Everything remembered, for a person to inspect."""
        return self._store.facts()

    def forget(self, person: str) -> int:
        """Delete every fact about a person from storage; returns how many were removed."""
        facts = self._store.facts()
        kept = [f for f in facts if f.person != person]
        self._store.replace(kept)
        return len(facts) - len(kept)
```

- Defines the method `facts`. It returns a list of the project type `Fact`. The author's own description: "Everything remembered, for a person to inspect."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `self._store.facts` to the caller.
  - The method `facts` of `self._store`.
- Defines the method `forget`. It returns a whole number. The author's own description: "Delete every fact about a person from storage; returns how many were removed."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `person` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._store.facts` under the name `facts`.
  - The method `facts` of `self._store`.
- Stores a list built by looping under the name `kept`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `!=` means not equal.
- Calls `replace` on the stored object `self._store`: it replaces every occurrence of one piece of text with another with 1 argument(s); the result is not kept.
  - `replace` on the stored object `self._store`: it replaces every occurrence of one piece of text with another.
- Ends the function and gives back the result of `len(facts) - len(kept)` to the caller.
  - `-` is subtract.
  - `len` counts the items in a collection (or the characters in text).

### `src/scheduling_agent/application/ports.py`

In its own words: "The boundaries the use cases depend on. Adapters in `infrastructure` implement them."

85 non-blank lines; it defines `ChatModel`, `Embedder`, `Clock`, `CalendarPort`, `ApprovalStore`, `CheckpointStore`, `AuditLog`, `MemoryStore`, `FailPoints`.

`src/scheduling_agent/application/ports.py`, lines 1 to 14:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime`, `time` from the standard library module `datetime`.
- Brings in `Protocol` from the standard library module `typing`.
- Brings in `Approval` (A proposal and what a person decided about it.), `AuditLine` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).), `BookingResult` (What the calendar answered to a write: the event and whether the answer was a replay of an earlier key.) from the project module `scheduling_agent.domain.approvals`.
- Brings in `Event` (A meeting: who, when and for how long. `cancelled` events no longer block anyone's time.) from the project module `scheduling_agent.domain.calendar`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Fact` (Something a person said about their own calendar, with where and when they said it and when it lapses.) from the project module `scheduling_agent.domain.memory`.
- Brings in `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.
- Brings in `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.) from the project module `scheduling_agent.domain.run`.

`src/scheduling_agent/application/ports.py`, lines 17 to 28:

```python
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
```

- Defines the class `ChatModel`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "One chat model behind one interface: a vendor, a local server or a recording."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text. The author's own description: "The model id the responses come from."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false. The author's own description: "False when the provider rejects `temperature` and `top_p` (the request then says so)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

`src/scheduling_agent/application/ports.py`, lines 30 to 42:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...


class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
```

- Defines the method `complete`. It returns the project type `ChatResponse`. The author's own description: "Send one request. Raises `TransientModelError` or `PermanentModelError`."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Embedder`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Turns texts into vectors."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `embed`. It returns a list of a list of a decimal number. The author's own description: "One vector per text, in order."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/ports.py`, lines 43 to 56:

```python
        ...


class Clock(Protocol):
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class CalendarPort(Protocol):
```

- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Clock`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Time, injected so tests are deterministic."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `CalendarPort`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "The calendar service. Writes take an idempotency key; a repeated key returns the first result."

`src/scheduling_agent/application/ports.py`, lines 57 to 70:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `free_slots`. It returns a list of a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `first_day` holds a calendar date.
    - `last_day` holds a calendar date.
    - `minutes` holds a whole number.
    - `not_before` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
    - `not_after` holds a time of day, or nothing (None); if the caller leaves it out it is nothing (`None`).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `get_event`. It returns the project type `Event`. The author's own description: "The event, cancelled or not; raises `UnknownEvent`."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/ports.py`, lines 71 to 83:

```python
        ...

    def book(self, people: Sequence[str], start: datetime, minutes: int, idempotency_key: str) -> BookingResult: ...

    def cancel(self, event_id: str, idempotency_key: str) -> BookingResult: ...

    def active_events(self) -> list[Event]:
        """Every event that is not cancelled (used to judge a run by the calendar's real end state)."""
        ...


class ApprovalStore(Protocol):
    """Proposals waiting for a person, and what the person decided."""
```

- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `book`. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `people` holds anything that behaves like a list of text.
    - `start` holds a date and time.
    - `minutes` holds a whole number.
    - `idempotency_key` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `cancel`. It returns the project type `BookingResult`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `event_id` holds text.
    - `idempotency_key` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `active_events`. It returns a list of the project type `Event`. The author's own description: "Every event that is not cancelled (used to judge a run by the calendar's real end state)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `ApprovalStore`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Proposals waiting for a person, and what the person decided."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/ports.py`, lines 85 to 97:

```python
    def request(self, run_id: str, step: int, proposal: Proposal, now: datetime) -> Approval:
        """Create the approval for this run and step, or return the one that exists (idempotent)."""
        ...

    def get(self, approval_id: str) -> Approval | None: ...

    def decide(self, approval_id: str, approved: bool, by: str, now: datetime) -> Approval: ...

    def pending(self) -> list[Approval]: ...


class CheckpointStore(Protocol):
    """Saved run state."""
```

- Defines the method `request`. It returns the project type `Approval`. The author's own description: "Create the approval for this run and step, or return the one that exists (idempotent)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
    - `step` holds a whole number.
    - `proposal` holds the project type `Proposal`.
    - `now` holds a date and time.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `get`. It returns the project type `Approval`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `approval_id` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `decide`. It returns the project type `Approval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `approval_id` holds text.
    - `approved` holds true or false.
    - `by` holds text.
    - `now` holds a date and time.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `pending`. It returns a list of the project type `Approval`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `CheckpointStore`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Saved run state."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/ports.py`, lines 99 to 111:

```python
    def save(self, state: RunState, now: datetime) -> None:
        """Write the whole run state in one transaction."""
        ...

    def load(self, run_id: str) -> RunState | None: ...

    def unfinished(self) -> list[str]:
        """Ids of runs that are running or waiting for an approval."""
        ...


class AuditLog(Protocol):
    """Append-only record of every write attempt."""
```

- Defines the method `save`. It returns nothing (None). The author's own description: "Write the whole run state in one transaction."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `state` holds the project type `RunState`.
    - `now` holds a date and time.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `load`. It returns the project type `RunState`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `unfinished`. It returns a list of text. The author's own description: "Ids of runs that are running or waiting for an approval."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `AuditLog`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Append-only record of every write attempt."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/ports.py`, lines 113 to 125:

```python
    def append(self, line: AuditLine) -> None: ...

    def lines(self, run_id: str | None = None) -> list[AuditLine]: ...


class MemoryStore(Protocol):
    """Facts people stated about themselves."""

    def facts(self) -> list[Fact]: ...

    def replace(self, facts: Sequence[Fact]) -> None:
        """Replace the whole set of facts (after compaction)."""
        ...
```

- Defines the method `append`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `line` holds the project type `AuditLine`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `lines`. It returns a list of the project type `AuditLine`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `MemoryStore`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Facts people stated about themselves."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `facts`. It returns a list of the project type `Fact`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `replace`. It returns nothing (None). The author's own description: "Replace the whole set of facts (after compaction)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `facts` holds anything that behaves like a list of the project type `Fact`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

`src/scheduling_agent/application/ports.py`, lines 128 to 131:

```python
class FailPoints(Protocol):
    """Named places where a test can kill the process, to prove a crash there is survivable."""

    def hit(self, name: str) -> None: ...
```

- Defines the class `FailPoints`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Named places where a test can kill the process, to prove a crash there is survivable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `hit`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

### `src/scheduling_agent/application/task_runner.py`

In its own words: "Run the task set and judge every task by the calendar's real end state, never by what the agent said."

128 non-blank lines; it defines `Approver`, `ExpectedWritesApprover`, `CalendarAdmin`, `AgentKit`, `TaskResult`, `TaskRunner`, `_writes_without_approval`.

`src/scheduling_agent/application/task_runner.py`, lines 1 to 14:

```python
"""Run the task set and judge every task by the calendar's real end state, never by what the agent said."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from scheduling_agent.application.agent import SchedulingAgent
from scheduling_agent.application.memory_service import MemoryService
from scheduling_agent.application.ports import ApprovalStore, AuditLog, CalendarPort, CheckpointStore, Clock
from scheduling_agent.domain.approvals import AuditLine
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Protocol` from the standard library module `typing`.
- Brings in `SchedulingAgent` (Books, moves and cancels meetings through tools, inside budgets, saving its state after every step.) from the project module `scheduling_agent.application.agent`.
- Brings in `MemoryService` (Remember what people say, recall the three most relevant facts for a task, forget on request.) from the project module `scheduling_agent.application.memory_service`.
- Brings in `ApprovalStore` (Proposals waiting for a person, and what the person decided.), `AuditLog` (Append-only record of every write attempt.), `CalendarPort` (The calendar service. Writes take an idempotency key; a repeated key returns the first result.), `CheckpointStore` (Saved run state.), `Clock` (Time, injected so tests are deterministic.) from the project module `scheduling_agent.application.ports`.
- Brings in `AuditLine` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).) from the project module `scheduling_agent.domain.approvals`.
- Brings in `Action` (The three writes.), `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.) from the project module `scheduling_agent.domain.proposals`.

`src/scheduling_agent/application/task_runner.py`, lines 15 to 28:

```python
from scheduling_agent.domain.run import RunState, RunStatus
from scheduling_agent.domain.tasks import TaskSpec, end_state, expected_end_state

_log = logging.getLogger(__name__)
MAX_APPROVAL_ROUNDS = 6


class Approver(Protocol):
    """The person: decides whether a proposal is what the task asked for."""

    def decide(self, task: TaskSpec, proposal: Proposal) -> bool: ...


class ExpectedWritesApprover:
```

- Brings in `RunState` (Everything needed to continue a run after a crash: it is saved after every step, in one transaction.), `RunStatus` (Where a run is.) from the project module `scheduling_agent.domain.run`.
- Brings in `TaskSpec` (A task in words, what people told the agent earlier, and the changes to the calendar it should end with.), `end_state` (The calendar's real state as comparable keys.), `expected_end_state` (The seeded calendar with the task's removals and additions applied, as comparable keys.) from the project module `scheduling_agent.domain.tasks`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Stores the number `6` under the name `MAX_APPROVAL_ROUNDS`.
- Defines the class `Approver`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "The person: decides whether a proposal is what the task asked for."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `decide`. It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds the project type `TaskSpec`.
    - `proposal` holds the project type `Proposal`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `ExpectedWritesApprover`. The author's own description: "Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else."

`src/scheduling_agent/application/task_runner.py`, lines 29 to 42:

```python
    """Approves a proposal exactly when it is one of the changes the task expects, and rejects everything else."""

    def decide(self, task: TaskSpec, proposal: Proposal) -> bool:
        args = proposal.args
        if proposal.action is Action.BOOK:
            return (tuple(sorted(args["people"])), args["start"], args["minutes"]) in task.add
        if proposal.action is Action.CANCEL:
            return args["event_id"] in task.remove
        new_key = (tuple(sorted(args["people"])), args["new_start"], args["minutes"])
        return args["event_id"] in task.remove and new_key in task.add


class CalendarAdmin(Protocol):
    """Resets the calendar to its seed between task runs (a demo and test aid)."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `decide`. It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds the project type `TaskSpec`.
    - `proposal` holds the project type `Proposal`.
- Stores the `args` of `proposal` under the name `args`.
- Decision: the indented lines below run only when `proposal.action is Action.BOOK` is true.
  - `is` means the very same object.
- Ends the function and gives back whether `(tuple(sorted(args['people'])), args['start'], args['minu...` holds to the caller.
  - `in` means is contained in.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `sorted` returns a new list with the items in order.
- Decision: the indented lines below run only when `proposal.action is Action.CANCEL` is true.
  - `is` means the very same object.
- Ends the function and gives back whether `args['event_id'] in task.remove` holds to the caller.
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a tuple of 3 item(s) under the name `new_key`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `sorted` returns a new list with the items in order.
- Ends the function and gives back the result of combining conditions: `args['event_id'] in task.remove and new_key in task.add` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `CalendarAdmin`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Resets the calendar to its seed between task runs (a demo and test aid)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/task_runner.py`, lines 44 to 56:

```python
    def reset(self) -> None: ...


@dataclass(frozen=True, slots=True)
class AgentKit:
    """One agent with the stores it was built on, so a runner can read what it did."""

    agent: SchedulingAgent
    approvals: ApprovalStore
    audit: AuditLog
    checkpoints: CheckpointStore
    memory: MemoryService
    calendar: CalendarPort
```

- Defines the method `reset`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `AgentKit`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One agent with the stores it was built on, so a runner can read what it did."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `agent` as the project type `SchedulingAgent`; it has no default, so a value must be given when the object is made.
- Declares `approvals` as the project type `ApprovalStore`; it has no default, so a value must be given when the object is made.
- Declares `audit` as the project type `AuditLog`; it has no default, so a value must be given when the object is made.
- Declares `checkpoints` as the project type `CheckpointStore`; it has no default, so a value must be given when the object is made.
- Declares `memory` as the project type `MemoryService`; it has no default, so a value must be given when the object is made.
- Declares `calendar` as the project type `CalendarPort`; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/application/task_runner.py`, lines 59 to 70:

```python
@dataclass(frozen=True, slots=True)
class TaskResult:
    """One attempt at one task."""

    task_id: str
    attempt: int
    passed: bool
    status: RunStatus
    steps: int
    tokens: int
    approvals_granted: int
    approvals_rejected: int
```

- Defines the class `TaskResult`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One attempt at one task."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `task_id` as text; it has no default, so a value must be given when the object is made.
- Declares `attempt` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `passed` as true or false; it has no default, so a value must be given when the object is made.
- Declares `status` as the project type `RunStatus`; it has no default, so a value must be given when the object is made.
- Declares `steps` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `approvals_granted` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `approvals_rejected` as a whole number; it has no default, so a value must be given when the object is made.

`src/scheduling_agent/application/task_runner.py`, lines 71 to 77:

```python
    writes_without_approval: int
    final_text: str
    stop_reason: str


class TaskRunner:
    """Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects."""
```

- Declares `writes_without_approval` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `final_text` as text; it has no default, so a value must be given when the object is made.
- Declares `stop_reason` as text; it has no default, so a value must be given when the object is made.
- Defines the class `TaskRunner`. The author's own description: "Resets the calendar, seeds memory, runs the agent with a person who approves only what the task expects."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/task_runner.py`, lines 79 to 91:

```python
    def __init__(
        self,
        admin: CalendarAdmin,
        build: Callable[[], AgentKit],
        approver: Approver,
        clock: Clock,
    ) -> None:
        self._admin = admin
        self._build = build
        self._approver = approver
        self._clock = clock

    def run_once(self, task: TaskSpec, attempt: int) -> TaskResult:
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `admin` holds the project type `CalendarAdmin`.
    - `build` holds a function.
    - `approver` holds the project type `Approver`.
    - `clock` holds the project type `Clock`.
- Stores the value named `admin` under the name `self._admin` (as an attribute of this object, so other methods can use it).
- Stores the value named `build` under the name `self._build` (as an attribute of this object, so other methods can use it).
- Stores the value named `approver` under the name `self._approver` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Defines the method `run_once`. It returns the project type `TaskResult`. The author's own description: "One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `task` holds the project type `TaskSpec`.
    - `attempt` holds a whole number.

`src/scheduling_agent/application/task_runner.py`, lines 92 to 105:

```python
        """One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task."""
        self._admin.reset()
        kit = self._build()
        seed = kit.calendar.active_events()
        for person, statement in task.facts:
            kit.memory.remember(person, statement, session=f"{task.id}-earlier")
        state = kit.agent.start(task.text, session=f"{task.id}-run{attempt}", run_id=f"{task.id}-r{attempt}")
        granted = rejected = rounds = 0
        while state.status is RunStatus.AWAITING_APPROVAL and rounds < MAX_APPROVAL_ROUNDS:
            rounds += 1
            for approval in [a for a in kit.approvals.pending() if a.run_id == state.run_id]:
                approve = self._approver.decide(task, approval.proposal)
                kit.approvals.decide(approval.id, approve, "task-runner", self._clock.now())
                granted += approve
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Calls the method `reset` of `self._admin`; the result is not kept.
  - The method `reset` of `self._admin`.
- Stores the result of calling `self._build` under the name `kit`.
  - The method `_build` of `self`.
- Stores the result of calling `kit.calendar.active_events` under the name `seed`.
  - The method `active_events` of `kit.calendar`.
- Loop: the indented lines below run once for each item of `task.facts`; `(person, statement)` names the current item.
- Calls the method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.) with 3 argument(s); the result is not kept.
  - The method `remember` of the project's `MemoryService` (Store a statement a person made about themselves. A sentence that states no usable fact is not kept.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `kit.agent.start` under the name `state`.
  - `.start(...)` starts a thread or process.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the number `0` under the name `granted`, `rejected`, `rounds`.
- Loop: the indented lines below repeat as long as `state.status is RunStatus.AWAITING_APPROVAL and rounds < ...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `<` means less than.
- Updates `rounds` in place: `+=` applies `+` with the number `1` and stores the result back.
- Loop: the indented lines below run once for each item of `[a for a in kit.approvals.pending() if a.run_id == state....`; `approval` names the current item.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `pending` of `kit.approvals`.
  - `==` means equal.
- Stores the result of calling `self._approver.decide` under the name `approve`.
  - The method `decide` of `self._approver`.
- Calls the method `decide` of `kit.approvals` with 4 argument(s); the result is not kept.
  - The method `decide` of `kit.approvals`.
  - The method `now` of `self._clock`.
- Updates `granted` in place: `+=` applies `+` with the value named `approve` and stores the result back.

`src/scheduling_agent/application/task_runner.py`, lines 106 to 109:

```python
                rejected += not approve
            state = kit.agent.resume(state.run_id)
        actual = end_state(kit.calendar.active_events())
        passed = actual == expected_end_state(seed, task)
```

- Updates `rejected` in place: `+=` applies `+` with `not approve` and stores the result back.
  - `not` flips true and false.
- Stores the result of calling `kit.agent.resume` under the name `state`.
  - The method `resume` of the project's `SchedulingAgent` (Continue a saved run from its last checkpoint. Writes already made are replayed with the same keys.).
- Stores the result of calling `end_state` under the name `actual`.
  - `end_state` from the project's `scheduling_agent.domain.tasks` (The calendar's real state as comparable keys.).
  - The method `active_events` of `kit.calendar`.
- Stores whether `actual == expected_end_state(seed, task)` holds under the name `passed`.
  - `==` means equal.
  - `expected_end_state` from the project's `scheduling_agent.domain.tasks` (The seeded calendar with the task's removals and additions applied, as comparable keys.).

`src/scheduling_agent/application/task_runner.py`, lines 110 to 122:

```python
        return TaskResult(
            task.id,
            attempt,
            passed,
            state.status,
            state.steps,
            state.tokens,
            granted,
            rejected,
            _writes_without_approval(kit, state),
            state.final_text,
            state.stop_reason,
        )
```

- Ends the function and gives back the result of calling `TaskResult` to the caller.
  - `TaskResult`, a class of this project (One attempt at one task.).
  - `_writes_without_approval`, a function defined in this file or passed in.

`src/scheduling_agent/application/task_runner.py`, lines 124 to 133:

```python
    def run_all(
        self, tasks: list[TaskSpec], repeats: int, stop_requested: Callable[[], bool] = lambda: False
    ) -> list[TaskResult]:
        """Every task `repeats` times, in order."""
        results: list[TaskResult] = []
        for task in tasks:
            for attempt in range(1, repeats + 1):
                if stop_requested():
                    return results
                result = self.run_once(task, attempt)
```

- Defines the method `run_all`. It returns a list of the project type `TaskResult`. The author's own description: "Every task `repeats` times, in order."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `tasks` holds a list of the project type `TaskSpec`.
    - `repeats` holds a whole number.
    - `stop_requested` holds a function; if the caller leaves it out it is a small function.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `results` as a list of the project type `TaskResult` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `tasks`; `task` names the current item.
- Loop: the indented lines below run once for each item of `range(1, repeats + 1)`; `attempt` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `+` is add.
- Decision: the indented lines below run only when `stop_requested()` is true.
  - `stop_requested`, a function defined in this file or passed in.
- Ends the function and gives back the value named `results` to the caller.
- Stores the result of calling `self.run_once` under the name `result`.
  - The method `run_once` of this object (One attempt: fresh calendar, fresh agent database, facts told in an earlier session, then the task.).

`src/scheduling_agent/application/task_runner.py`, lines 134 to 147:

```python
                _log.info(
                    "task attempt",
                    extra={
                        "fields": {"task": task.id, "attempt": attempt, "passed": result.passed, "steps": result.steps}
                    },
                )
                results.append(result)
        return results


def _writes_without_approval(kit: AgentKit, state: RunState) -> int:
    """'written' audit lines whose approval is missing or not approved: must be zero."""
    lines: list[AuditLine] = kit.audit.lines(state.run_id)
    bad = 0
```

- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `results` to the caller.
- Defines the function `_writes_without_approval`. It returns a whole number. The author's own description: "'written' audit lines whose approval is missing or not approved: must be zero."
- Its parameters:
    - `kit` holds the project type `AgentKit`.
    - `state` holds the project type `RunState`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `lines` as a list of the project type `AuditLine` and sets it to the result of calling `kit.audit.lines`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `lines` of `kit.audit`.
- Stores the number `0` under the name `bad`.

`src/scheduling_agent/application/task_runner.py`, lines 148 to 154:

```python
    for line in lines:
        if line.outcome != "written":
            continue
        approval = kit.approvals.get(line.approval_id) if line.approval_id else None
        if approval is None or approval.status is not ApprovalStatus.APPROVED:
            bad += 1
    return bad
```

- Loop: the indented lines below run once for each item of `lines`; `line` names the current item.
- Decision: the indented lines below run only when `line.outcome != 'written'` is true.
  - `!=` means not equal.
- Skips the rest of this round of the loop and starts the next.
- Stores one of two values, chosen by a condition under the name `approval`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `approval is None or approval.status is not ApprovalStatus.APPROVED` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `is not` means not the same object.
- Updates `bad` in place: `+=` applies `+` with the number `1` and stores the result back.
- Ends the function and gives back the value named `bad` to the caller.

### `src/scheduling_agent/application/tools.py`

In its own words: "The agent's tools: reads run as they are, every write is a proposal that waits for a person's approval."

224 non-blank lines; it defines `tool_specs`, `dump`, `_time`, `ToolBox`.

`src/scheduling_agent/application/tools.py`, lines 1 to 14:

```python
"""The agent's tools: reads run as they are, every write is a proposal that waits for a person's approval."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import date, datetime, time
from typing import Any

from scheduling_agent.application.ports import ApprovalStore, AuditLog, CalendarPort, Clock, FailPoints
from scheduling_agent.domain.approvals import AuditLine
from scheduling_agent.domain.errors import ApprovalError, CalendarError
from scheduling_agent.domain.llm import ToolSpec
from scheduling_agent.domain.proposals import Action, ApprovalStatus, Proposal, write_key
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `Callable`, `Mapping` from the standard library module `collections.abc`.
- Brings in `date`, `datetime`, `time` from the standard library module `datetime`.
- Brings in `Any` from the standard library module `typing`.
- Brings in `ApprovalStore` (Proposals waiting for a person, and what the person decided.), `AuditLog` (Append-only record of every write attempt.), `CalendarPort` (The calendar service. Writes take an idempotency key; a repeated key returns the first result.), `Clock` (Time, injected so tests are deterministic.), `FailPoints` (Named places where a test can kill the process, to prove a crash there is survivable.) from the project module `scheduling_agent.application.ports`.
- Brings in `AuditLine` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).) from the project module `scheduling_agent.domain.approvals`.
- Brings in `ApprovalError` (An approval is missing, not approved, or was granted for a different proposal.), `CalendarError` (The calendar refused or could not do what was asked.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `scheduling_agent.domain.llm`.
- Brings in `Action` (The three writes.), `ApprovalStatus` (Where an approval is: waiting for a person, approved or rejected.), `Proposal` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.), `write_key` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.) from the project module `scheduling_agent.domain.proposals`.

`src/scheduling_agent/application/tools.py`, lines 16 to 23:

```python
READ_TOOLS = ("find_free_slots", "get_event")
WRITE_TOOLS = {"book_meeting": Action.BOOK, "move_meeting": Action.MOVE, "cancel_meeting": Action.CANCEL}
MAX_SLOTS_SHOWN = 12


def tool_specs() -> tuple[ToolSpec, ...]:
    """The tool definitions as the model sees them."""
    people = {"type": "array", "items": {"type": "string"}, "description": "lowercase first names, for example alice"}
```

- Stores a tuple of 2 item(s) under the name `READ_TOOLS`.
- Stores a dictionary with 3 entries under the name `WRITE_TOOLS`.
- Stores the number `12` under the name `MAX_SLOTS_SHOWN`.
- Defines the function `tool_specs`. It returns a fixed list of the project type `ToolSpec` (any length). The author's own description: "The tool definitions as the model sees them."
- It takes no parameters.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a dictionary with 3 entries under the name `people`.

`src/scheduling_agent/application/tools.py`, lines 24 to 76:

```python
    return (
        ToolSpec(
            "find_free_slots",
            "Find start times at which every listed person is free. Weekdays, 09:00 to 17:00, on the half hour.",
            {
                "type": "object",
                "properties": {
                    "people": people,
                    "first_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "last_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "minutes": {"type": "integer", "description": "length, a multiple of 30"},
                    "not_before": {"type": "string", "description": "HH:MM, earliest start"},
                    "not_after": {"type": "string", "description": "HH:MM, latest end"},
                },
                "required": ["people", "first_day", "last_day", "minutes"],
            },
        ),
        ToolSpec(
            "get_event",
            "Read one event by id: who is in it, when it starts and how long it is.",
            {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]},
        ),
        ToolSpec(
            "book_meeting",
            "Propose a new meeting. A person must approve it before it is booked.",
            {
                "type": "object",
                "properties": {
                    "people": people,
                    "start": {"type": "string", "description": "YYYY-MM-DDTHH:MM"},
                    "minutes": {"type": "integer"},
                },
                "required": ["people", "start", "minutes"],
            },
        ),
        ToolSpec(
            "move_meeting",
            "Propose moving an event to a new start. A person must approve it first.",
            {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "new_start": {"type": "string", "description": "YYYY-MM-DDTHH:MM"},
                },
                "required": ["event_id", "new_start"],
            },
        ),
        ToolSpec(
            "cancel_meeting",
            "Propose cancelling an event. A person must approve it first.",
            {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]},
        ),
    )
```

- Ends the function and gives back a tuple of 5 item(s) to the caller.
  - `ToolSpec` from the project's `scheduling_agent.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).

`src/scheduling_agent/application/tools.py`, lines 79 to 89:

```python
def dump(value: Mapping[str, Any]) -> str:
    """Tool results are compact, sorted JSON."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _time(text: str | None) -> time | None:
    return time.fromisoformat(text) if text else None


class ToolBox:
    """Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly."""
```

- Defines the function `dump`. It returns text. The author's own description: "Tool results are compact, sorted JSON."
- Its parameters:
    - `value` holds anything that behaves like a dictionary from text to any value.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `json.dumps` to the caller.
  - `json.dumps` turns Python data into JSON text.
- Defines the function `_time`. It returns a time of day, or nothing (None).
- Its parameters:
    - `text` holds text, or nothing (None).
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `time.fromisoformat` from the standard library module `datetime`.
- Defines the class `ToolBox`. The author's own description: "Runs tools against the calendar. A write only runs with an approval that matches its proposal exactly."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/scheduling_agent/application/tools.py`, lines 91 to 103:

```python
    def __init__(
        self,
        calendar: CalendarPort,
        approvals: ApprovalStore,
        audit: AuditLog,
        clock: Clock,
        failpoints: FailPoints,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._calendar = calendar
        self._approvals = approvals
        self._audit = audit
        self._clock = clock
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `calendar` holds the project type `CalendarPort`.
    - `approvals` holds the project type `ApprovalStore`.
    - `audit` holds the project type `AuditLog`.
    - `clock` holds the project type `Clock`.
    - `failpoints` holds the project type `FailPoints`.
    - `now` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `calendar` under the name `self._calendar` (as an attribute of this object, so other methods can use it).
- Stores the value named `approvals` under the name `self._approvals` (as an attribute of this object, so other methods can use it).
- Stores the value named `audit` under the name `self._audit` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).

`src/scheduling_agent/application/tools.py`, lines 104 to 114:

```python
        self._failpoints = failpoints
        self._now = now or clock.now

    @staticmethod
    def is_write(name: str) -> bool:
        return name in WRITE_TOOLS

    def read(self, name: str, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run a read tool. A problem with the arguments or the calendar comes back as an error the model can read."""
        try:
            if name == "find_free_slots":
```

- Stores the value named `failpoints` under the name `self._failpoints` (as an attribute of this object, so other methods can use it).
- Stores the result of combining conditions: `now or clock.now` under the name `self._now` (as an attribute of this object, so other methods can use it).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `is_write`. `@staticmethod` makes it an ordinary function that lives inside the class. It returns true or false.
- Its parameters:
    - `name` holds text.
- Ends the function and gives back whether `name in WRITE_TOOLS` holds to the caller.
  - `in` means is contained in.
- Defines the method `read`. It returns a dictionary from text to any value. The author's own description: "Run a read tool. A problem with the arguments or the calendar comes back as an error the model can read."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
    - `args` holds anything that behaves like a dictionary from text to any value.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Decision: the indented lines below run only when `name == 'find_free_slots'` is true.
  - `==` means equal.

`src/scheduling_agent/application/tools.py`, lines 115 to 126:

```python
                slots = self._calendar.free_slots(
                    [str(p) for p in args["people"]],
                    date.fromisoformat(str(args["first_day"])),
                    date.fromisoformat(str(args["last_day"])),
                    int(args["minutes"]),
                    _time(args.get("not_before")),
                    _time(args.get("not_after")),
                )
                shown = [s.isoformat(timespec="minutes") for s in slots[:MAX_SLOTS_SHOWN]]
                return {"slots": shown, "count": len(slots), "truncated": len(slots) > MAX_SLOTS_SHOWN}
            if name == "get_event":
                event = self._calendar.get_event(str(args["event_id"]))
```

- Stores the result of calling `self._calendar.free_slots` under the name `slots`.
  - The method `free_slots` of `self._calendar`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `date.fromisoformat` reads a date from ISO text.
  - `int` turns a value into a whole number.
  - `_time`, a function defined in this file or passed in.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Stores a list built by looping under the name `shown`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Ends the function and gives back a dictionary with 3 entries to the caller.
  - `len` counts the items in a collection (or the characters in text).
  - `>` means greater than.
- Decision: the indented lines below run only when `name == 'get_event'` is true.
  - `==` means equal.
- Stores the result of calling `self._calendar.get_event` under the name `event`.
  - The method `get_event` of `self._calendar`.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/scheduling_agent/application/tools.py`, lines 127 to 140:

```python
                return {
                    "event_id": event.id,
                    "people": list(event.people),
                    "start": event.start.isoformat(timespec="minutes"),
                    "minutes": event.minutes,
                    "cancelled": event.cancelled,
                }
        except CalendarError as error:
            return {"error": f"{type(error).__name__}: {error}"}
        except (KeyError, ValueError, TypeError) as error:
            return {"error": f"bad arguments: {error}"}
        return {"error": f"unknown tool {name}"}

    def propose(self, name: str, args: Mapping[str, Any]) -> Proposal | dict[str, Any]:
```

- Ends the function and gives back a dictionary with 5 entries to the caller.
  - `list` makes a list (a copy when given a collection).
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- `except` handler: it runs when the `try` block raised `(KeyError, ValueError, TypeError)`; `error` names the error object.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `propose`. It returns the project type `Proposal`, or a dictionary from text to any value. The author's own description: "Build the proposal for a write tool call, or an error result when the arguments or the target are bad."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `name` holds text.
    - `args` holds anything that behaves like a dictionary from text to any value.

`src/scheduling_agent/application/tools.py`, lines 141 to 150:

```python
        """Build the proposal for a write tool call, or an error result when the arguments or the target are bad."""
        action = WRITE_TOOLS[name]
        try:
            if action is Action.BOOK:
                people = sorted(str(p) for p in args["people"])
                start = datetime.fromisoformat(str(args["start"])).isoformat(timespec="minutes")
                return Proposal(action, {"people": people, "start": start, "minutes": int(args["minutes"])})
            event = self._calendar.get_event(str(args["event_id"]))
            if event.cancelled:
                return {"error": f"event {event.id} is already cancelled"}
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the part of `WRITE_TOOLS` picked by `name` under the name `action`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Decision: the indented lines below run only when `action is Action.BOOK` is true.
  - `is` means the very same object.
- Stores the result of calling `sorted` under the name `people`.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `datetime.fromisoformat(str(args['start'])).isof...` under the name `start`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `Proposal` to the caller.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
  - `int` turns a value into a whole number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `self._calendar.get_event` under the name `event`.
  - The method `get_event` of `self._calendar`.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `event.cancelled` is true.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/application/tools.py`, lines 151 to 164:

```python
            snapshot = {
                "event_id": event.id,
                "people": sorted(event.people),
                "minutes": event.minutes,
                "start": event.start.isoformat(timespec="minutes"),
            }
            if action is Action.CANCEL:
                return Proposal(action, snapshot)
            new_start = datetime.fromisoformat(str(args["new_start"])).isoformat(timespec="minutes")
            return Proposal(action, {**snapshot, "new_start": new_start})
        except CalendarError as error:
            return {"error": f"{type(error).__name__}: {error}"}
        except (KeyError, ValueError, TypeError) as error:
            return {"error": f"bad arguments: {error}"}
```

- Stores a dictionary with 4 entries under the name `snapshot`.
  - `sorted` returns a new list with the items in order.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
- Decision: the indented lines below run only when `action is Action.CANCEL` is true.
  - `is` means the very same object.
- Ends the function and gives back the result of calling `Proposal` to the caller.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- Stores the result of calling `datetime.fromisoformat(str(args['new_start']))....` under the name `new_start`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `Proposal` to the caller.
  - `Proposal` from the project's `scheduling_agent.domain.proposals` (A write the agent wants to make. An approval is for exactly this content, not for a tool name.).
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- `except` handler: it runs when the `try` block raised `(KeyError, ValueError, TypeError)`; `error` names the error object.
- Ends the function and gives back a dictionary with 1 entry to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/scheduling_agent/application/tools.py`, lines 166 to 168:

```python
    def request_approval(self, run_id: str, step: int, proposal: Proposal) -> dict[str, Any]:
        """Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write."""
        approval = self._approvals.request(run_id, step, proposal, self._now())
```

- Defines the method `request_approval`. It returns a dictionary from text to any value. The author's own description: "Record the proposal for a person to decide on and write the audit line for the refused (unapproved) write."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
    - `step` holds a whole number.
    - `proposal` holds the project type `Proposal`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self._approvals.request` under the name `approval`.
  - The method `request` of `self._approvals`.
  - The method `_now` of `self`.

`src/scheduling_agent/application/tools.py`, lines 169 to 182:

```python
        self._audit.append(
            AuditLine(
                self._now(),
                run_id,
                step,
                proposal.action.value,
                "refused",
                approval.id,
                "no approval yet; proposal recorded",
            )
        )
        return {"status": "needs_approval", "approval_id": approval.id, "proposal": json.loads(proposal.canonical())}

    def execute_write(self, run_id: str, step: int, proposal: Proposal, approval_id: str | None) -> dict[str, Any]:
```

- Calls `append` on the stored object `self._audit`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._audit`: it adds one item at the end of a list.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
  - The method `_now` of `self`.
- Ends the function and gives back a dictionary with 3 entries to the caller.
  - `json.loads` turns JSON text into Python data.
  - The method `canonical` of the project's `Proposal` (Stable JSON: sorted keys, no spaces. The same proposal always gives the same text.).
- Defines the method `execute_write`. It returns a dictionary from text to any value. The author's own description: "Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
    - `step` holds a whole number.
    - `proposal` holds the project type `Proposal`.
    - `approval_id` holds text, or nothing (None).

`src/scheduling_agent/application/tools.py`, lines 183 to 196:

```python
        """Run the write if `approval_id` is an approved approval for exactly this proposal; otherwise refuse and log.

        The calendar calls carry keys built from the run id and the step, so running this twice after a crash is safe.
        """
        try:
            self._check_approval(proposal, approval_id)
        except ApprovalError as error:
            self._audit.append(
                AuditLine(self._now(), run_id, step, proposal.action.value, "refused", approval_id, str(error))
            )
            return {"status": "refused", "detail": str(error)}
        try:
            result = self._apply(run_id, step, proposal)
        except CalendarError as error:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Calls the method `_check_approval` of this object with 2 argument(s); the result is not kept.
  - The method `_check_approval` of this object.
- `except` handler: it runs when the `try` block raised the project type `ApprovalError`; `error` names the error object.
- Calls `append` on the stored object `self._audit`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._audit`: it adds one item at the end of a list.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
  - The method `_now` of `self`.
  - `str` turns a value into text.
- Ends the function and gives back a dictionary with 2 entries to the caller.
  - `str` turns a value into text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._apply` under the name `result`.
  - The method `_apply` of this object.
- `except` handler: it runs when the `try` block raised the project type `CalendarError`; `error` names the error object.

`src/scheduling_agent/application/tools.py`, lines 197 to 208:

```python
            self._audit.append(
                AuditLine(
                    self._now(),
                    run_id,
                    step,
                    proposal.action.value,
                    "failed",
                    approval_id,
                    f"{type(error).__name__}: {error}",
                )
            )
            return {"status": "failed", "error": f"{type(error).__name__}: {error}"}
```

- Calls `append` on the stored object `self._audit`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._audit`: it adds one item at the end of a list.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
  - The method `_now` of `self`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Ends the function and gives back a dictionary with 2 entries to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.

`src/scheduling_agent/application/tools.py`, lines 209 to 222:

```python
        self._audit.append(
            AuditLine(self._now(), run_id, step, proposal.action.value, "written", approval_id, result["event_id"])
        )
        return result

    def _check_approval(self, proposal: Proposal, approval_id: str | None) -> None:
        if approval_id is None:
            raise ApprovalError("no approval id: a person has to approve every write")
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ApprovalError(f"unknown approval {approval_id}")
        if approval.status is not ApprovalStatus.APPROVED:
            raise ApprovalError(f"approval {approval_id} is {approval.status.value}")
        if approval.proposal.digest() != proposal.digest():
```

- Calls `append` on the stored object `self._audit`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._audit`: it adds one item at the end of a list.
  - `AuditLine` from the project's `scheduling_agent.domain.approvals` (One write attempt: refused (no valid approval) or written (with the approval that allowed it).).
  - The method `_now` of `self`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the value named `result` to the caller.
- Defines the method `_check_approval`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `proposal` holds the project type `Proposal`.
    - `approval_id` holds text, or nothing (None).
- Decision: the indented lines below run only when `approval_id is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
- Stores the result of calling `self._approvals.get` under the name `approval`.
  - `get` on the stored object `self._approvals`: it reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `approval is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `approval.status is not ApprovalStatus.APPROVED` is true.
  - `is not` means not the same object.
- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `approval.proposal.digest() != proposal.digest()` is true.
  - `!=` means not equal.
  - The method `digest` of `approval.proposal`.
  - The method `digest` of `proposal`.

`src/scheduling_agent/application/tools.py`, lines 223 to 236:

```python
            raise ApprovalError(f"approval {approval_id} was granted for a different proposal")

    def _apply(self, run_id: str, step: int, proposal: Proposal) -> dict[str, Any]:
        args = proposal.args
        if proposal.action is Action.BOOK:
            booked = self._calendar.book(
                args["people"], datetime.fromisoformat(args["start"]), args["minutes"], write_key(run_id, step)
            )
            return {"status": "booked", "event_id": booked.event.id, "replayed": booked.replayed}
        if proposal.action is Action.CANCEL:
            cancelled = self._calendar.cancel(args["event_id"], write_key(run_id, step))
            return {"status": "cancelled", "event_id": cancelled.event.id, "replayed": cancelled.replayed}
        cancelled = self._calendar.cancel(args["event_id"], write_key(run_id, step, "cancel"))
        self._failpoints.hit("between_move_cancel_and_book")
```

- Raises an error: the result of calling `ApprovalError`. Execution jumps out to the nearest matching `except`.
  - `ApprovalError` from the project's `scheduling_agent.domain.errors` (An approval is missing, not approved, or was granted for a different proposal.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `_apply`. It returns a dictionary from text to any value.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `run_id` holds text.
    - `step` holds a whole number.
    - `proposal` holds the project type `Proposal`.
- Stores the `args` of `proposal` under the name `args`.
- Decision: the indented lines below run only when `proposal.action is Action.BOOK` is true.
  - `is` means the very same object.
- Stores the result of calling `self._calendar.book` under the name `booked`.
  - The method `book` of `self._calendar`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Ends the function and gives back a dictionary with 3 entries to the caller.
- Decision: the indented lines below run only when `proposal.action is Action.CANCEL` is true.
  - `is` means the very same object.
- Stores the result of calling `self._calendar.cancel` under the name `cancelled`.
  - The method `cancel` of `self._calendar`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Ends the function and gives back a dictionary with 3 entries to the caller.
- Stores the result of calling `self._calendar.cancel` under the name `cancelled`.
  - The method `cancel` of `self._calendar`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Calls the method `hit` of `self._failpoints` with 1 argument(s); the result is not kept.
  - The method `hit` of `self._failpoints`.

`src/scheduling_agent/application/tools.py`, lines 237 to 245:

```python
        booked = self._calendar.book(
            args["people"], datetime.fromisoformat(args["new_start"]), args["minutes"], write_key(run_id, step, "book")
        )
        return {
            "status": "moved",
            "event_id": booked.event.id,
            "cancelled": cancelled.event.id,
            "replayed": booked.replayed,
        }
```

- Stores the result of calling `self._calendar.book` under the name `booked`.
  - The method `book` of `self._calendar`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `datetime.fromisoformat` reads a date and time from ISO text.
  - `write_key` from the project's `scheduling_agent.domain.proposals` (The idempotency key of a write: built from the run id and the step number, never from a clock or a random value.).
- Ends the function and gives back a dictionary with 4 entries to the caller.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import scheduling_agent.application.__init__; print(scheduling_agent.application.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Use cases and the ports they need. Depends on the domain only.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/scheduling_agent/application').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
agent.py 4
memory_service.py 1
ports.py 9
task_runner.py 7
tools.py 4
```

3. The rule that keeps this layer in its place: both contracts must be KEPT.

```bash
.venv/bin/lint-imports --no-logo 2>&1 | grep -E 'KEPT|BROKEN'
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT
```

## Mistakes people make

- **Common mistakes with this layer.** Calling a concrete adapter directly from a use case (the layering contract would fail), hiding state in module-level variables, or doing slow input/output inside a loop without a way to stop it. Here the ports are protocols and long loops check a shutdown flag.

## Check yourself

1. What is the job of `src/scheduling_agent/application/__init__.py`?

   *Answer:* Use cases and the ports they need. Depends on the domain only.

2. What is the job of `src/scheduling_agent/application/agent.py`?

   *Answer:* The agent loop: model step, tool calls, a checkpoint after every step, writes only after a person approves.

3. What is the job of `src/scheduling_agent/application/memory_service.py`?

   *Answer:* Long-term memory with a write policy: only what a person states about themselves, one fact per topic.

4. What is the job of `src/scheduling_agent/application/ports.py`?

   *Answer:* The boundaries the use cases depend on. Adapters in `infrastructure` implement them.

5. What is the job of `src/scheduling_agent/application/task_runner.py`?

   *Answer:* Run the task set and judge every task by the calendar's real end state, never by what the agent said.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).
