# uvicorn

## What it is

A web framework such as FastAPI only knows how to *answer* a request. Something must listen on a network port, accept connections, read the bytes of each HTTP request, hand them to the framework and write the answer back. That program is a **web server**. **uvicorn** is a fast server for ASGI applications (see `fastapi.md`). You call `uvicorn.run(app, host=..., port=...)` and it keeps running, serving requests, until it is told to stop.

## Why this repository uses it

Every service in the family (calendar, platform services, cited answers, the email extractor) ends in one `uvicorn.run(...)` call inside a small command-line wrapper. uvicorn is a good fit because it handles the shutdown signal gracefully: on SIGTERM it stops accepting new connections and lets the requests already in progress finish, which the Makefile and the tests rely on.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/interfaces/calendar_server.py` | `uvicorn.run(...)` |
| `Makefile` | starts the services in the background with `nohup`, stops them with `kill` (SIGTERM) |
| `pyproject.toml` | `uvicorn==0.54.0` |
| `requirements.lock` | `uvicorn`, `h11`, `click` (its command-line helper) |

## How it works underneath

**The loop.** uvicorn opens a *socket* on the host and port, then uses an *event loop* (asyncio) to wait for many connections at once without a thread for each. When bytes arrive it parses them with an HTTP implementation (`h11`), builds an ASGI request description, awaits the application, and writes the response.

**Graceful shutdown.** On SIGTERM or SIGINT (Ctrl-C) uvicorn closes the listening socket, waits for in-flight requests to finish (up to `timeout_graceful_shutdown` seconds), and then exits. Any request that arrives after the socket closes is refused by the operating system.

**Host and port.** `127.0.0.1` accepts connections from this computer only; `0.0.0.0` accepts from any network interface (needed inside a container so the published port can reach it).

**Logging.** uvicorn configures its own logging unless told otherwise.

## Walkthrough of this repository's use

The call, as it appears in `src/scheduling_agent/interfaces/calendar_server.py`:

`src/scheduling_agent/interfaces/calendar_server.py`, lines 35 to 40:

```python
        return 0
    reset = (lambda: reset_calendar(connection, settings.sql_dir)) if settings.allow_reset else None
    app = create_app(SqliteCalendar(connection), reset)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None, timeout_graceful_shutdown=10)
    connection.close()
    return 0
```

- `uvicorn.run(app, ...)`: start the server and block (do not return) until it stops. `app` is the FastAPI object.
- `host=settings.host`, `port=settings.port`: where to listen; both come from `HTTP_HOST` and `HTTP_PORT` (see `environment-variables.md`).
- `log_config=None`: do not install uvicorn's own logging setup. The program already called `configure_logging(...)` (see `python-logging.md`), so uvicorn's records go through the project's logfmt formatter, giving one consistent log format.
- `timeout_graceful_shutdown=10`: after a stop signal, wait up to 10 seconds for running requests before giving up.

Around it, the wrapper reads the settings (exiting with code 2 on a bad setting), configures logging, builds the app and then calls `uvicorn.run`. When `uvicorn.run` returns, the wrapper closes its resources (a database connection) and returns exit code 0.

How the Makefile uses it (see `make.md`): `nohup <program> serve > out/NAME.log 2>&1 &` starts the process in the background and `echo $$! > out/NAME.pid` saves its process id; `kill $(cat out/NAME.pid)` sends SIGTERM, which triggers the graceful shutdown. The tests start the same program as a real subprocess and send it SIGTERM and SIGKILL to check both outcomes.

## Try it yourself

1. The installed uvicorn.

```bash
.venv/bin/python -c "import uvicorn; print(uvicorn.__version__)"
```

What you should see (captured from this repository):

```text
0.54.0
```

2. uvicorn also ships a command-line program; this repository calls `uvicorn.run` from Python instead.

```bash
.venv/bin/uvicorn --help | sed -n 1,12p
```

What you should see (captured from this repository):

```text
Usage: uvicorn [OPTIONS] APP

Options:
  --host TEXT                     Bind socket to this host.  [default:
                                  127.0.0.1]
  --port INTEGER                  Bind socket to this port. If 0, an available
                                  port will be picked.  [default: 8000]
  --uds TEXT                      Bind to a UNIX domain socket.
  --fd INTEGER                    Bind to socket from this file descriptor.
  --reload                        Enable auto-reload.
  --reload-dir PATH               Set reload directories explicitly, instead
                                  of using the current working directory.
```

3. The four parameters used here exist in the installed uvicorn.

```bash
.venv/bin/python -c "import inspect, uvicorn; s = inspect.signature(uvicorn.run).parameters; print([k for k in s if k in ('host', 'port', 'log_config', 'timeout_graceful_shutdown')])"
```

What you should see (captured from this repository):

```text
['host', 'port', 'log_config', 'timeout_graceful_shutdown']
```

## Mistakes people make

- **Listening on `0.0.0.0` on a laptop for no reason.** Locally the default is `127.0.0.1`; only the container setting is `0.0.0.0`.
- **Killing with `kill -9` and calling it graceful.** SIGKILL cannot be caught; only SIGTERM lets requests finish. The Makefile uses plain `kill`.
- **Two log formats.** `log_config=None` hands logging to the project's formatter.
- **Starting twice on one port.** The second process fails with "address already in use"; the Makefile checks the pid file first.

## Check yourself

1. What does a web server do that a web framework does not?

   *Answer:* Listens on a port, accepts connections and parses HTTP, then hands requests to the framework.

2. What happens on SIGTERM?

   *Answer:* uvicorn stops accepting connections, lets in-flight requests finish, then exits.

3. What does `log_config=None` change?

   *Answer:* uvicorn does not install its own logging; the project's logfmt formatter is used.

4. Why `0.0.0.0` in a container?

   *Answer:* So the published port can reach the service from outside the container.

5. What can SIGKILL not do?

   *Answer:* Be caught: the process is removed immediately, with no cleanup.

## Further reading

- uvicorn documentation, https://www.uvicorn.org/ (uvicorn 0.54.0 is pinned; signature checked locally).
