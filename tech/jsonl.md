# JSON Lines (JSONL)

## What it is

**JSON Lines** is JSON with one rule added: a file holds **one complete JSON value per line** (almost always an object), with no commas between lines and no enclosing brackets. A file of 450 records is simply 450 lines. A reader can process it one line at a time without loading the whole file.

## Why this repository uses it

Two properties matter here. First, **appending is safe**: adding a record is writing one line at the end, so a recording that is interrupted keeps every complete line, and a restarted recording resumes from there. Second, **diffs and tools work line by line**: `wc -l` counts records and `grep` finds one. The recordings (answers saved from a real local model so that tests and demos can replay them) are JSON Lines for exactly this reason.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `data/tasks.jsonl` | records, one per line |
| `tests/fixtures/embeddings/nomic-embed-text.jsonl` | records, one per line |

## How it works underneath

To read a JSON Lines file, split the text on newline characters and parse each non-empty line with an ordinary JSON parser. To write one, serialize each record with no line breaks inside (JSON escapes a newline inside text as `\n`, so a record never spans lines) and add one newline. If a process dies in the middle of writing a line, the last line is incomplete; a careful reader skips or cuts it.

A **recording** here is keyed by a SHA-256 fingerprint of the request (model, messages, settings). Replaying means: compute the fingerprint of the new request, look it up, and return the saved answer. The same request therefore always gets the same answer, offline, which is what makes the test numbers repeatable.

## Walkthrough of this repository's use

### Every JSON Lines file in this repository

| File | Shape | Keys (first ones) |
| --- | --- | --- |
| `data/tasks.jsonl` | one JSON object per line, 30 lines | `id`, `kind`, `text`, `facts`, `add`, `remove` |
| `tests/fixtures/embeddings/nomic-embed-text.jsonl` | one JSON object per line, 20 lines | `key`, `model`, `vector` |

### The files, key by key

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

`tests/fixtures/embeddings/nomic-embed-text.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "key": "f1109be0a3f3b4cf0d9c7b6124ffd4026316ca200a0904d696e31ee090d42e38",
  "model": "nomic-embed-text",
  "vector": "QbStvIgRpj2O+TG+BqtmvfB+AzzIyx49pqpwvNIZKb3GFnI8fEG2PCDTI730noA9kk3ru7..."
}
```

What each key means:

- `key` (text): a fingerprint (SHA-256) of the request, used to look the answer up.
- `model` (text): the model id (a name the provider or the local server knows).
- `vector` (text): the embedding, as base64 text of 32-bit floating-point numbers.

### Embedding vectors

A vector is a list of numbers (768 of them for `nomic-embed-text`). Written as JSON numbers it would take about 20 characters each. The files that hold vectors store them as **base64 text of 32-bit floats** (4 bytes per number, 3072 bytes per vector, then base64 encoded to plain letters and digits). Reading one back is `struct.unpack` of the decoded bytes. This keeps those files smaller and exact (a float32 round-trips without loss).

## Try it yourself

1. A JSON Lines file's record count is its line count.

```bash
wc -l data/tasks.jsonl
```

What you should see (captured from this repository):

```text
      30 data/tasks.jsonl
```

2. The first record, as stored: one line.

```bash
head -c 300 data/tasks.jsonl
```

What you should see (captured from this repository):

```text
{"id": "t-book-01", "kind": "book", "text": "Book a 30-minute meeting with alice and bob on 2026-11-03.", "facts": [["alice", "I never want meetings before 10"]], "add": [{"people": ["alice", "bob"], "start": "2026-11-03T10:00", "minutes": 30}], "remove": []}
{"id": "t-book-02", "kind": "book", "tex
```

3. Parse every line and list the keys of the first record.

```bash
.venv/bin/python -c "import json; rows = [json.loads(x) for x in open('data/tasks.jsonl') if x.strip()]; print(len(rows), sorted(rows[0]))"
```

What you should see (captured from this repository):

```text
30 ['add', 'facts', 'id', 'kind', 'remove', 'text']
```

4. A well-formed file ends with a newline.

```bash
tail -c 1 data/tasks.jsonl | od -c | head -1
```

What you should see (captured from this repository):

```text
0000000   \n                                                            
```

## Mistakes people make

- **Wrapping the records in `[ ]` or adding commas.** That is plain JSON, not JSON Lines.
- **A record with a real line break inside.** JSON escapes it as `\n`; a writer must use a JSON serializer, never hand-built text.
- **Assuming the last line is complete.** After a crash it may be cut off.
- **Re-sorting a recording.** Order does not matter to the replay, but a changed order makes a diff noisy.
- **Loading a huge file at once.** Read it line by line.

## Check yourself

1. What distinguishes JSON Lines from JSON?

   *Answer:* One complete JSON value per line; no commas or outer brackets.

2. Why does append-only suit recordings?

   *Answer:* An interrupted run keeps every finished line and can resume.

3. How is a request matched to its recorded answer?

   *Answer:* By a SHA-256 fingerprint of the request.

4. How are embedding vectors stored here?

   *Answer:* As base64 text of 32-bit floats.

5. How do you count the records?

   *Answer:* Count the lines (`wc -l`).

## Further reading

- JSON Lines, https://jsonlines.org/ (the format is a convention on top of RFC 8259 JSON; examples were run locally).
