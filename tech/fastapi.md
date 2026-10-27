# FastAPI

## What it is

A **web service** is a program that waits for HTTP requests (see `curl-and-http.md`) and answers them. A **web framework** handles the routine parts: reading the request, choosing which function to call from the method and path, checking the data, turning the return value into JSON, and sending the right status code. **FastAPI** is a Python web framework in which you write ordinary functions with type hints and the framework does the rest. The same hints also make FastAPI generate an **OpenAPI** document: a machine-readable description of every route that tools and people can read.

## Why this repository uses it

The agents and the orchestrator drive *services* (a calendar, orders, a help center, an email extractor behind a migration flag). Real HTTP services let the tests exercise real network behavior: retries, status codes, idempotency keys, version conflicts, two processes racing on one order. FastAPI keeps each service small: the route functions are thin, the rules live in the domain code, and request bodies are checked by pydantic before any rule runs.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/interfaces/calendar_api.py` | routes and the factory that builds the app |
| `pyproject.toml` | `fastapi==0.162.0` |
| `requirements.lock` | `starlette` (the toolkit FastAPI is built on), `pydantic`, `annotated-doc`, `typing-inspection` |

## How it works underneath

**ASGI.** Python web frameworks and web servers talk through a standard interface called ASGI (Asynchronous Server Gateway Interface). The server (uvicorn, see `uvicorn.md`) accepts connections and parses HTTP; it then calls the application object with a description of the request, and the application calls back with the response. FastAPI is built on **Starlette**, a small ASGI toolkit that provides routing, request and response objects.

**From a function to a route.** When the app starts, FastAPI reads each decorated function's signature. Parameters named in the path become path parameters; those with a pydantic model type become the body; the rest become query parameters, unless marked `Header(...)`. It builds a validator from the hints, so every request is checked before your code runs.

**Sync and async handlers.** A plain `def` handler is run in a thread pool so it does not block the server; an `async def` handler runs on the event loop. All routes here use plain functions that call blocking code (SQLite), except small lifespan and error handlers.

**OpenAPI and docs.** `app.openapi()` returns the generated description (paths, parameters, schemas). A running app also serves it at `/openapi.json` and shows interactive pages at `/docs`.

**Status codes used here.** 200 OK, 201 Created, 404 not found, 409 conflict (already exists, slot taken, wrong version), 422 invalid body, 429 too many requests.

## Walkthrough of this repository's use

### The routes

Each row is one *path operation*: a function that runs when a request with that method and path arrives. (Read from the decorators in the code.)

| Method | Path | Function | Where |
| --- | --- | --- | --- |
| GET | `/health` | `health` | `src/scheduling_agent/interfaces/calendar_api.py:64` |
| GET | `/people` | `people` | `src/scheduling_agent/interfaces/calendar_api.py:68` |
| GET | `/free-slots` | `free_slots` | `src/scheduling_agent/interfaces/calendar_api.py:72` |
| GET | `/events` | `events` | `src/scheduling_agent/interfaces/calendar_api.py:87` |
| GET | `/events/{event_id}` | `get_event` | `src/scheduling_agent/interfaces/calendar_api.py:91` |
| POST | `/events` | `book` | `src/scheduling_agent/interfaces/calendar_api.py:98` |
| POST | `/events/{event_id}/cancel` | `cancel` | `src/scheduling_agent/interfaces/calendar_api.py:110` |
| POST | `/admin/reset` | `admin_reset` | `src/scheduling_agent/interfaces/calendar_api.py:121` |

A route written inside an `if` (the `POST /admin/reset` route) exists only when that condition holds: the reset endpoint is created only when an environment variable switches it on (`CALENDAR_ALLOW_RESET` or `ALLOW_RESET`), so `create_app` with no reset function does not list it.

### Building the app: `create_app`

`src/scheduling_agent/interfaces/calendar_api.py`, lines 56 to 57:

```python
def create_app(calendar: SqliteCalendar, reset: Callable[[], None] | None = None) -> FastAPI:
    """Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data."""
```

The factory is the function that builds the `FastAPI` object. It takes its collaborators (`calendar`, `reset`) as parameters instead of creating them, so tests can pass fakes and the process wiring happens in one place. `FastAPI(title=..., version=...)` creates the application object; the title and version appear in the automatically generated API description.

### One real handler

`src/scheduling_agent/interfaces/calendar_api.py`, lines 98 to 108:

```python
    @app.post("/events", status_code=201)
    def book(
        body: BookRequest, response: Response, idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]
    ) -> dict[str, Any]:
        try:
            result = calendar.book(body.people, body.start, body.minutes, idempotency_key)
        except CalendarError as error:
            raise fail(error) from error
        response.status_code = 200 if result.replayed else 201
        _log.info("booked", extra={"fields": {"event_id": result.event.id, "replayed": result.replayed}})
        return {"event": event_json(result.event), "replayed": result.replayed}
```

### How to read the constructs this service uses

- **A route** is a function with a decorator such as `@app.get("/health")`. The decorator names the HTTP method and the path; the function runs when such a request arrives. In this repository: `src/scheduling_agent/interfaces/calendar_api.py`, lines 64 to 65:

```python
    @app.get("/health")
    def health() -> dict[str, object]:
```

- **Path parameters.** A name in braces in the path (such as `{id}`) arrives as a function parameter of the same name. `src/scheduling_agent/interfaces/calendar_api.py`, lines 91 to 94:

```python
    @app.get("/events/{event_id}")
    def get_event(event_id: str) -> dict[str, Any]:
        try:
            return event_json(calendar.get_event(event_id))
```

- **Query parameters** are the `?name=value` part of an address. A function parameter that is not in the path becomes one, and `Query(...)` adds rules such as `ge` (greater or equal) and `le`. `src/scheduling_agent/interfaces/calendar_api.py`, lines 73 to 75:

```python
    def free_slots(
        people: Annotated[list[str], Query(min_length=1)],
        first_day: date,
```

- **A body.** A parameter typed with a pydantic model (see `pydantic.md`) is filled from the JSON body of the request and validated; an invalid body is answered with status **422** and a list of what is wrong, before the function runs. `src/scheduling_agent/interfaces/calendar_api.py`, lines 100 to 101:

```python
        body: BookRequest, response: Response, idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]
    ) -> dict[str, Any]:
```

- **Headers.** `Header(...)` reads a request header; FastAPI turns `idempotency_key` into the header name `Idempotency-Key`. `src/scheduling_agent/interfaces/calendar_api.py`, lines 99 to 101:

```python
    def book(
        body: BookRequest, response: Response, idempotency_key: Annotated[str, Header(min_length=8, max_length=128)]
    ) -> dict[str, Any]:
```

- **Errors.** The code raises `HTTPException(status_code, detail=...)`; FastAPI sends that status with a JSON body. `src/scheduling_agent/interfaces/calendar_api.py`, lines 61 to 64:

```python
        status = _STATUS.get(type(error), 400)
        return HTTPException(status_code=status, detail={"error": type(error).__name__, "message": str(error)})

    @app.get("/health")
```

- **A success status other than 200.** `status_code=201` means "Created". `src/scheduling_agent/interfaces/calendar_api.py`, lines 98 to 99:

```python
    @app.post("/events", status_code=201)
    def book(
```

- **The return value.** Whatever the function returns (a dictionary, a list, a model) is converted to JSON.

## Try it yourself

1. The installed FastAPI.

```bash
.venv/bin/python -c "import fastapi; print(fastapi.__version__)"
```

What you should see (captured from this repository):

```text
0.162.0
```

2. Build the app with placeholder collaborators (nothing is started, no port opened) and list every route FastAPI found. This is the route table above, produced by the framework itself.

```bash
.venv/bin/python -c "from scheduling_agent.interfaces.calendar_api import create_app; import json; print('\n'.join(sorted(f'{m.upper()} {p}' for p, ms in create_app(None).openapi()['paths'].items() for m in ms)))"
```

What you should see (captured from this repository):

```text
GET /events
GET /events/{event_id}
GET /free-slots
GET /health
GET /people
POST /events
POST /events/{event_id}/cancel
```

3. How many places set a status code explicitly.

```bash
grep -rn 'status_code=' src | wc -l | tr -d ' '
```

What you should see (captured from this repository):

```text
2
```

4. Where routes raise HTTP errors.

```bash
grep -rn 'HTTPException' src | head -3
```

What you should see (captured from this repository):

```text
src/scheduling_agent/interfaces/calendar_api.py:10:from fastapi import FastAPI, Header, HTTPException, Query, Response
src/scheduling_agent/interfaces/calendar_api.py:60:    def fail(error: CalendarError) -> HTTPException:
src/scheduling_agent/interfaces/calendar_api.py:62:        return HTTPException(status_code=status, detail={"error": type(error).__name__, "message": str(error)})
```

## Mistakes people make

- **Doing business rules in the route function.** The routes stay thin; rules live in the domain and application code.
- **Returning raw exceptions.** Domain errors are mapped to precise statuses in one table.
- **Binding to 127.0.0.1 in a container.** Inside Docker the service listens on `0.0.0.0` (`HTTP_HOST`).
- **Leaving an admin endpoint on.** `POST /admin/reset` exists only when an environment variable enables it (`CALENDAR_ALLOW_RESET`, `ALLOW_RESET`).
- **Skipping idempotency on writes.** A retried POST must not repeat its effect; writes take an `Idempotency-Key` header.
- **Blocking the event loop.** Blocking calls are in plain `def` handlers, which FastAPI runs in a thread pool.

## Check yourself

1. What does a type hint on a handler parameter do?

   *Answer:* It tells FastAPI where to get the value (path, query, header or body) and how to validate it.

2. What status does FastAPI send for an invalid body?

   *Answer:* 422.

3. What is OpenAPI?

   *Answer:* A standard machine-readable description of an HTTP API's routes and data.

4. What is ASGI?

   *Answer:* The interface between a Python web server and a web application.

5. Why is the app built by a factory function?

   *Answer:* So collaborators are passed in and tests can supply fakes.

## Further reading

- FastAPI documentation, https://fastapi.tiangolo.com/ and Starlette, https://www.starlette.io/ (FastAPI 0.162.0 is pinned; the route table was read from the code and cross-checked with `app.openapi()`).
