"""Budgets around the agent loop: steps, tokens and wall-clock time, each checked on its own."""

from __future__ import annotations

from dataclasses import dataclass

from scheduling_agent.domain.errors import BudgetExceeded


@dataclass(slots=True)
class Budget:
    """Three independent caps. `check` raises `BudgetExceeded` naming the cap that fired."""

    max_steps: int
    max_tokens: int
    max_seconds: float
    started_at: float
    steps: int = 0
    tokens: int = 0

    def check(self, now: float) -> None:
        """Called before every action: a long tool call between checks can blow the time cap on its own."""
        if self.steps >= self.max_steps:
            raise BudgetExceeded("steps", f"step cap reached: {self.steps}/{self.max_steps}")
        if self.tokens >= self.max_tokens:
            raise BudgetExceeded("tokens", f"token cap reached: {self.tokens}/{self.max_tokens}")
        if now - self.started_at >= self.max_seconds:
            raise BudgetExceeded("seconds", f"time cap reached: {now - self.started_at:.1f}s/{self.max_seconds:g}s")

    def spend(self, tokens: int) -> None:
        """Record one step and the tokens it used."""
        self.steps += 1
        self.tokens += tokens
