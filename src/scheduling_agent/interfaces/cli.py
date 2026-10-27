"""The `agent` command: run a task, approve or reject a write, resume a run, tell it a preference, run the task set."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from collections.abc import Sequence

from scheduling_agent.application.agent import UnknownRun
from scheduling_agent.application.task_runner import AgentKit, ExpectedWritesApprover, TaskResult, TaskRunner
from scheduling_agent.domain.errors import ApprovalError, DomainError
from scheduling_agent.domain.prompts import PromptNotFound
from scheduling_agent.domain.run import RunState, RunStatus
from scheduling_agent.domain.tasks import InvalidTasks
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.env import ConfigurationError
from scheduling_agent.infrastructure.files import load_tasks
from scheduling_agent.infrastructure.logging import configure_logging
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from scheduling_agent.infrastructure.settings import AgentSettings
from scheduling_agent.infrastructure.shutdown import ShutdownSignal
from scheduling_agent.infrastructure.sqlite import connect
from scheduling_agent.infrastructure.wiring import build_calendar, build_embedder, build_kit

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_AWAITING, EXIT_STOPPED = 0, 1, 2, 5, 6
_log = logging.getLogger("agent")


def build_parser() -> argparse.ArgumentParser:
    """The `agent` argument parser."""
    parser = argparse.ArgumentParser(prog="agent", description="A scheduling agent that asks before it writes.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one task")
    run.add_argument("task")
    run.add_argument("--session", default="cli")
    run.add_argument("--run-id")
    run.add_argument(
        "--auto-approve", action="store_true", help="approve every proposal without asking (demos and tests)"
    )
    resume = sub.add_parser("resume", help="continue a saved run from its last checkpoint")
    resume.add_argument("run_id")
    resume.add_argument("--auto-approve", action="store_true")
    for name in ("approve", "reject"):
        decide = sub.add_parser(name, help=f"{name} a pending proposal")
        decide.add_argument("approval_id")
        decide.add_argument("--resume", action="store_true", help="resume the run right away")
    sub.add_parser("pending", help="list proposals waiting for a decision")
    sub.add_parser("unfinished", help="list runs that a crash left unfinished")
    audit = sub.add_parser("audit", help="print the audit log")
    audit.add_argument("--run")
    tell = sub.add_parser("tell", help="tell the agent something about a person's calendar")
    tell.add_argument("person")
    tell.add_argument("statement")
    tell.add_argument("--session", default="cli")
    sub.add_parser("memory", help="print what the agent remembers")
    forget = sub.add_parser("forget", help="delete everything the agent remembers about a person")
    forget.add_argument("person")
    tasks = sub.add_parser("tasks", help="run the task set against the calendar service and judge by end state")
    tasks.add_argument("--runs", type=int, default=3)
    tasks.add_argument("--only", help="a single task id")
    return parser


def _kit(settings: AgentSettings) -> AgentKit:
    clock = SystemClock()
    model = build_chat_model(ModelSettings.from_env(), clock)
    return build_kit(settings, model, clock, build_embedder(settings))


def _show(state: RunState) -> None:
    print(f"run {state.run_id}: {state.status.value} after {state.steps} step(s), {state.tokens} tokens")
    if state.status is RunStatus.AWAITING_APPROVAL and state.pending is not None:
        print(f"  waiting for approval {state.pending.approval_id}: {state.pending.proposal.canonical()}")
        print(f"  decide with: agent approve {state.pending.approval_id} --resume   (or: agent reject ...)")
    if state.final_text:
        print(f"  {state.final_text}")


def _drive_with_approval(kit: AgentKit, state: RunState, auto: bool) -> RunState:
    clock = SystemClock()
    while auto and state.status is RunStatus.AWAITING_APPROVAL and state.pending is not None:
        kit.approvals.decide(state.pending.approval_id, True, "auto-approve", clock.now())
        state = kit.agent.resume(state.run_id)
    return state


def _exit(state: RunState) -> int:
    return {RunStatus.AWAITING_APPROVAL: EXIT_AWAITING, RunStatus.STOPPED: EXIT_STOPPED}.get(state.status, EXIT_OK)


def _tasks(args: argparse.Namespace, settings: AgentSettings, shutdown: ShutdownSignal) -> int:
    tasks = load_tasks(settings.tasks_path)
    if args.only:
        tasks = [t for t in tasks if t.id == args.only]
    clock = SystemClock()
    calendar = build_calendar(settings)
    model_settings = ModelSettings.from_env()
    embedder = build_embedder(settings)

    def build() -> AgentKit:
        return build_kit(
            settings, build_chat_model(model_settings, clock), clock, embedder, calendar, connect(":memory:")
        )

    runner = TaskRunner(calendar, build, ExpectedWritesApprover(), clock)
    results = runner.run_all(tasks, args.runs, lambda: shutdown.requested)
    print(render_task_report(results, args.runs))
    return EXIT_OK if results and all(r.passed for r in results) else EXIT_ERROR


def render_task_report(results: list[TaskResult], runs: int) -> str:
    """Pass rate per task across the runs, and the totals the lesson asks for."""
    by_task: dict[str, list[TaskResult]] = defaultdict(list)
    for result in results:
        by_task[result.task_id].append(result)
    lines = ["task                 passed  steps  tokens  writes without approval  ended"]
    for task_id, items in by_task.items():
        passed = sum(r.passed for r in items)
        steps = round(sum(r.steps for r in items) / len(items))
        tokens = round(sum(r.tokens for r in items) / len(items))
        bad = sum(r.writes_without_approval for r in items)
        ended = ",".join(sorted({f"{r.status.value}{':' + r.stop_reason if r.stop_reason else ''}" for r in items}))
        lines.append(f"{task_id:<20} {passed}/{len(items):<5} {steps:>5} {tokens:>7} {bad:>24}  {ended}")
    total = sum(r.passed for r in results)
    lines.append(f"\ntasks passed: {total}/{len(results)} attempts ({len(by_task)} tasks x {runs} runs)")
    lines.append(f"writes without an approval: {sum(r.writes_without_approval for r in results)}")
    granted = sum(r.approvals_granted for r in results)
    lines.append(f"approvals granted: {granted}, rejected: {sum(r.approvals_rejected for r in results)}")
    return "\n".join(lines)


def _decide(kit: AgentKit, args: argparse.Namespace) -> int:
    approval = kit.approvals.decide(args.approval_id, args.command == "approve", "cli", SystemClock().now())
    print(f"{approval.id}: {approval.status.value} ({approval.proposal.canonical()})")
    if args.resume:
        state = kit.agent.resume(approval.run_id)
        _show(state)
        return _exit(state)
    return EXIT_OK


def _inspect(kit: AgentKit, args: argparse.Namespace) -> int:
    if args.command == "pending":
        for approval in kit.approvals.pending():
            print(f"{approval.id}  run {approval.run_id}  step {approval.step}  {approval.proposal.canonical()}")
    elif args.command == "unfinished":
        for run_id in kit.checkpoints.unfinished():
            print(run_id)
    elif args.command == "audit":
        for line in kit.audit.lines(args.run):
            stamp = f"{line.at:%Y-%m-%dT%H:%M:%S}"
            print(f"{stamp} run {line.run_id} step {line.step} {line.action} {line.outcome} {line.detail}")
    else:
        facts = [
            {"person": f.person, "kind": f.kind.value, "value": f.value, "text": f.text, "stated_on": str(f.stated_on)}
            for f in kit.memory.facts()
        ]
        print(json.dumps(facts, indent=2))
    return EXIT_OK


def _run(args: argparse.Namespace, settings: AgentSettings, shutdown: ShutdownSignal) -> int:
    if args.command == "tasks":
        return _tasks(args, settings, shutdown)
    kit = _kit(settings)
    if args.command == "run":
        state = _drive_with_approval(kit, kit.agent.start(args.task, args.session, args.run_id), args.auto_approve)
        _show(state)
        return _exit(state)
    if args.command == "resume":
        state = _drive_with_approval(kit, kit.agent.resume(args.run_id), args.auto_approve)
        _show(state)
        return _exit(state)
    if args.command in ("approve", "reject"):
        return _decide(kit, args)
    if args.command == "tell":
        fact = kit.memory.remember(args.person.lower(), args.statement, args.session)
        print(f"remembered: {fact.text}" if fact else "that states nothing about their calendar that I keep")
        return EXIT_OK
    if args.command == "forget":
        print(f"forgot {kit.memory.forget(args.person.lower())} fact(s) about {args.person}")
        return EXIT_OK
    return _inspect(kit, args)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 5 waiting for approval, 6 stopped by a budget)."""
    args = build_parser().parse_args(argv)
    try:
        settings = AgentSettings.from_env()
        configure_logging(settings.log_level)
        shutdown = ShutdownSignal()
        shutdown.install()
        return _run(args, settings, shutdown)
    except (ConfigurationError, PromptNotFound, InvalidTasks) as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except (UnknownRun, ApprovalError) as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_ERROR
    except DomainError as error:
        print(f"agent: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
