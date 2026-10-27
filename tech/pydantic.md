# pydantic

## What it is

Data that arrives from outside (a JSON request, a model's answer, a file) cannot be trusted to have the right shape. **Validation** is checking it before using it: is every required field there, is each one the right type, is the number in range, is the text in the right form? **pydantic** is a Python library for this. You describe the shape once as a class with type hints; pydantic checks data against it and gives you either a clean object or a precise list of errors.

It also produces a **JSON Schema** from the class: a standard, machine-readable description of the shape that other tools (a web framework, a model API) understand.

## Why this repository uses it

Two places in the family of repositories receive data they must not trust: HTTP services receive request bodies from clients, and the extraction pipeline receives text from a language model that sometimes writes wrong or invented values. pydantic gives both the same tool: a declared shape, strict checks and error messages that name the field.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/interfaces/calendar_api.py` | model class `BookRequest` |
| `pyproject.toml` | `pydantic==2.14.1` is a runtime dependency |
| `requirements.lock` | `pydantic-core` (the Rust engine that does the work), `annotated-types`, `typing-inspection`, `typing-extensions` |

## How it works underneath

**Fast validation core.** pydantic v2 is split in two: the Python layer reads your class and its type hints and builds a *schema* of rules; `pydantic-core`, written in Rust, runs those rules on incoming data, which is why validation is fast.

**Two modes.** In the default *lax* mode pydantic converts compatible values (`"5"` to `5`). In *strict* mode it accepts only the exact type. Strictness is chosen per model with `ConfigDict(strict=True)`.

**Errors.** `ValidationError.errors()` returns a list of dictionaries (`loc`, `type`, `msg`, `input`). It collects all the problems, not just the first.

**Constraints.** `Field(...)` arguments (`ge`, `le`, `min_length`, `max_length`, `pattern`) are checked by the core. Custom rules go in `@field_validator`.

**JSON Schema.** `Model.model_json_schema()` turns the class into a dictionary describing `type`, `properties`, `required` and the constraints.

## Walkthrough of this repository's use

This repository uses pydantic for the **request and response bodies of its HTTP service** (see `fastapi.md`). The models: `BookRequest`.

`src/scheduling_agent/interfaces/calendar_api.py`, lines 36 to 42:

```python
class BookRequest(BaseModel):
    """The body of POST /events."""

    model_config = ConfigDict(extra="forbid")
    people: Annotated[list[str], Field(min_length=1, max_length=8)]
    start: datetime
    minutes: Annotated[int, Field(ge=1, le=1440)]
```

The fields of each model, read from the code:

`BookRequest` in `src/scheduling_agent/interfaces/calendar_api.py`:

| Field | Type | Required? | `Field(...)` rules |
| --- | --- | --- | --- |
| `people` | `Annotated[list[str], Field(min_length=1, max_length=8)]` | required |  |
| `start` | `datetime` | required |  |
| `minutes` | `Annotated[int, Field(ge=1, le=1440)]` | required |  |

How to read them:

- `class X(BaseModel)`: a class that inherits from pydantic's `BaseModel` becomes a validated data model. Its annotated names are its fields; the HTTP framework builds one from the JSON body of a request and rejects the request with status 422 when a field is wrong.
- A field with no default is **required**; one with a default is optional.
- A type such as `str | None` allows null; `list[str]` is a list of text; `int` a whole number; `bool` true or false.
- `model_config = ConfigDict(extra="forbid")` rejects any field the model does not list, so a typo such as `percnt` is an error instead of being silently ignored.
- `Annotated[T, Field(...)]` means "a `T` that also satisfies these constraints". Constraint names: `min_length` and `max_length` (size of text or list), `ge` and `le` (greater or equal, less or equal), `pattern` (a regular expression). Real example: `src/scheduling_agent/interfaces/calendar_api.py`, line 40:

```python
    people: Annotated[list[str], Field(min_length=1, max_length=8)]
```
- A field typed `datetime` accepts a text such as `"2026-11-03T10:00"` from the JSON body and turns it into a real `datetime` object (conversion happens because the model is not in strict mode).

The service function that takes a model as a parameter (for example `body: SomeModel`) receives a fully checked instance, so the code inside never sees an invalid body.

## Try it yourself

1. The fields of `BookRequest` as pydantic reports them in its JSON Schema.

```bash
.venv/bin/python -c "from scheduling_agent.interfaces.calendar_api import BookRequest; print(sorted(BookRequest.model_json_schema()['properties']))"
```

What you should see (captured from this repository):

```text
['minutes', 'people', 'start']
```

2. Validate an empty body against `BookRequest`: each missing required field is reported.

```bash
.venv/bin/python - <<'EOF'
from scheduling_agent.interfaces.calendar_api import BookRequest
try:
    BookRequest.model_validate({})
except Exception as error:
    for line in str(error).split("\n")[:5]:
        print(line)
EOF
```

What you should see (captured from this repository):

```text
3 validation errors for BookRequest
people
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/missing
start
```

3. Each problem as a (location, kind) pair. Besides the missing required fields you see `extra_forbidden` for the unlisted field `surprise`, which is what `extra="forbid"` produces.

```bash
.venv/bin/python - <<'EOF'
from scheduling_agent.interfaces.calendar_api import BookRequest
try:
    BookRequest.model_validate({"surprise": 1})
except Exception as error:
    print([(e["loc"], e["type"]) for e in error.errors()])
EOF
```

What you should see (captured from this repository):

```text
[(('people',), 'missing'), (('start',), 'missing'), (('minutes',), 'missing'), (('surprise',), 'extra_forbidden')]
```

4. The installed pydantic.

```bash
.venv/bin/python -c "import pydantic; print(pydantic.VERSION)"
```

What you should see (captured from this repository):

```text
2.14.1
```

## Mistakes people make

- **Trusting data because it came from a model.** Models write wrong values with confidence. The extraction pipeline validates everything and measures how often it fails.
- **Lax conversion hiding a bug.** Strict mode refuses `'5'` for a number; the HTTP models use `extra="forbid"` so typos fail loudly.
- **Validating only the shape.** A schema cannot say "this order id must appear in the email". Meaning checks are separate code.
- **Stopping at the first error.** Collect them all; the repair prompt needs the full list.
- **Duplicating the shape in a prompt, a schema file and a validator.** One class produces the schema and the validation.

## Check yourself

1. What does `extra="forbid"` do?

   *Answer:* Rejects any field that the model does not list.

2. What is the difference between lax and strict mode?

   *Answer:* Lax converts compatible values (`"5"` to `5`); strict accepts only the exact type.

3. What does `Field(ge=0)` mean?

   *Answer:* The value must be greater than or equal to 0.

4. What does `model_json_schema()` return?

   *Answer:* A dictionary in JSON Schema form describing the model.

5. Why is the validator not the schema alone?

   *Answer:* Some rules need code (counting words, comparing with the email).

## Further reading

- pydantic documentation, https://docs.pydantic.dev/latest/ (pydantic 2.14.1 is pinned; the commands above were run locally).
