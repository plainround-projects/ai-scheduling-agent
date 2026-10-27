"""Named places where a test can kill the process with SIGKILL, to prove a crash there is survivable."""

from __future__ import annotations

import os
import signal
from collections.abc import Mapping


class NoFailPoints:
    """The production default: nothing ever fails on purpose."""

    def hit(self, name: str) -> None:
        return None


class SigkillAt:
    """Kills the whole process with SIGKILL (no cleanup, no `finally`) when execution reaches the named point.

    Enabled only by the `FAILPOINT` environment variable, which exists for the crash tests and is never set otherwise.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    def hit(self, name: str) -> None:
        if name == self._name:
            os.kill(os.getpid(), signal.SIGKILL)


def from_env(environ: Mapping[str, str]) -> NoFailPoints | SigkillAt:
    """`SigkillAt` when `FAILPOINT` names a point, otherwise `NoFailPoints`."""
    name = environ.get("FAILPOINT", "").strip()
    return SigkillAt(name) if name else NoFailPoints()
