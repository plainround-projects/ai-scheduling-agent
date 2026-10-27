# Regular expressions

## What it is

A **regular expression** (regex) is a short pattern that describes a set of texts, used to find, check or pull apart text. `^PR-\d{6}$` describes "the whole text is `PR-` followed by exactly six digits". Python's `re` module runs them; pydantic and JSON Schema accept the same kind of pattern for validation.

The vocabulary is small: ordinary characters match themselves; `.` matches any character; `[abc]` matches one of a set; `\d`, `\w`, `\s` match a digit, a word character, a whitespace; `+`, `*`, `?` and `{n,m}` say how many times; `^` and `$` anchor to the start and the end; `( )` groups and captures; `|` means or.

## Why this repository uses it

The code reads text it does not control: model answers, customer emails, help-center files, command strings. A pattern is the compact way to say "an order id looks like this" or "a heading line is one to three `#` signs". Putting the patterns in one named constant per rule (and, for field formats, in the pydantic model or JSON Schema) keeps them reviewable.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `(see list)` | each pattern lists the file and line where it is used |
| `src/scheduling_agent/infrastructure/files.py:12` | pattern: \A---\n(.*?)\n---\n(.*)\Z |
| `src/scheduling_agent/infrastructure/scripted_policy.py:29` | pattern: cancel event (ev-\d+) |
| `src/scheduling_agent/infrastructure/scripted_policy.py:31` | pattern: ^- (\w+): (.+?) \(said (\d{4}-\d{2}-\d{2}), session (\S+)\)$ |
| `src/scheduling_agent/infrastructure/scripted_policy.py:35` | pattern: ,\s*\|\s+and\s+ |

## How it works underneath

A regex engine reads the pattern and the text together and tries to match from left to right. For quantifiers it is *greedy* by default (take as much as possible, then give back if the rest fails); adding `?` after the quantifier makes it *lazy* (take as little as possible). When part of the pattern fails the engine *backtracks*: it returns to an earlier choice and tries another. That is why a badly written pattern on a long input can be slow; the patterns here are anchored and short.

**Functions.** `re.search(p, text)` finds the first match anywhere; `re.match` only at the start; `re.fullmatch` requires the whole text; `re.findall` returns all matches; `re.sub(p, replacement, text)` replaces matches; `re.compile(p)` prepares a pattern once for repeated use. In a match object, `.group(1)` is the text captured by the first parenthesis.

**Raw strings.** A Python string written `r"\d+"` keeps the backslash. Without the `r`, Python would read `\d` as its own escape.

## Walkthrough of this repository's use

Every regular expression found in this repository's code and data, taken apart piece by piece.

#### `\A---\n(.*?)\n---\n(.*)\Z`

Used in `src/scheduling_agent/infrastructure/files.py:12` (`re.compile`).

| Piece | Meaning |
| --- | --- |
| `\A` | the very start of the text |
| `---` | the text itself, letter for letter |
| `\n` | a newline character |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `.` | any single character except a newline |
| `*?` | zero or more of the thing before; the `?` makes it *lazy*: take as little as possible |
| `)` | ends the group |
| `\n` | a newline character |
| `---` | the text itself, letter for letter |
| `\n` | a newline character |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `.` | any single character except a newline |
| `*` | zero or more of the thing before |
| `)` | ends the group |
| `\Z` | the very end of the text |

#### `cancel event (ev-\d+)`

Used in `src/scheduling_agent/infrastructure/scripted_policy.py:29` (`re.compile`).

| Piece | Meaning |
| --- | --- |
| `cancel event ` | the text itself, letter for letter |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `ev-` | the text itself, letter for letter |
| `\d` | a digit (0 to 9) |
| `+` | one or more of the thing before |
| `)` | ends the group |

#### `^- (\w+): (.+?) \(said (\d{4}-\d{2}-\d{2}), session (\S+)\)$`

Used in `src/scheduling_agent/infrastructure/scripted_policy.py:31` (`re.compile`).

| Piece | Meaning |
| --- | --- |
| `^` | start of the text (or of a line with the `m` flag) |
| `- ` | the text itself, letter for letter |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `\w` | a word character: a letter, a digit or an underscore |
| `+` | one or more of the thing before |
| `)` | ends the group |
| `: ` | the text itself, letter for letter |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `.` | any single character except a newline |
| `+?` | one or more of the thing before; the `?` makes it *lazy*: take as little as possible |
| `)` | ends the group |
| ` ` | the text itself, letter for letter |
| `\(` | the literal character `(` (the backslash removes its special meaning) |
| `said ` | the text itself, letter for letter |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `\d` | a digit (0 to 9) |
| `{4}` | exactly 4 of the thing before |
| `-` | the text itself, letter for letter |
| `\d` | a digit (0 to 9) |
| `{2}` | exactly 2 of the thing before |
| `-` | the text itself, letter for letter |
| `\d` | a digit (0 to 9) |
| `{2}` | exactly 2 of the thing before |
| `)` | ends the group |
| `, session ` | the text itself, letter for letter |
| `(` | starts a capture group: the matched text is saved and can be read back |
| `\S` | anything that is not whitespace |
| `+` | one or more of the thing before |
| `)` | ends the group |
| `\)` | the literal character `)` (the backslash removes its special meaning) |
| `$` | end of the text (or of a line with the `m` flag) |

#### `,\s*|\s+and\s+`

Used in `src/scheduling_agent/infrastructure/scripted_policy.py:35` (`re.split`).

| Piece | Meaning |
| --- | --- |
| `,` | the text itself, letter for letter |
| `\s` | a whitespace character (space, tab, newline) |
| `*` | zero or more of the thing before |
| `\|` | or: either what is on the left or what is on the right |
| `\s` | a whitespace character (space, tab, newline) |
| `+` | one or more of the thing before |
| `and` | the text itself, letter for letter |
| `\s` | a whitespace character (space, tab, newline) |
| `+` | one or more of the thing before |

## Try it yourself

1. Compile a pattern from this repository and print it back.

```bash
.venv/bin/python -c "import re; p = re.compile(r'\A---\n(.*?)\n---\n(.*)\Z'); print(p.pattern)"
```

What you should see (captured from this repository):

```text
\A---\n(.*?)\n---\n(.*)\Z
```

2. `{6}` means exactly six: a five-digit id does not match.

```bash
.venv/bin/python -c "import re; print(re.fullmatch(r'PR-\d{6}', 'PR-123456') is not None, re.fullmatch(r'PR-\d{6}', 'PR-12345') is not None)"
```

What you should see (captured from this repository):

```text
True False
```

3. Greedy versus lazy: `.+` takes as much as it can, `.+?` as little.

```bash
.venv/bin/python -c "import re; print(re.findall(r'<.+>', '<a><b>'), re.findall(r'<.+?>', '<a><b>'))"
```

What you should see (captured from this repository):

```text
['<a><b>'] ['<a>', '<b>']
```

4. Capture groups pull out the parts you care about.

```bash
.venv/bin/python -c "import re; m = re.search(r'order (\S+) on (\d{4}-\d{2}-\d{2})', 'refund order ord-1201 on 2026-11-03'); print(m.group(1), m.group(2))"
```

What you should see (captured from this repository):

```text
ord-1201 2026-11-03
```

5. Replace every run of unwanted characters with one hyphen: a slug.

```bash
.venv/bin/python -c "import re; print(re.sub(r'[^a-z0-9]+', '-', 'Free Return, 30 days!'.lower()).strip('-'))"
```

What you should see (captured from this repository):

```text
free-return-30-days
```

## Mistakes people make

- **Forgetting the anchors.** `\d{6}` finds six digits inside `1234567`. Format checks use `^...$` (or `fullmatch`).
- **Greedy surprises.** `.+` runs to the last possible match. Use `.+?` or a negated class like `[^"]+`.
- **Not escaping a dot.** `.` matches any character; a literal dot is `\.`.
- **Writing a regex where a parser is needed.** JSON, dates and HTML are read with `json`, `date.fromisoformat` and proper parsers; the regexes only cut simple text.
- **Normal strings instead of raw strings.** Use `r"..."` so backslashes reach the regex engine.
- **Catastrophic backtracking.** Avoid nested quantifiers such as `(a+)+` on untrusted text.

## Check yourself

1. What does `^PR-\d{6}$` accept?

   *Answer:* Exactly `PR-` followed by six digits and nothing else.

2. What is the difference between `.+` and `.+?`?

   *Answer:* Greedy takes as much as possible; lazy takes as little as possible.

3. What does `(?i)` do?

   *Answer:* Turns on case-insensitive matching for the pattern.

4. What does `\b` match?

   *Answer:* A word boundary, a position rather than a character.

5. When do you use `re.fullmatch`?

   *Answer:* When the whole text must fit the pattern.

## Further reading

- Python `re` module and Regular Expression HOWTO, https://docs.python.org/3/library/re.html and https://docs.python.org/3/howto/regex.html (the piece-by-piece tables were generated by a small tokenizer that stops on any syntax it does not know; examples run on Python 3.13).
