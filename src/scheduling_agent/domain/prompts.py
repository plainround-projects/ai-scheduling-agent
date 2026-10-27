"""A prompt file: its name, its version line and its text."""

from __future__ import annotations

from dataclasses import dataclass

from scheduling_agent.domain.errors import DomainError


class PromptNotFound(DomainError):
    """No prompt file for that name and version, or the file's version line does not match."""


@dataclass(frozen=True, slots=True)
class Prompt:
    """A prompt as sent to the model, with the version that produced a given result."""

    name: str
    version: str
    text: str
