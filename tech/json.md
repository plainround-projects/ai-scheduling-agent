# JSON

## What it is

**JSON** (JavaScript Object Notation) is a text format for data. It has six kinds of value: **text** in double quotes (`"hello"`), **numbers** (`3`, `0.5`), **true** and **false**, **null** (nothing), **arrays** (ordered lists in square brackets, `[1, 2, 3]`) and **objects** (collections of `"name": value` pairs in curly braces, `{"id": "p01", "kind": "short"}`). Values nest freely. There are no comments and no trailing commas.

Almost every programming language can read and write JSON, which makes it the common way for programs to exchange data: web services speak it, model APIs speak it, and so do the data files in this repository.

## Why this repository uses it

The repository's data (prices, thresholds, decision rules, tool definitions, reports) must be readable by people, comparable in version control and loadable without extra libraries. JSON meets all three: Python's standard library reads it, a diff shows exactly which number changed, and the same format is used on the wire to the model servers. Money amounts are written as **text** (`"0.0001"`) rather than numbers so they are read as exact decimals, not binary floating-point approximations.

## Where it appears

| File | What it does with this technology |
| --- | --- |

## How it works underneath

A JSON parser reads the characters from left to right and builds objects in memory: an object becomes a dictionary, an array a list, text a string. Python's `json.loads(text)` does this and `json.dumps(obj)` writes it back. Rules that surprise people: keys are always text; the order of keys is kept by Python but carries no meaning in the format; a number has no size or type (the reader decides; `1` and `1.0` are both numbers); and strings are Unicode, with `\n` and `\"` as escapes for a newline and a quote.

`sort_keys` and a fixed indent produce *canonical* output: the same data always gives the same bytes. The repository writes its reports that way so that a rerun gives an identical file, and a change in the file means a change in the data.

## Walkthrough of this repository's use

This repository has no `.json` file of its own: its data files are JSON Lines (see `jsonl.md`), whose every line is one JSON object, and its services speak JSON in HTTP requests and answers. One record, key by key:

`data/tasks.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "id": "t-book-01",
  "kind": "book",
  "text": "Book a 30-minute meeting with alice and bob on 2026-11-03.",
  "facts": [
    [
      "alice",
      "I never want meetings before 10"
    ]
  ],
  "add": [
    {
      "people": [
        "alice",
        "bob"
      ],
      "start": "2026-11-03T10:00",
      "minutes": 30
    }
  ],
  "remove": []
}
```

What each key means:

- `id` (text): a short unique id for this record.
- `kind` (text): which group the record belongs to.
- `text` (text): the text of the record.
- `facts` (list): facts to store in the agent's memory before the task, as pairs of person and sentence.
- `add` (list): the events that must exist in the calendar after the task.
- `add[].people` (list): the people in the meeting.
- `add[].start` (text): start time as `YYYY-MM-DDTHH:MM`.
- `add[].minutes` (whole number): length in minutes.
- `remove` (list): the events that must no longer exist.

## Try it yourself

1. Python data to JSON text: `None` becomes `null`, `True` becomes `true`, keys are sorted.

```bash
.venv/bin/python -c "import json; print(json.dumps({'b': 1, 'a': [1.5, None, True]}, sort_keys=True))"
```

What you should see (captured from this repository):

```text
{"a": [1.5, null, true], "b": 1}
```

2. A price stored as text and read as an exact `Decimal`.

```bash
.venv/bin/python -c "import json; d = json.loads('{\"price\": \"0.0001\"}'); from decimal import Decimal; print(Decimal(d['price']) * 3)"
```

What you should see (captured from this repository):

```text
0.0003
```

3. A trailing comma is not allowed in JSON; this is the error.

```bash
.venv/bin/python -c "import json; json.loads('{\"a\": 1,}')" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
json.decoder.JSONDecodeError: Illegal trailing comma before end of object: line 1 column 8 (char 7)
```

4. How many JSON files the repository tracks and generates, outside the tool caches.

```bash
find . -name '*.json' -not -path './.venv/*' -not -path './.mypy_cache/*' -not -path './.ruff_cache/*' -not -path './.import_linter_cache/*' | wc -l
```

What you should see (captured from this repository):

```text
       2
```

5. Python's built-in pretty printer (`json.tool`) reformats any JSON text.

```bash
head -1 data/tasks.jsonl | .venv/bin/python -m json.tool | sed -n 1,6p
```

What you should see (captured from this repository):

```text
{
    "id": "t-book-01",
    "kind": "book",
    "text": "Book a 30-minute meeting with alice and bob on 2026-11-03.",
    "facts": [
        [
```

## Mistakes people make

- **Comments or trailing commas.** JSON allows neither; the parser raises an error.
- **Storing money as a number.** `0.1 + 0.2` is not `0.3` in binary floating point. Prices are text, read with `Decimal`.
- **Assuming key order means something.** Order is not part of the format.
- **Single quotes.** JSON strings use double quotes only.
- **Hand-editing a generated file.** Reports are written by the program; edit the code or data and rerun.

## Check yourself

1. What are the six JSON value kinds?

   *Answer:* Text, number, true/false, null, array, object.

2. Why are prices stored as text?

   *Answer:* So they can be read as exact decimals instead of floating-point numbers.

3. Can a JSON file hold a comment?

   *Answer:* No.

4. What does `json.loads` return for an object?

   *Answer:* A Python dictionary.

5. Why write JSON with sorted keys?

   *Answer:* So the same data always produces the same bytes and the file diff shows real changes only.

## Further reading

- ECMA-404 / RFC 8259, https://www.rfc-editor.org/rfc/rfc8259 and Python `json`, https://docs.python.org/3/library/json.html (examples run on Python 3.13).
