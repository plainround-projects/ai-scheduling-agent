"""Readers for prompt files and the task set."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scheduling_agent.domain.prompts import Prompt, PromptNotFound
from scheduling_agent.domain.tasks import InvalidTasks, TaskSpec, validate_tasks

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


class FilePromptStore:
    """Prompt files at `<root>/<name>/<version>.md`; the front matter's `version:` line must match the file name."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def load(self, name: str, version: str) -> Prompt:
        path = self._root / name / f"{version}.md"
        if not path.exists():
            raise PromptNotFound(f"no prompt file {path}")
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            raise PromptNotFound(f"{path} has no front matter with a version line")
        header = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
        if header.get("version", "").strip() != version:
            raise PromptNotFound(
                f"{path}: the version line says {header.get('version', '').strip()!r}, not {version!r}"
            )
        return Prompt(name, version, match.group(2).strip())


def load_tasks(path: Path) -> list[TaskSpec]:
    """Read the 30 tasks; a bad line is reported with its number, and the lesson's mix is checked."""
    tasks: list[TaskSpec] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                tasks.append(TaskSpec.from_json(json.loads(line)))
            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
                raise InvalidTasks(f"{path}:{number}: {error!r}") from error
    validate_tasks(tasks)
    return tasks
