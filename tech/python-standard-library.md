# The Python standard library

## What it is

Python ships with a large collection of ready-made modules, called the **standard library**. You use one with `import name`. Because it comes with the interpreter, using it adds no dependency: nothing to install, pin or audit.

## Why this repository uses it

The project keeps outside dependencies to a minimum (see `pyproject-toml.md`: the runtime needs only a few packages). Most of what it needs is in the standard library: reading JSON and CSV, hashing, threads, signals, subprocesses, SQLite, dates, exact decimals. Sticking to the standard library keeps the install small and the behavior stable.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/` | the program |
| `tests/` | tests use `subprocess`, `threading`, `signal`, `socket`, `tempfile` and others |
| `scripts/` | data generators use `random`, `json`, `csv` |

## How it works underneath

Most of the standard library is itself written in Python and lives in a folder next to the interpreter; some parts (`hashlib`, `zlib`, `sqlite3`, `socket`, `_json`) are compiled C code wrapped in a Python interface. `import x` finds the module through `sys.path`, runs it once, and caches it in `sys.modules`.

Modules that talk to the operating system (`os`, `signal`, `subprocess`, `socket`, `threading`, `time`) are thin layers over system calls, so their behavior can differ slightly between macOS, Linux and Windows. Where it matters, this repository's tests check the behavior on the platform they run on.

## Walkthrough of this repository's use

The **standard library** is the large set of modules that come with Python itself, with nothing to install. This repository imports 30 of them. Each one, in alphabetical order, with the names this repository actually uses and one real line:

#### `__future__`

A special module whose imports switch on language behavior early. `annotations` stores type hints as text.

- Imported in 45 file(s).
- What this repository uses from it: `annotations`.

#### `argparse`

Reads the command line (`meter run --budget 0.05`) into named values and prints help and errors. A *sub-command* (`run`, `report`) is added with sub-parsers.

- Imported in 2 file(s).
- What this repository uses from it: `argparse.Namespace`, `argparse.ArgumentParser`.
- Example: `src/scheduling_agent/interfaces/calendar_server.py:22`: `parser = argparse.ArgumentParser(prog="calendar-service", description="The sample calendar service.")`

#### `base64`

Turns bytes into plain letters and digits and back, so binary data can travel in text.

- Imported in 1 file(s).
- What this repository uses from it: `base64.b64encode`, `base64.b64decode`.
- Example: `src/scheduling_agent/infrastructure/embeddings.py:25`: `return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")`

#### `collections`

Extra container types: `Counter` counts items, `defaultdict` makes a missing key start with a default, `deque` is a queue you can add to and remove from at both ends.

- Imported in 29 file(s).
- What this repository uses from it: `defaultdict`.
- Example: `src/scheduling_agent/interfaces/cli.py:116`: `by_task: dict[str, list[TaskResult]] = defaultdict(list)`

#### `collections.abc`

Names for the *kinds* of containers (`Mapping`, `Sequence`, `Iterable`, `Callable`). Used in type hints.

- Imported in 29 file(s).
- What this repository uses from it: `Sequence`, `Callable`, `Mapping`, `Collection`, `Iterator`.
- Example: `src/scheduling_agent/application/agent.py:61`: `new_run_id: Callable[[], str] = lambda: uuid.uuid4().hex[:12],`

#### `contextlib`

Helpers for `with` blocks. `@contextmanager` turns a function with one `yield` into something usable after `with`.

- Imported in 1 file(s).
- What this repository uses from it: `contextmanager`.
- Example: `src/scheduling_agent/infrastructure/sqlite.py:23`: `@contextmanager`

#### `dataclasses`

The `@dataclass` decorator, `field()` for per-field settings and `replace()` for making a changed copy of a frozen object.

- Imported in 15 file(s).
- What this repository uses from it: `dataclass`, `field`, `replace`, `dataclasses.replace`.
- Example: `src/scheduling_agent/application/agent.py:28`: `@dataclass(frozen=True, slots=True)`

#### `datetime`

Dates, times and durations (`date`, `datetime`, `timedelta`, `UTC`).

- Imported in 22 file(s).
- What this repository uses from it: `datetime`, `date`, `datetime.fromisoformat`, `time`, `timedelta`, `datetime.combine`, `UTC`, `datetime.now`, `datetime.min`, `datetime.fromtimestamp`.
- Example: `src/scheduling_agent/application/tools.py:146`: `start = datetime.fromisoformat(str(args["start"])).isoformat(timespec="minutes")`

#### `enum`

Fixed sets of named values; `StrEnum` members are also strings.

- Imported in 5 file(s).
- What this repository uses from it: `StrEnum`.
- Example: `src/scheduling_agent/domain/llm.py:13`: `class Role(StrEnum):`

#### `functools`

Tools for functions, such as caching results and fixing some arguments in advance.

- Imported in 1 file(s).
- What this repository uses from it: `functools.wraps`.
- Example: `src/scheduling_agent/infrastructure/calendar_db.py:44`: `@functools.wraps(method)`

#### `hashlib`

Hash functions. A hash turns any bytes into a short fixed-length fingerprint. `sha256` is used for fingerprints of requests and files.

- Imported in 5 file(s).
- What this repository uses from it: `hashlib.sha256`, `hashlib.md5`.
- Example: `src/scheduling_agent/domain/llm.py:110`: `return hashlib.sha256(canonical.encode("utf-8")).hexdigest()`

#### `io`

In-memory file-like objects such as `StringIO`.

- Imported in 1 file(s).
- What this repository uses from it: `io.StringIO`.

#### `json`

Reads and writes JSON text (`loads` text to Python objects, `dumps` the other way).

- Imported in 18 file(s).
- What this repository uses from it: `json.dumps`, `json.loads`, `json.JSONDecodeError`.
- Example: `src/scheduling_agent/application/tools.py:81`: `return json.dumps(value, sort_keys=True, separators=(",", ":"))`

#### `logging`

Writes log messages with a level, a source name and extra fields.

- Imported in 8 file(s).
- What this repository uses from it: `logging.getLogger`, `logging.Formatter`, `logging.LogRecord`, `logging.StreamHandler`, `logging.getLevelName`, `logging.WARNING`, `logging.INFO`.
- Example: `src/scheduling_agent/application/agent.py:21`: `_log = logging.getLogger(__name__)`

#### `math`

Mathematical functions (square root, rounding up, logarithms).

- Imported in 2 file(s).
- What this repository uses from it: `math.sqrt`, `math.exp`, `math.log`.
- Example: `src/scheduling_agent/domain/memory.py:104`: `recency = math.exp(-math.log(2) * age / half_life_days)`

#### `os`

Operating-system services: environment variables (`os.environ`), file descriptors (`os.fsync`), process ids and more.

- Imported in 7 file(s).
- What this repository uses from it: `os.environ`, `os.kill`, `os.getpid`.
- Example: `src/scheduling_agent/infrastructure/failpoints.py:28`: `os.kill(os.getpid(), signal.SIGKILL)`

#### `pathlib`

File locations as objects (`Path`).

- Imported in 11 file(s).
- What this repository uses from it: `Path`.
- Example: `src/scheduling_agent/infrastructure/calendar_seed.py:11`: `def init_calendar(connection: sqlite3.Connection, sql_dir: Path) -> None:`

#### `random`

Pseudo-random numbers. A `random.Random(seed)` object gives the same sequence every time for the same seed.

- Imported in 4 file(s).
- What this repository uses from it: `random.Random`.
- Example: `src/scheduling_agent/infrastructure/resilient.py:29`: `rng: random.Random | None = None,`

#### `re`

Regular expressions: patterns that search and extract text.

- Imported in 4 file(s).
- What this repository uses from it: `re.compile`, `re.IGNORECASE`, `re.I`, `re.DOTALL`, `re.M`, `re.split`, `re.findall`.
- Example: `src/scheduling_agent/domain/memory.py:15`: `_EARLIEST = re.compile(rf"\b(?:no|nothing|not|never)\b[^.]{{0,30}}?\bbefore\s+{_TIME}", re.IGNORECASE)`

#### `signal`

Receives operating-system signals such as SIGTERM and SIGINT in a Python handler function.

- Imported in 6 file(s).
- What this repository uses from it: `signal.SIGTERM`, `signal.SIGKILL`, `signal.signal`, `signal.SIGINT`, `signal.raise_signal`, `signal.SIG_DFL`, `signal.default_int_handler`.
- Example: `src/scheduling_agent/infrastructure/failpoints.py:28`: `os.kill(os.getpid(), signal.SIGKILL)`

#### `socket`

Low-level network connections. Here it is used for plain network checks, such as asking the system for a free port.

- Imported in 1 file(s).
- What this repository uses from it: `socket.socket`.

#### `sqlite3`

The driver for SQLite, a database stored in one file (see `sqlite.md`).

- Imported in 6 file(s).
- What this repository uses from it: `sqlite3.Connection`, `sqlite3.Row`, `sqlite3.connect`.
- Example: `src/scheduling_agent/infrastructure/agent_db.py:21`: `def _approval(row: sqlite3.Row) -> Approval:`

#### `struct`

Packs and unpacks numbers into raw bytes.

- Imported in 1 file(s).
- What this repository uses from it: `struct.pack`, `struct.unpack`.
- Example: `src/scheduling_agent/infrastructure/embeddings.py:25`: `return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")`

#### `subprocess`

Starts another program from Python and reads its output and exit code.

- Imported in 2 file(s).
- What this repository uses from it: `subprocess.Popen`, `subprocess.PIPE`, `subprocess.run`, `subprocess.CompletedProcess`.
- Example: `src/scheduling_agent/application/agent.py:25`: `"""No saved run with that id."""`

#### `sys`

The interpreter itself: command-line arguments (`sys.argv`), standard streams (`sys.stdout`, `sys.stderr`) and `sys.exit()`.

- Imported in 5 file(s).
- What this repository uses from it: `sys.stderr`, `sys.executable`, `sys.exit`.
- Example: `src/scheduling_agent/infrastructure/logging.py:45`: `handler = logging.StreamHandler(stream or sys.stderr)`

#### `threading`

Threads, locks (`Lock`) and events (`Event`).

- Imported in 7 file(s).
- What this repository uses from it: `threading.Thread`, `threading.RLock`, `threading.Lock`, `threading.Event`.
- Example: `src/scheduling_agent/infrastructure/agent_db.py:43`: `self._lock = threading.RLock()`

#### `time`

Clocks and sleeping: `time.monotonic()` is a clock that never goes backwards, good for measuring durations; `time.sleep()` pauses.

- Imported in 5 file(s).
- What this repository uses from it: `time.fromisoformat`, `time.monotonic`, `time.sleep`.
- Example: `src/scheduling_agent/application/tools.py:85`: `return time.fromisoformat(text) if text else None`

#### `types`

Names for built-in object types; `FrameType` appears in the signature of a signal handler.

- Imported in 1 file(s).
- What this repository uses from it: `FrameType`.
- Example: `src/scheduling_agent/infrastructure/shutdown.py:21`: `def _handle(self, _number: int, _frame: FrameType | None) -> None:`

#### `typing`

Type-hint helpers: `Any`, `Protocol`, `Literal`, `Final`, `Annotated`, `Concatenate`, `TextIO`.

- Imported in 17 file(s).
- What this repository uses from it: `Any`, `Protocol`, `Literal`, `Concatenate`, `TextIO`, `Annotated`.
- Example: `src/scheduling_agent/application/ports.py:17`: `class ChatModel(Protocol):`

#### `uuid`

Universally unique identifiers (long random ids).

- Imported in 2 file(s).
- What this repository uses from it: `uuid.uuid4`.
- Example: `src/scheduling_agent/application/agent.py:61`: `new_run_id: Callable[[], str] = lambda: uuid.uuid4().hex[:12],`

## Try it yourself

1. How many top-level modules this Python's standard library has.

```bash
.venv/bin/python -c "import sys; print(len(sys.stdlib_module_names), 'standard-library modules')"
```

What you should see (captured from this repository):

```text
290 standard-library modules
```

2. `hashlib`: the SHA-256 fingerprint of five bytes. Change one letter and every digit changes.

```bash
.venv/bin/python -c "import hashlib; print(hashlib.sha256(b'hello').hexdigest())"
```

What you should see (captured from this repository):

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

3. `decimal`: exact arithmetic.

```bash
.venv/bin/python -c "from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

What you should see (captured from this repository):

```text
0.3
```

4. `json`: Python object to text and back.

```bash
.venv/bin/python -c "import json; s = json.dumps({'a': [1, 2]}); print(s, json.loads(s)['a'][1])"
```

What you should see (captured from this repository):

```text
{"a": [1, 2]} 2
```

5. `random`: two generators with the same seed give the same numbers.

```bash
.venv/bin/python -c "import random; a = random.Random(7); b = random.Random(7); print(a.random() == b.random())"
```

What you should see (captured from this repository):

```text
True
```

## Mistakes people make

- **Shadowing a module with your own file name.** A file named `json.py` in the project would hide the standard `json`. Module names here avoid the standard names.
- **Using `time.time()` to measure a duration.** The wall clock can jump. Durations use `time.monotonic()`.
- **Using `random` for secrets.** `random` is predictable. Here it only makes test data and jitter; it is not used for security.
- **Reading a whole huge file with `read_text()`.** Fine for these small data files; large files need streaming.
- **Trusting `os.environ` values to be set.** The settings code supplies defaults and checks values.

## Check yourself

1. Why can the project use `json` without adding it to `pyproject.toml`?

   *Answer:* It is part of the standard library, which comes with Python.

2. Which module measures durations safely and why?

   *Answer:* `time.monotonic()`, because it never jumps backwards.

3. What does `hashlib.sha256(data).hexdigest()` return?

   *Answer:* A 64-character hexadecimal fingerprint of the data.

4. What does a `ThreadPoolExecutor` do?

   *Answer:* Runs submitted functions on a fixed pool of worker threads.

5. What is `sys.argv`?

   *Answer:* The list of command-line words the program was started with.

## Further reading

- The Python Standard Library reference, https://docs.python.org/3.13/library/index.html (each module's page lists what it provides; examples above were run on Python 3.13).
