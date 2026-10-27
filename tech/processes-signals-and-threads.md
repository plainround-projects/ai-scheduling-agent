# Processes, signals and threads

## What it is

A **process** is one running program: its own memory, its own open files, and a number called the **process id** (pid). A process can start other processes (children) and can end with an **exit code**: `0` means success, anything else means a problem. A **signal** is a small message the operating system delivers to a process: `SIGTERM` politely asks it to stop, `SIGINT` is what Ctrl-C sends, `SIGKILL` removes it immediately and cannot be caught. A **thread** is a separate line of execution *inside* one process; threads share memory.

Three questions follow from these: how does a program stop cleanly when asked (signals), what happens to its data if it is killed mid-way (crash safety), and what goes wrong when two threads touch the same data (locks).

## Why this repository uses it

The repositories make promises about interruption: "a killed run resumes with no call paid twice", "the service finishes in-flight requests when stopped", "two processes racing on one order produce one refund". Those promises can only be tested with real processes, real signals and real threads, so the tests start the programs as subprocesses and kill them, and the code protects shared data with locks.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/infrastructure/shutdown.py` | turns SIGINT and SIGTERM into a flag the loops check |
| `tests/integration/` | start real subprocesses, send signals, check the state afterwards |
| `Makefile` | `nohup ... &`, `kill`, `kill -0`, pid files (see `make.md`) |
| `src/scheduling_agent/` | `threading` locks and events, thread pools where used |

## How it works underneath

**Signals are asynchronous.** The kernel interrupts the process at any point and calls the handler; Python runs it between two bytecode instructions of the main thread. That is why handlers only set a flag.

**SIGKILL and durability.** Because SIGKILL gives the program no chance to react, anything it had not yet written to disk is lost, and a file may end in a half-written row. Code that must survive this writes data in small durable steps (append one line, flush, `fsync`) and reads state back carefully on start.

**Exit codes.** A parent reads the child's exit code. Conventions here: 0 success, 2 bad settings, 3 refused before starting (budget), 4 interrupted (resume later), 5 waiting for approval (scheduling agent).

**Threads and the GIL.** In standard Python only one thread runs Python code at a time (the global interpreter lock), but a thread that waits for the network or the disk lets others run. So threads help with waiting, not with heavy calculation, and they still need locks around shared data, because a switch can happen between any two steps of `x = x + 1`.

**Deadlock.** If thread A waits for a lock that B holds while B waits for one A holds, both wait forever. The code takes one lock at a time and keeps critical sections short.

**Daemon-free shutdown.** A thread pool is closed with `with`; services close their connections after `uvicorn.run` returns.

## Walkthrough of this repository's use

### Telling a running program to stop: `src/scheduling_agent/infrastructure/shutdown.py`

`src/scheduling_agent/infrastructure/shutdown.py`, lines 1 to 29:

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()

    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        self._requested.set()

    @property
    def requested(self) -> bool:
        return self._requested.is_set()
```

- `signal.signal(number, handler)` tells the operating system: when this process receives signal `number`, call `handler` instead of the default action. For `SIGINT` (Ctrl-C) the default is to stop at once; for `SIGTERM` (the polite stop request from `kill`) the default is also to stop at once. Here both are routed to `_handle`.
- `threading.Event()` is a thread-safe flag: `set()` raises it, `is_set()` reads it. A signal handler runs at an unpredictable moment between two lines of the main program, so it must do almost nothing; it only raises the flag.
- The work loops check `requested` between units of work (between two model calls, for example). So a stop request lets the **current call finish**, writes its result, and then the loop ends cleanly, closing files. The command-line program then returns a special exit code that says "interrupted, resume later" (the exit codes are listed below).
- `FrameType` is only a type hint for the second argument Python passes to a handler (the running code's stack frame); the handler ignores it (`_frame`).

### Proving it with a real process

The integration tests start the program as a **subprocess** and kill it.

`tests/integration/test_processes.py`, lines 36 to 56:

```python
def test_a_real_sigkill_at_four_points_and_a_clean_run_leave_exactly_five_new_events_none_twice(service, tmp_path):
    reset(service)
    baseline = len(events(service))
    for index, (point, task) in enumerate(CRASH_CASES, start=1):
        run_id = f"crash-{index}"
        killed = agent(service, tmp_path, "run", task, "--run-id", run_id, "--auto-approve", failpoint=point)
        if point is None:
            assert killed.returncode == 0, killed.stderr
        else:
            assert killed.returncode == -signal.SIGKILL, (point, killed.returncode, killed.stderr)
            resumed = agent(service, tmp_path, "resume", run_id, "--auto-approve")
            assert resumed.returncode == 0, resumed.stderr
            assert "done after" in resumed.stdout
            assert "Booked event" in resumed.stdout
        written = agent(service, tmp_path, "audit", "--run", run_id).stdout.count(" written ")
        assert written == 1, (point, written)
    after = events(service)
    assert len(after) == baseline + 5
    keys = [(tuple(e["people"]), e["start"], e["minutes"]) for e in after]  # type: ignore[arg-type,var-annotated]
    assert len(keys) == len(set(keys))
    assert double_bookings(service) == 0
```

- `SIGKILL` (sent with `send_signal` or `os.kill`) removes the process at once: no handler runs, no file is closed, no cleanup. This is the **crash test**: after it the program must still be correct when restarted.
- `returncode == -signal.SIGKILL`: when a process is ended by a signal, Python reports its exit code as the *negative* signal number (`-9` for SIGKILL), so the test can tell "killed" from "exited with an error".
- `SIGTERM` tests the polite path: the process finishes what it is doing and exits with its "interrupted" exit code.
- A *failpoint* is a named place in the program where a test can make it kill itself on purpose (see the last section).

### Threads and locks

A **thread** is an independent line of execution inside one process; threads share memory. Two threads changing the same data at the same time can corrupt it, so shared state is guarded by a **lock**: only one thread at a time can hold it.

`src/scheduling_agent/infrastructure/calendar_db.py`, lines 56 to 60:

```python
        self._db = connection
        self._now = now
        self._lock = threading.RLock()  # one connection, many request threads: calls take turns

    @_locked
```

A `Lock` is held with `with self._lock:`; other threads that reach the same line wait. An `RLock` (re-entrant) may be taken again by the thread that already holds it.

### Crashing on purpose: failpoints

To test crash safety the code can kill itself at a named place. The environment variable `FAILPOINT` names the place; when execution reaches it, the process sends itself SIGKILL.

`src/scheduling_agent/infrastructure/failpoints.py`, lines 1 to 40:

```python
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

```

## Try it yourself

1. Signals are numbers: SIGINT is 2, SIGKILL is 9, SIGTERM is 15.

```bash
.venv/bin/python -c "import os, signal; print(os.getpid() > 0, signal.SIGTERM.value, signal.SIGINT.value, signal.SIGKILL.value)"
```

What you should see (captured from this repository):

```text
True 15 2 9
```

2. Start a background `sleep`, send it SIGTERM, and read its exit code: 143, which is 128 plus the signal number 15.

```bash
sh -c 'sleep 30 & echo $! > /dev/null; kill $!; wait $! 2>/dev/null; echo "exit code after SIGTERM: $?"'
```

What you should see (captured from this repository):

```text
exit code after SIGTERM: 143
```

3. Start a child process and read its exit code.

```bash
.venv/bin/python -c "import subprocess, sys; p = subprocess.run([sys.executable, '-c', 'import sys; sys.exit(7)']); print(p.returncode)"
```

What you should see (captured from this repository):

```text
7
```

4. Four threads each add 1 fifty thousand times to a shared counter under a lock: the total is exactly 200000.

```bash
.venv/bin/python - <<'EOF'
import threading
n = 0
lock = threading.Lock()
def work():
    global n
    for _ in range(50000):
        with lock:
            n += 1
ts = [threading.Thread(target=work) for _ in range(4)]
[t.start() for t in ts]
[t.join() for t in ts]
print(n)
EOF
```

What you should see (captured from this repository):

```text
200000
```

5. A process sends itself SIGTERM; because a handler is installed, it runs instead of stopping the process.

```bash
.venv/bin/python - <<'EOF'
import signal, os, time
seen = []
signal.signal(signal.SIGTERM, lambda n, f: seen.append(n))
os.kill(os.getpid(), signal.SIGTERM)
time.sleep(0.1)
print('handler ran, signal number', seen)
EOF
```

What you should see (captured from this repository):

```text
handler ran, signal number [15]
```

## Mistakes people make

- **Doing real work in a signal handler.** It can run in the middle of anything. The handler only sets a flag.
- **Assuming `kill` is instant.** SIGTERM is a request; the program stops after the current unit of work.
- **Trusting a file after `kill -9`.** It may end mid-row; readers cut a torn tail.
- **Sharing data between threads without a lock.** Updates can interleave and be lost.
- **Waiting forever.** `communicate(timeout=...)` and deadlines in the tests prevent a hung test run.
- **Leaving a child running.** The tests always kill or wait for the subprocesses they start.

## Check yourself

1. What is the difference between SIGTERM and SIGKILL?

   *Answer:* SIGTERM can be caught so the program can finish cleanly; SIGKILL cannot be caught.

2. Why does the handler only set an `Event`?

   *Answer:* A handler can run at any moment, so it must do almost nothing; the loop checks the flag at a safe point.

3. What does a lock protect?

   *Answer:* Shared data from being changed by two threads at once.

4. What does exit code 143 mean?

   *Answer:* The process was ended by signal 15 (SIGTERM): 128 plus 15.

5. Why are killed-process tests part of the suite?

   *Answer:* Crash safety can only be shown by actually crashing the program.

## Further reading

- Python `signal`, `subprocess`, `threading` and `concurrent.futures`, https://docs.python.org/3/library/signal.html, https://docs.python.org/3/library/subprocess.html, https://docs.python.org/3/library/threading.html, https://docs.python.org/3/library/concurrent.futures.html (examples run locally on Python 3.13 and macOS).
