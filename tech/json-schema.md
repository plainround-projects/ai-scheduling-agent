# JSON Schema

## What it is

**JSON Schema** is a standard way to describe the shape of JSON data in JSON itself: which fields exist, their types, limits and patterns, which are required. A program (a *validator*) can check any JSON value against a schema and list what is wrong. Schemas are also how you tell a language model what a tool's arguments or an answer must look like.

The main keywords: `type` (`string`, `integer`, `number`, `boolean`, `array`, `object`, `null`), `properties`, `required`, `enum` (allowed values), `items` (the schema of list elements), `minimum`/`maximum`, `minLength`/`maxLength`, `minItems`/`maxItems`, `pattern` (a regular expression) and `additionalProperties`.

## Why this repository uses it

A model asked for "a JSON answer" may add words, rename a field or invent a value. A schema turns that request into something exact: the model server can constrain the output to it, and the program can verify whatever comes back. For tool calling, the schema is the contract between the model and the tool.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/scheduling_agent/application/tools.py` | the tools the agent may call, each with a JSON Schema for its arguments |

## How it works underneath

A validator walks the data and the schema together. For each location it checks the keywords that apply to the data's type and records a problem for each failure, prefixing it with the path of the location. Validation is *structural*: it can say a number is out of range, but not that an order id exists. That second kind of check is code (see `pydantic.md`).

Schemas are used in two directions: to **constrain generation** (the server only lets the model produce text that fits) and to **validate results** (the program checks after the fact). Constrained generation is not available on every server; validation always is.

## Walkthrough of this repository's use

The agent offers the model a small set of tools. Each tool is described by a name, a description and a JSON Schema for its arguments; the model fills in the arguments and the program validates them before acting:

`src/scheduling_agent/application/tools.py`, lines 25 to 39:

```python
        ToolSpec(
            "find_free_slots",
            "Find start times at which every listed person is free. Weekdays, 09:00 to 17:00, on the half hour.",
            {
                "type": "object",
                "properties": {
                    "people": people,
                    "first_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "last_day": {"type": "string", "description": "YYYY-MM-DD"},
                    "minutes": {"type": "integer", "description": "length, a multiple of 30"},
                    "not_before": {"type": "string", "description": "HH:MM, earliest start"},
                    "not_after": {"type": "string", "description": "HH:MM, latest end"},
                },
                "required": ["people", "first_day", "last_day", "minutes"],
            },
```

- `name` and `description` are what the model reads to decide whether to use the tool.
- `parameters` is the JSON Schema of the arguments: `"type": "object"`, a `properties` mapping (each argument with its own `type`, and limits such as `minimum`/`maximum`, `pattern`, `items`), and `required`.
- The adapters pass the schema to the model API in that API's shape (`input_schema` for Claude, `parameters` inside a `function` for the OpenAI-compatible protocol; see `anthropic-sdk.md` and `ollama.md`).

## Try it yourself

1. A tiny schema: an object with a required integer `n` of at least 1 and no other fields.

```bash
.venv/bin/python -c "import json; print(json.dumps({'type': 'object', 'properties': {'n': {'type': 'integer', 'minimum': 1}}, 'required': ['n'], 'additionalProperties': False}))"
```

What you should see (captured from this repository):

```text
{"type": "object", "properties": {"n": {"type": "integer", "minimum": 1}}, "required": ["n"], "additionalProperties": false}
```

## Mistakes people make

- **Treating the schema as the only check.** It cannot express rules between fields or facts about the world; code adds those.
- **Leaving `additionalProperties` open.** A model may add fields. The schemas here close the object.
- **Expecting every model server to enforce it.** Some ignore the schema; the program validates results anyway.
- **Writing the same shape twice.** Generate the schema from one source (the pydantic model) or keep it in the single tool definition file.

## Check yourself

1. What does `required` list?

   *Answer:* The properties that must be present.

2. What does `additionalProperties: false` do?

   *Answer:* Forbids any property not listed under `properties`.

3. What is the difference between constraining and validating?

   *Answer:* Constraining limits what the model can write; validating checks what it wrote.

4. What does `enum` do?

   *Answer:* Limits a value to a listed set.

5. Can a schema say that an order id exists?

   *Answer:* No; that needs code that looks at data.

## Further reading

- JSON Schema, https://json-schema.org/understanding-json-schema/ (Draft 2020-12; the project checks and uses only the keywords listed above).
