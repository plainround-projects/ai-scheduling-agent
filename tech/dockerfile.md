# Dockerfile syntax

## What it is

A **Dockerfile** is a recipe for building a **Docker image**: a read-only package that holds a minimal operating system, your program and everything it needs. Each line is an **instruction** (`FROM`, `COPY`, `RUN`, ...). Docker runs them top to bottom; each instruction that changes files makes a **layer**, a saved snapshot of the changes. Layers are cached: if an instruction and everything above it are unchanged, Docker reuses the saved layer instead of running it again.

## Why this repository uses it

The service repositories ship a Dockerfile so the same service runs anywhere with Docker, without the person having to install Python or the packages. It is written for repeatability: a pinned base image, a hash-checked install from the lock file, an unprivileged user and a health check.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | the image definition |
| `.dockerignore` | what to leave out of the build context |
| `docker-compose.yml` | `build: .` builds this Dockerfile |
| `requirements.lock` | installed inside the image |

## How it works underneath

**Layers and cache.** Each `RUN`, `COPY` and `ADD` creates a layer. Docker computes a key for each layer from the instruction and, for `COPY`, a hash of the copied files. If the key is unchanged since the last build, the layer is taken from the cache. The first changed layer, and every layer after it, is rebuilt. That is why the Dockerfile copies `requirements.lock` and installs packages *before* copying the source: editing a source file then only rebuilds the last layers.

**Image and container.** An image is the package; a **container** is a running copy of an image, with its own process, file system and network. `docker run IMAGE` creates and starts one.

**`CMD` and `ENTRYPOINT`.** `CMD` is the default command of the container. In the JSON-list form it runs without a shell.

**Shell form and list form.** `RUN pip install x` runs the text in a shell. `CMD ["a", "b"]` passes the words directly.

**User.** The container starts as `root` unless `USER` says otherwise.

**Health.** `HEALTHCHECK` makes Docker run a command periodically and record healthy or unhealthy; `docker compose up --wait` waits for healthy.

## Walkthrough of this repository's use

`Dockerfile`, the whole file, block by block. Under each block, every line is explained.

```dockerfile
# The sample calendar service as an image: HTTP over SQLite. The agent itself is a command-line program and runs
# from the host's virtual environment (or `docker run ... agent ...` against this service).
FROM python:3.12.8-slim-bookworm
```

- `# The sample calendar service as an image: HTTP over SQLite. The agent itself is a command-line program and runs`: A comment.
- `` # from the host's virtual environment (or `docker run ... agent ...` against this service). ``: A comment.
- `FROM python:3.12.8-slim-bookworm`: Every image starts `FROM` another image. This one is the official Python image, pinned to the exact version 3.12.8 (`slim` is a smaller variant; `bookworm` is the Debian release it is built on). Pinning an exact tag means a rebuild next month starts from the same Python.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

- `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1`: `ENV` sets environment variables for the build and for the running container: `PYTHONDONTWRITEBYTECODE=1`: stops Python from writing `.pyc` cache files, which are useless inside an image; `PYTHONUNBUFFERED=1`: sends Python's printed output straight out instead of holding it in a buffer, so `docker logs` shows lines at once; `PIP_NO_CACHE_DIR=1`: tells pip not to keep downloaded files, which keeps the image smaller; `PIP_DISABLE_PIP_VERSION_CHECK=1`: stops pip from checking the internet for a newer pip.

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
```

- `WORKDIR /app`: Sets the working folder for the following instructions and for the running program (`/app` is created if missing).
- `COPY requirements.lock ./`: Copies the lock file from the build context (the project folder) into the image's working folder. Only this file is copied first, on purpose: Docker builds an image in **layers**, one per instruction, and re-uses a layer when nothing it depends on has changed. The packages change rarely, so the slow install below stays cached while the code changes.
- `RUN pip install --require-hashes -r requirements.lock`: Runs a command while building. It installs the locked packages, checking every file's hash (see `pip-and-venv.md`). Inside an image there is no virtual environment: the image itself is the isolated environment.

```dockerfile
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY sql ./sql
```

- `COPY pyproject.toml README.md ./`: Copies the project description (the build backend reads `README.md` as the long description).
- `COPY src ./src`: Copies the source code. This layer changes with every code change, which is why it comes after the install layer.
- `RUN pip install --no-deps .`: Installs the project itself (not editable this time: the code is copied into the image's Python). `--no-deps` because the lock already installed the dependencies. This also creates the command-line program (for example `cited`) in the image.
- `COPY sql ./sql`: Copies a folder of files the program reads at run time.

```dockerfile
RUN useradd --system --uid 10001 --home-dir /data app && mkdir /data && chown app /data
USER app
ENV CALENDAR_DB=/data/calendar.db SQL_DIR=/app/sql HTTP_HOST=0.0.0.0 HTTP_PORT=8090
```

- `RUN useradd --system --uid 10001 --home-dir /data app && mkdir /data && chown app /data`: Creates the unprivileged user `app` with `/data` as its home, creates that folder, and gives `app` ownership of it, so the program can write its database there. `&&` runs the next command only if the previous one worked.
- `USER app`: Every following instruction, and the running container, runs as `app` instead of `root`.
- `ENV CALENDAR_DB=/data/calendar.db SQL_DIR=/app/sql HTTP_HOST=0.0.0.0 HTTP_PORT=8090`: `ENV` sets environment variables for the build and for the running container: `CALENDAR_DB=/data/calendar.db`: the path of the SQLite file holding the calendar; `SQL_DIR=/app/sql`: where the SQL files are inside the image; `HTTP_HOST=0.0.0.0`: the network address the HTTP server listens on (`127.0.0.1` means this computer only); `HTTP_PORT=8090`: the port number the HTTP server listens on.

```dockerfile
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)"
CMD ["calendar-service", "serve"]
```

- `EXPOSE 8090`: Documents that the program listens on port 8090 inside the container. `EXPOSE` does not open the port; `docker run -p` or the compose `ports:` key does.
- `HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)"`: Tells Docker how to ask "is this container healthy?". Every 15s Docker runs the command; a run that takes more than 5s counts as a failure; after 3 failures in a row the container is marked unhealthy. The command is a tiny Python program: it opens `http://127.0.0.1:PORT/health` with `urllib.request` (standard library only, so no `curl` is needed in the image) and exits 0 if the status is 200 and 1 otherwise.
- `CMD ["calendar-service", "serve"]`: The command the container runs when it starts: `calendar-service serve`. The list form (JSON array) runs the program directly, with no shell in between, so signals such as SIGTERM from `docker stop` reach the program.

### `.dockerignore`

Before a build, Docker sends the project folder (the *build context*) to the engine. `.dockerignore` lists what to leave out, like `.gitignore` does for git, so the context stays small and secrets do not end up in an image.

`.dockerignore`, the whole file, block by block. Under each block, every line is explained.

```text
.git
.venv
out
tests
docs
**/__pycache__
.mypy_cache
.ruff_cache
.pytest_cache
.coverage
.env
```

- `.git`: Leave out the git history.
- `.venv`: Leave out the virtual environment (the image builds its own packages).
- `out`: Leave out run output.
- `tests`: Leave out the tests (the drill's Dockerfile copies the recordings explicitly).
- `docs`: Leave out the documents.
- `**/__pycache__`: Leave out Python cache folders at any depth.
- `.mypy_cache`: Leave out a tool cache folder.
- `.ruff_cache`: Leave out a tool cache folder.
- `.pytest_cache`: Leave out a tool cache folder.
- `.coverage`: Leave out the coverage data file.
- `.env`: Leave out the private settings file, which may hold a key.

## Try it yourself

1. The installed Docker client.

```bash
docker --version
```

What you should see (captured from this repository):

```text
Docker version 24.0.6, build ed223bc
```

2. How many instruction lines the Dockerfile has.

```bash
grep -c '^[A-Z]' Dockerfile
```

What you should see (captured from this repository):

```text
15
```

3. Build the image. Not run in this session: the machine's Docker engine had no free disk space. Expect one `RUN pip install` layer to take the longest on the first build and to be cached afterwards.

```bash
docker build -t ai-scheduling-agent .
```

4. Run the image and publish its port. Not run here.

```bash
docker run --rm -p 8080:8080 ai-scheduling-agent
```

5. Show that the program runs as user id 10001, not root. Not run here.

```bash
docker run --rm ai-scheduling-agent id -u
```

## Mistakes people make

- **Copying the source before installing packages.** Every code change would reinstall everything. The lock file is copied and installed first.
- **Running as root.** `USER app` limits what a compromised program can do.
- **`latest` as the base image.** The base is pinned to `3.12.8-slim-bookworm`.
- **Putting secrets in the image.** An image can be inspected. Keys come from the environment at run time (the file comment says so).
- **A health check that needs tools the image lacks.** The check uses Python's `urllib`, not `curl`.
- **Shell-form `CMD`.** The program would not receive SIGTERM directly. The list form avoids that.

## Check yourself

1. What is a layer?

   *Answer:* A saved snapshot of the changes made by one instruction, reused from cache if nothing it depends on changed.

2. Why is `requirements.lock` copied before `src`?

   *Answer:* So the slow package install stays cached when only code changes.

3. What does `USER app` do?

   *Answer:* Runs later instructions and the container as the unprivileged user `app`.

4. Does `EXPOSE 8080` publish the port?

   *Answer:* No; it only documents it. Publishing is done with `-p` or the compose `ports:` key.

5. Why does the health check use Python and not curl?

   *Answer:* Because the slim image has no curl and Python is already there.

## Further reading

- Dockerfile reference, https://docs.docker.com/reference/dockerfile/ and build best practices, https://docs.docker.com/build/building/best-practices/ (the image was not built in this session: the machine's Docker engine had no free disk; instruction semantics are from the reference).
