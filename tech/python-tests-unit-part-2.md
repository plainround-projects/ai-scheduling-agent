# Python source, the unit tests (part 2 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 5 files with 58 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 124 non-blank lines |
| `tests/unit/infrastructure/test_calendar_service.py` | 230 non-blank lines |
| `tests/unit/infrastructure/test_openai_compatible.py` | 102 non-blank lines |
| `tests/unit/infrastructure/test_recording.py` | 45 non-blank lines |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 134 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/infrastructure/test_anthropic_chat.py`

124 non-blank lines; it defines `message`, `adapter`, `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, `test_a_schema_goes_into_output_config_format_not_a_forced_tool`, `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`, `test_tool_use_blocks_in_the_response_become_tool_calls`, `test_other_stop_reasons_are_mapped`, `test_rate_limits_and_server_errors_are_transient`, `test_a_bad_request_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 1 to 13:

```python
import json

import anthropic
import httpx2
import pytest

from scheduling_agent.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from scheduling_agent.infrastructure.anthropic_chat import AnthropicChatModel
from tests.conftest import FixedClock


def message(content, stop="end_turn", tokens_in=21, tokens_out=6):
```

- Makes the module `json` (standard library) available.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx2` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `scheduling_agent.domain.llm`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.) from the project module `scheduling_agent.infrastructure.anthropic_chat`.
- Brings in `FixedClock` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.) from the project module `tests.conftest`.
- Defines the function `message`.
- Its parameters:
    - `content`.
    - `stop`; if the caller leaves it out it is the text `end_turn`.
    - `tokens_in`; if the caller leaves it out it is the number `21`.
    - `tokens_out`; if the caller leaves it out it is the number `6`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 14 to 26:

```python
    return httpx2.Response(
        200,
        json={
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": content,
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out},
        },
    )
```

- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 29 to 39:

```python
def adapter(handler, thinking="disabled"):
    client = anthropic.Anthropic(
        api_key="test-key-not-real",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, "claude-haiku-5-5", FixedClock(), thinking)


def test_text_usage_stop_reason_and_model_come_from_the_response():
    seen = {}
```

- Defines the function `adapter`.
- Its parameters:
    - `handler`.
    - `thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
  - `anthropic.DefaultHttpxClient` from the installed package module `anthropic`.
  - `httpx2.MockTransport` from the installed package module `httpx2`.
- Ends the function and gives back the result of calling `AnthropicChatModel` to the caller.
  - `AnthropicChatModel` from the project's `scheduling_agent.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Defines the function `test_text_usage_stop_reason_and_model_come_from_the_response`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 41 to 53:

```python
    def handler(request):
        seen["body"] = json.loads(request.content)
        return message([{"type": "text", "text": "hello"}])

    response = adapter(handler).complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=40)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 21, 6)
    assert response.stop_reason is StopReason.END
    assert response.model == "claude-haiku-5-5"
    assert seen["body"]["system"] == "be brief"
    assert seen["body"]["max_tokens"] == 40
    assert seen["body"]["thinking"] == {"type": "disabled"}
```

- Defines the function `handler`.
- Its parameters:
    - `request`.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `message` to the caller.
  - `message`, a function of this file.
- Stores the result of calling `adapter(handler).complete` under the name `response`.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['body']['system'] == 'be brief'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['max_tokens'] == 40` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['thinking'] == {'type': 'disabled'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 54 to 67:

```python
    assert "temperature" not in seen["body"]
    assert "top_p" not in seen["body"]


def test_sampling_is_refused_because_the_messages_api_rejects_it():
    model = adapter(lambda r: message([]))
    assert not model.supports_sampling
    with pytest.raises(UnsupportedParameter, match="temperature"):
        model.complete(ChatRequest((ChatMessage.user("hi"),), temperature=0.0))
    with pytest.raises(UnsupportedParameter):
        model.complete(ChatRequest((ChatMessage.user("hi"),), top_p=0.9))


def test_thinking_can_be_left_out_or_set_to_between_tools():
```

- Checks that `'temperature' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'top_p' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_sampling_is_refused_because_the_messages_api_rejects_it`.
- It takes no parameters.
- Stores the result of calling `adapter` under the name `model`.
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter, match='temperature')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the function `test_thinking_can_be_left_out_or_set_to_between_tools`.
- It takes no parameters.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 68 to 79:

```python
    assert "thinking" not in adapter(lambda r: message([]), "omit").build_payload(ChatRequest((ChatMessage.user("x"),)))
    payload = adapter(lambda r: message([]), "between_tools").build_payload(ChatRequest((ChatMessage.user("x"),)))
    assert payload["thinking"] == {"type": "between_tools"}


def test_a_schema_goes_into_output_config_format_not_a_forced_tool():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    payload = adapter(lambda r: message([])).build_payload(
        ChatRequest((ChatMessage.user("x"),), response_schema=schema)
    )
    assert payload["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "tool_choice" not in payload
```

- Checks that `'thinking' not in adapter(lambda r: message([]), 'omit').build_payload(ChatRe...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `build_payload` of `adapter(lambda r: message([]), 'omit')`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Stores the result of calling `adapter(lambda r: message([]), 'between_tools')...` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]), 'betwe...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['thinking'] == {'type': 'between_tools'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_goes_into_output_config_format_not_a_forced_tool`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['output_config'] == {'format': {'type': 'json_schema', 'schema': sche...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'tool_choice' not in payload` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 82 to 93:

```python
def test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks():
    history = (
        ChatMessage.user("book it"),
        ChatMessage(
            Role.ASSISTANT, "checking", (ToolCall("t1", "slots", {"day": "mon"}), ToolCall("t2", "get", {"id": 1}))
        ),
        ChatMessage(Role.TOOL, "free", tool_call_id="t1"),
        ChatMessage(Role.TOOL, "event", tool_call_id="t2"),
    )
    spec = ToolSpec("slots", "find slots", {"type": "object"})
    payload = adapter(lambda r: message([])).build_payload(ChatRequest(history, tools=(spec,)))
    assert payload["tools"] == [{"name": "slots", "description": "find slots", "input_schema": {"type": "object"}}]
```

- Defines the function `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`.
- It takes no parameters.
- Stores a tuple of 4 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `scheduling_agent.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `payload['tools'] == [{'name': 'slots', 'description': 'find slots', 'input_sc...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 94 to 107:

```python
    assistant = payload["messages"][1]["content"]
    assert [b["type"] for b in assistant] == ["text", "tool_use", "tool_use"]
    results = payload["messages"][2]
    assert results["role"] == "user"
    assert [b["tool_use_id"] for b in results["content"]] == ["t1", "t2"]
    assert len(payload["messages"]) == 3


def test_tool_use_blocks_in_the_response_become_tool_calls():
    content = [
        {"type": "text", "text": "ok"},
        {"type": "tool_use", "id": "tu1", "name": "slots", "input": {"day": "tue"}},
    ]
    response = adapter(lambda r: message(content, "tool_use")).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Stores the part of `payload['messages'][1]` picked by `'content'` under the name `assistant`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['type'] for b in assistant] == ['text', 'tool_use', 'tool_use']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `payload['messages']` picked by `2` under the name `results`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `results['role'] == 'user'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['tool_use_id'] for b in results['content']] == ['t1', 't2']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `len(payload['messages']) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_use_blocks_in_the_response_become_tool_calls`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `content`.
- Stores the result of calling `adapter(lambda r: message(content, 'tool_use'))...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message(content, 't...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 108 to 120:

```python
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("tu1", "slots", {"day": "tue"}),)


@pytest.mark.parametrize(
    ("stop", "expected"),
    [("max_tokens", StopReason.LENGTH), ("refusal", StopReason.REFUSAL), ("pause_turn", StopReason.OTHER)],
)
def test_other_stop_reasons_are_mapped(stop, expected):
    response = adapter(lambda r: message([{"type": "text", "text": "x"}], stop)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is expected
```

- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('tu1', 'slots', {'day': 'tue'}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Defines the function `test_other_stop_reasons_are_mapped`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `stop`.
    - `expected`.
- Stores the result of calling `adapter(lambda r: message([{'type': 'text', 'te...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message([{'type': '...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `response.stop_reason is expected` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 123 to 134:

```python
@pytest.mark.parametrize("status", [429, 500, 529])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        adapter(
            lambda r: httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "y"}})
        ).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_bad_request_is_permanent():
    body = {"type": "error", "error": {"type": "invalid_request_error", "message": "nope"}}
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        adapter(lambda r: httpx2.Response(400, json=body)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(sta...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(sta...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.
- Defines the function `test_a_bad_request_is_permanent`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `body`.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(400...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(400...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 137 to 148:

```python
def test_a_dropped_connection_is_transient():
    def handler(request):
        raise httpx2.ConnectError("refused", request=request)

    with pytest.raises(TransientModelError):
        adapter(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_count_tokens_asks_the_provider_without_generating():
    seen = {}

    def handler(request):
```

- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.
- Defines the function `handler`.
- Its parameters:
    - `request`.
- Raises an error: the result of calling `httpx2.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx2.ConnectError` from the installed package module `httpx2`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_count_tokens_asks_the_provider_without_generating`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.
- Defines the function `handler`.
- Its parameters:
    - `request`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 149 to 157:

```python
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json={"input_tokens": 17})

    count = adapter(handler).count_tokens(ChatRequest((ChatMessage.user("hi"),), system="s"))
    assert count == 17
    assert seen["path"].endswith("/messages/count_tokens")
    assert "max_tokens" not in seen["body"]
    assert "thinking" not in seen["body"]
```

- Stores the `path` of `request.url` under the name `seen['path']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.
- Stores the result of calling `adapter(handler).count_tokens` under the name `count`.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `count == 17` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['path'].endswith('/messages/count_tokens')` is true; if it is not, the test fails with an `AssertionError`.
  - `.endswith(...)` asks whether text ends with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'max_tokens' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'thinking' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/unit/infrastructure/test_calendar_service.py`

230 non-blank lines; it defines `free_start`, `test_the_seed_has_five_people_and_two_weeks_of_meetings_and_nobody_is_double_booked`, `test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event`, `test_two_different_bookings_with_identical_content_but_different_keys_are_not_mistaken_for_duplicates`, `test_reusing_a_key_for_a_different_request_is_a_conflict_not_a_silent_replay`, `test_a_failed_write_leaves_no_idempotency_key_behind_so_the_retry_can_succeed`, `test_the_booking_rules_each_raise_their_own_error`, `test_cancel_frees_the_time_replays_by_key_and_refuses_a_second_cancel_with_a_new_key`, `test_parallel_requests_with_one_key_create_one_event_and_with_two_keys_for_one_slot_only_one_wins`, `served`, `test_the_http_api_books_replays_and_maps_errors_to_status_codes`, `test_the_http_api_lists_people_slots_and_active_events_and_reports_health`, ....

`tests/unit/infrastructure/test_calendar_service.py`, lines 1 to 6:

```python
import threading
from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient
```

- Makes the module `threading` (standard library) available.
- Brings in `datetime` from the standard library module `datetime`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `TestClient` from the installed package module `fastapi.testclient`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 8 to 20:

```python
from scheduling_agent.domain.errors import (
    AlreadyCancelled,
    CalendarError,
    IdempotencyConflict,
    InvalidSlot,
    SlotUnavailable,
    UnknownEvent,
    UnknownPerson,
)
from scheduling_agent.infrastructure.calendar_client import HttpCalendar
from scheduling_agent.infrastructure.calendar_seed import init_calendar, reset_calendar
from scheduling_agent.infrastructure.sqlite import connect
from scheduling_agent.interfaces.calendar_api import create_app
```

- Brings in `AlreadyCancelled` (The event is already cancelled.), `CalendarError` (The calendar refused or could not do what was asked.), `IdempotencyConflict` (An Idempotency-Key was reused for a different request.), `InvalidSlot` (The time is outside working hours, off the half-hour grid, on a weekend or has a bad length.), `SlotUnavailable` (A person is already busy at that time.), `UnknownEvent` (No event with that id.), `UnknownPerson` (A name that is not one of the calendar's people.) from the project module `scheduling_agent.domain.errors`.
- Brings in `HttpCalendar` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.) from the project module `scheduling_agent.infrastructure.calendar_client`.
- Brings in `init_calendar` (Create the tables and load the seed if the database has no people yet.), `reset_calendar` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).) from the project module `scheduling_agent.infrastructure.calendar_seed`.
- Brings in `connect` (Open a database with the settings every store here relies on.) from the project module `scheduling_agent.infrastructure.sqlite`.
- Brings in `create_app` (Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data.) from the project module `scheduling_agent.interfaces.calendar_api`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 21 to 34:

```python
from tests.conftest import REPO, new_calendar

QUIET = datetime(2026, 11, 3, 16, 0)  # a time at which alice and bob are free in the seed


def free_start(calendar, people=("alice", "bob"), minutes=30):
    slots = calendar.free_slots(list(people), QUIET.date(), QUIET.date(), minutes)
    return slots[0]


def test_the_seed_has_five_people_and_two_weeks_of_meetings_and_nobody_is_double_booked():
    calendar = new_calendar()
    assert calendar.people() == ["alice", "bob", "carol", "dave", "erin"]
    events = calendar.active_events()
```

- Brings in `REPO`, `new_calendar` from the project module `tests.conftest`.
- Stores the result of calling `datetime` under the name `QUIET`.
  - `datetime` from the standard library module `datetime`.
- Defines the function `free_start`.
- Its parameters:
    - `calendar`.
    - `people`; if the caller leaves it out it is a tuple of 2 item(s).
    - `minutes`; if the caller leaves it out it is the number `30`.
- Stores the result of calling `calendar.free_slots` under the name `slots`.
  - The method `free_slots` of `calendar`.
  - `list` makes a list (a copy when given a collection).
  - The method `date` of `QUIET`.
- Ends the function and gives back the part of `slots` picked by `0` to the caller.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_the_seed_has_five_people_and_two_weeks_of_meetings_and_nobody_is_double_booked`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Checks that `calendar.people() == ['alice', 'bob', 'carol', 'dave', 'erin']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `people` of `calendar`.
- Stores the result of calling `calendar.active_events` under the name `events`.
  - The method `active_events` of `calendar`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 35 to 48:

```python
    assert len(events) >= 30
    assert min(e.start for e in events).date().isoformat() == "2026-11-02"
    assert max(e.start for e in events).date().isoformat() <= "2026-11-13"
    for a in events:
        for b in events:
            if a.id < b.id and set(a.people) & set(b.people):
                assert a.end <= b.start or b.end <= a.start


def test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event():
    calendar = new_calendar()
    start = free_start(calendar)
    before = len(calendar.active_events())
    first = calendar.book(["alice", "bob"], start, 30, "key-0001-aaaa")
```

- Checks that `len(events) >= 30` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `min((e.start for e in events)).date().isoformat() == '2026-11-02'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `min` picks the smallest value.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `max((e.start for e in events)).date().isoformat() <= '2026-11-13'` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `max` picks the largest value.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Loop: the indented lines below run once for each item of `events`; `a` names the current item.
- Loop: the indented lines below run once for each item of `events`; `b` names the current item.
- Decision: the indented lines below run only when `a.id < b.id and set(a.people) & set(b.people)` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `&` is and.
  - `set` makes a set: a collection with no repeated items.
- Checks that `a.end <= b.start or b.end <= a.start` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<=` means less than or equal.
- Defines the function `test_booking_the_same_request_twice_with_one_key_creates_exactly_one_event`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the result of calling `free_start` under the name `start`.
  - `free_start`, a function of this file.
- Stores the result of calling `len` under the name `before`.
  - `len` counts the items in a collection (or the characters in text).
  - The method `active_events` of `calendar`.
- Stores the result of calling `calendar.book` under the name `first`.
  - The method `book` of `calendar`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 49 to 62:

```python
    second = calendar.book(["alice", "bob"], start, 30, "key-0001-aaaa")
    assert first.event.id == second.event.id
    assert (first.replayed, second.replayed) == (False, True)
    assert len(calendar.active_events()) == before + 1


def test_two_different_bookings_with_identical_content_but_different_keys_are_not_mistaken_for_duplicates():
    calendar = new_calendar()
    start = free_start(calendar)
    calendar.book(["alice"], start, 30, "key-0001-aaaa")
    with pytest.raises(
        SlotUnavailable
    ):  # the second is a real conflict, not a replay: the key decides, not the content
        calendar.book(["alice"], start, 30, "key-0002-bbbb")
```

- Stores the result of calling `calendar.book` under the name `second`.
  - The method `book` of `calendar`.
- Checks that `first.event.id == second.event.id` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `(first.replayed, second.replayed) == (False, True)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `len(calendar.active_events()) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - The method `active_events` of `calendar`.
- Defines the function `test_two_different_bookings_with_identical_content_but_different_keys_are_not_mistaken_for_duplicates`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the result of calling `free_start` under the name `start`.
  - `free_start`, a function of this file.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
- A `with` block: it sets up `pytest.raises(SlotUnavailable)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 65 to 76:

```python
def test_reusing_a_key_for_a_different_request_is_a_conflict_not_a_silent_replay():
    calendar = new_calendar()
    start = free_start(calendar)
    calendar.book(["alice"], start, 30, "key-0001-aaaa")
    with pytest.raises(IdempotencyConflict):
        calendar.book(["alice"], start.replace(hour=15), 30, "key-0001-aaaa")


def test_a_failed_write_leaves_no_idempotency_key_behind_so_the_retry_can_succeed():
    calendar = new_calendar()
    with pytest.raises(InvalidSlot):
        calendar.book(["alice"], datetime(2026, 11, 3, 3, 0), 30, "key-0003-cccc")
```

- Defines the function `test_reusing_a_key_for_a_different_request_is_a_conflict_not_a_silent_replay`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the result of calling `free_start` under the name `start`.
  - `free_start`, a function of this file.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
- A `with` block: it sets up `pytest.raises(IdempotencyConflict)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `.replace(...)` replaces every occurrence of one piece of text with another.
- Defines the function `test_a_failed_write_leaves_no_idempotency_key_behind_so_the_retry_can_succeed`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- A `with` block: it sets up `pytest.raises(InvalidSlot)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `datetime` from the standard library module `datetime`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 77 to 90:

```python
    assert calendar.book(["alice"], free_start(calendar, ("alice",)), 30, "key-0003-cccc").replayed is False


def test_the_booking_rules_each_raise_their_own_error():
    calendar = new_calendar()
    busy = calendar.active_events()[0]
    with pytest.raises(SlotUnavailable, match="busy"):
        calendar.book(list(busy.people), busy.start, 30, "key-0004-dddd")
    with pytest.raises(UnknownPerson):
        calendar.book(["zed"], QUIET, 30, "key-0005-eeee")
    with pytest.raises(UnknownPerson):
        calendar.book([], QUIET, 30, "key-0006-ffff")
    with pytest.raises(InvalidSlot):
        calendar.book(["alice"], datetime(2026, 11, 7, 10, 0), 30, "key-0007-gggg")
```

- Checks that `calendar.book(['alice'], free_start(calendar, ('alice',)), 30, 'key-0003-cccc...` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `book` of `calendar`.
  - `free_start`, a function of this file.
- Defines the function `test_the_booking_rules_each_raise_their_own_error`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the part of `calendar.active_events()` picked by `0` under the name `busy`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `calendar`.
- A `with` block: it sets up `pytest.raises(SlotUnavailable, match='busy')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `list` makes a list (a copy when given a collection).
- A `with` block: it sets up `pytest.raises(UnknownPerson)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
- A `with` block: it sets up `pytest.raises(UnknownPerson)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
- A `with` block: it sets up `pytest.raises(InvalidSlot)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `datetime` from the standard library module `datetime`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 91 to 104:

```python
    with pytest.raises(UnknownEvent):
        calendar.get_event("ev-9999")


def test_cancel_frees_the_time_replays_by_key_and_refuses_a_second_cancel_with_a_new_key():
    calendar = new_calendar()
    event = calendar.active_events()[0]
    first = calendar.cancel(event.id, "key-0008-hhhh")
    again = calendar.cancel(event.id, "key-0008-hhhh")
    assert first.event.cancelled
    assert again.replayed
    assert event.id not in {e.id for e in calendar.active_events()}
    with pytest.raises(AlreadyCancelled):
        calendar.cancel(event.id, "key-0009-iiii")
```

- A `with` block: it sets up `pytest.raises(UnknownEvent)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `get_event` of `calendar` with 1 argument(s); the result is not kept.
  - The method `get_event` of `calendar`.
- Defines the function `test_cancel_frees_the_time_replays_by_key_and_refuses_a_second_cancel_with_a_new_key`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the part of `calendar.active_events()` picked by `0` under the name `event`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `active_events` of `calendar`.
- Stores the result of calling `calendar.cancel` under the name `first`.
  - The method `cancel` of `calendar`.
- Stores the result of calling `calendar.cancel` under the name `again`.
  - The method `cancel` of `calendar`.
- Checks that `first.event.cancelled` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `again.replayed` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `event.id not in {e.id for e in calendar.active_events()}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `calendar`.
- A `with` block: it sets up `pytest.raises(AlreadyCancelled)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `cancel` of `calendar` with 2 argument(s); the result is not kept.
  - The method `cancel` of `calendar`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 105 to 118:

```python
    with pytest.raises(UnknownEvent):
        calendar.cancel("ev-9999", "key-0010-jjjj")
    calendar.book(list(event.people), event.start, event.minutes, "key-0011-kkkk")  # the slot is free again


def test_parallel_requests_with_one_key_create_one_event_and_with_two_keys_for_one_slot_only_one_wins():
    calendar = new_calendar()
    start = free_start(calendar)
    before = len(calendar.active_events())
    outcomes: list[str] = []

    def attempt(key: str) -> None:
        try:
            calendar.book(["alice", "bob"], start, 30, key)
```

- A `with` block: it sets up `pytest.raises(UnknownEvent)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `cancel` of `calendar` with 2 argument(s); the result is not kept.
  - The method `cancel` of `calendar`.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `list` makes a list (a copy when given a collection).
- Defines the function `test_parallel_requests_with_one_key_create_one_event_and_with_two_keys_for_one_slot_only_one_wins`.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Stores the result of calling `free_start` under the name `start`.
  - `free_start`, a function of this file.
- Stores the result of calling `len` under the name `before`.
  - `len` counts the items in a collection (or the characters in text).
  - The method `active_events` of `calendar`.
- Declares `outcomes` as a list of text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `attempt`. It returns nothing (None).
- Its parameters:
    - `key` holds text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 119 to 130:

```python
            outcomes.append("ok")
        except SlotUnavailable:
            outcomes.append("conflict")

    threads = [threading.Thread(target=attempt, args=("same-key-001",)) for _ in range(6)]
    threads += [threading.Thread(target=attempt, args=("other-key-02",))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(calendar.active_events()) == before + 1
    assert outcomes.count("ok") >= 6
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- `except` handler: it runs when the `try` block raised the project type `SlotUnavailable`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Stores a list built by looping under the name `threads`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `threading.Thread` makes a thread.
  - `range` makes the numbers from 0 up to (not including) the given one.
- Updates `threads` in place: `+=` applies `+` with a list of 1 item(s) and stores the result back.
  - `threading.Thread` makes a thread.
- Loop: the indented lines below run once for each item of `threads`; `thread` names the current item.
- Calls `.start(...)` starts a thread or process; the result is not kept.
  - `.start(...)` starts a thread or process.
- Loop: the indented lines below run once for each item of `threads`; `thread` names the current item.
- Calls `.join(...)` glues the pieces of a collection into one text, with the given text between them; the result is not kept.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Checks that `len(calendar.active_events()) == before + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - The method `active_events` of `calendar`.
- Checks that `outcomes.count('ok') >= 6` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `.count(...)` counts how often an item appears.

`tests/unit/infrastructure/test_calendar_service.py`, lines 133 to 144:

```python
@pytest.fixture
def served():
    calendar = new_calendar()
    return calendar, TestClient(create_app(calendar, reset=lambda: reset_calendar(calendar._db, REPO / "sql")))


def test_the_http_api_books_replays_and_maps_errors_to_status_codes(served):
    calendar, api = served
    start = free_start(calendar).isoformat(timespec="minutes")
    body = {"people": ["alice", "bob"], "start": start, "minutes": 30}
    first = api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0001"})
    second = api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0001"})
```

- Defines the function `served`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- It takes no parameters.
- Stores the result of calling `new_calendar` under the name `calendar`.
  - `new_calendar` from the project's `tests.conftest`.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `TestClient` from the installed package module `fastapi.testclient`.
  - `create_app` from the project's `scheduling_agent.interfaces.calendar_api` (Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data.).
  - `lambda args: expression` is a small unnamed function written inline.
  - `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).).
  - `/` is divide.
- Defines the function `test_the_http_api_books_replays_and_maps_errors_to_status_codes`.
- Its parameters:
    - `served`.
- Stores the value named `served` under the name `(calendar, api)`.
- Stores the result of calling `free_start(calendar).isoformat` under the name `start`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `free_start`, a function of this file.
- Stores a dictionary with 3 entries under the name `body`.
- Stores the result of calling `api.post` under the name `first`.
  - `.post(...)` sends an HTTP POST request.
- Stores the result of calling `api.post` under the name `second`.
  - `.post(...)` sends an HTTP POST request.

`tests/unit/infrastructure/test_calendar_service.py`, lines 145 to 153:

```python
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["event"]["id"] == second.json()["event"]["id"]
    assert second.json()["replayed"] is True
    assert api.get(f"/events/{first.json()['event']['id']}").json()["people"] == ["alice", "bob"]
    assert api.get("/events/ev-9999").status_code == 404
    assert (
        api.post("/events", json={**body, "people": ["zed"]}, headers={"Idempotency-Key": "http-key-0002"}).status_code
        == 404
    )
```

- Checks that `(first.status_code, second.status_code) == (201, 200)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `first.json()['event']['id'] == second.json()['event']['id']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Checks that `second.json()['replayed'] is True` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Checks that `api.get(f"/events/{first.json()['event']['id']}").json()['people'] == ['alice...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Checks that `api.get('/events/ev-9999').status_code == 404` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Checks that `api.post('/events', json={**body, 'people': ['zed']}, headers={'Idempotency-K...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.

`tests/unit/infrastructure/test_calendar_service.py`, lines 154 to 163:

```python
    assert (
        api.post(
            "/events", json={**body, "start": "2026-11-07T10:00"}, headers={"Idempotency-Key": "http-key-0003"}
        ).status_code
        == 422
    )
    assert api.post("/events", json=body, headers={"Idempotency-Key": "http-key-0004"}).status_code == 409
    assert api.post("/events", json=body).status_code == 422  # the header is required
    cancel = api.post(f"/events/{first.json()['event']['id']}/cancel", headers={"Idempotency-Key": "http-key-0005"})
    assert cancel.json()["event"]["cancelled"] is True
```

- Checks that `api.post('/events', json={**body, 'start': '2026-11-07T10:00'}, headers={'Ide...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Checks that `api.post('/events', json=body, headers={'Idempotency-Key': 'http-key-0004'})....` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Checks that `api.post('/events', json=body).status_code == 422` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
- Stores the result of calling `api.post` under the name `cancel`.
  - `.post(...)` sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Checks that `cancel.json()['event']['cancelled'] is True` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.

`tests/unit/infrastructure/test_calendar_service.py`, lines 164 to 175:

```python
    assert (
        api.post(
            f"/events/{first.json()['event']['id']}/cancel", headers={"Idempotency-Key": "http-key-0006"}
        ).status_code
        == 409
    )


def test_the_http_api_lists_people_slots_and_active_events_and_reports_health(served):
    calendar, api = served
    assert api.get("/health").json() == {"status": "ok", "people": 5}
    assert api.get("/people").json() == ["alice", "bob", "carol", "dave", "erin"]
```

- Checks that `api.post(f"/events/{first.json()['event']['id']}/cancel", headers={'Idempoten...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the function `test_the_http_api_lists_people_slots_and_active_events_and_reports_health`.
- Its parameters:
    - `served`.
- Stores the value named `served` under the name `(calendar, api)`.
- Checks that `api.get('/health').json() == {'status': 'ok', 'people': 5}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Checks that `api.get('/people').json() == ['alice', 'bob', 'carol', 'dave', 'erin']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`tests/unit/infrastructure/test_calendar_service.py`, lines 176 to 186:

```python
    slots = api.get(
        "/free-slots",
        params={
            "people": ["alice", "bob"],
            "first_day": "2026-11-03",
            "last_day": "2026-11-03",
            "minutes": 30,
            "not_before": "14:00",
        },
    ).json()
    assert slots["slots"][0].startswith("2026-11-03T14") or slots["slots"][0] > "2026-11-03T14:00"
```

- Stores the result of calling `api.get('/free-slots', params={'people': ['alic...` under the name `slots`.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Checks that `slots['slots'][0].startswith('2026-11-03T14') or slots['slots'][0] > '2026-11...` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.startswith(...)` asks whether text begins with the given text.
  - `>` means greater than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_calendar_service.py`, lines 187 to 200:

```python
    assert (
        api.get(
            "/free-slots",
            params={"people": ["zed"], "first_day": "2026-11-03", "last_day": "2026-11-03", "minutes": 30},
        ).status_code
        == 404
    )
    assert len(api.get("/events").json()) == len(calendar.active_events())


def test_the_reset_endpoint_reseeds_the_calendar_and_exists_only_when_enabled(served):
    calendar, api = served
    seeded = len(calendar.active_events())
    calendar.book(["alice"], free_start(calendar, ("alice",)), 30, "reset-key-001")
```

- Checks that `api.get('/free-slots', params={'people': ['zed'], 'first_day': '2026-11-03', ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Checks that `len(api.get('/events').json()) == len(calendar.active_events())` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - The method `active_events` of `calendar`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Defines the function `test_the_reset_endpoint_reseeds_the_calendar_and_exists_only_when_enabled`.
- Its parameters:
    - `served`.
- Stores the value named `served` under the name `(calendar, api)`.
- Stores the result of calling `len` under the name `seeded`.
  - `len` counts the items in a collection (or the characters in text).
  - The method `active_events` of `calendar`.
- Calls the method `book` of `calendar` with 4 argument(s); the result is not kept.
  - The method `book` of `calendar`.
  - `free_start`, a function of this file.

`tests/unit/infrastructure/test_calendar_service.py`, lines 201 to 214:

```python
    assert len(calendar.active_events()) == seeded + 1
    assert api.post("/admin/reset").json() == {"status": "reseeded"}
    assert len(calendar.active_events()) == seeded
    assert TestClient(create_app(new_calendar())).post("/admin/reset").status_code == 404


def test_the_http_client_speaks_the_same_contract_and_turns_error_bodies_back_into_domain_errors(served):
    calendar, api = served
    client = HttpCalendar(api, "http://testserver", attempts=1)
    start = free_start(calendar)
    booked = client.book(["alice", "bob"], start, 30, "client-key-001")
    assert client.book(["alice", "bob"], start, 30, "client-key-001").replayed is True
    assert client.get_event(booked.event.id).people == ("alice", "bob")
    assert booked.event.key() in {e.key() for e in client.active_events()}
```

- Checks that `len(calendar.active_events()) == seeded + 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `+` is add.
  - The method `active_events` of `calendar`.
- Checks that `api.post('/admin/reset').json() == {'status': 'reseeded'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.json(...)` reads the body of an HTTP answer as JSON.
  - `.post(...)` sends an HTTP POST request.
- Checks that `len(calendar.active_events()) == seeded` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `active_events` of `calendar`.
- Checks that `TestClient(create_app(new_calendar())).post('/admin/reset').status_code == 404` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.post(...)` sends an HTTP POST request.
  - `TestClient` from the installed package module `fastapi.testclient`.
  - `create_app` from the project's `scheduling_agent.interfaces.calendar_api` (Build the app around a calendar. `reset` enables POST /admin/reset, a demo and test aid that reseeds the data.).
  - `new_calendar` from the project's `tests.conftest`.
- Defines the function `test_the_http_client_speaks_the_same_contract_and_turns_error_bodies_back_into_domain_errors`.
- Its parameters:
    - `served`.
- Stores the value named `served` under the name `(calendar, api)`.
- Stores the result of calling `HttpCalendar` under the name `client`.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
- Stores the result of calling `free_start` under the name `start`.
  - `free_start`, a function of this file.
- Stores the result of calling `client.book` under the name `booked`.
  - The method `book` of `client`.
- Checks that `client.book(['alice', 'bob'], start, 30, 'client-key-001').replayed is True` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `book` of `client`.
- Checks that `client.get_event(booked.event.id).people == ('alice', 'bob')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `get_event` of `client`.
- Checks that `booked.event.key() in {e.key() for e in client.active_events()}` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `key` of the project's `Event` (What the end-state check compares: the people, the start and the length (not the generated id).).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `active_events` of `client`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 215 to 226:

```python
    assert client.cancel(booked.event.id, "client-key-002").event.cancelled
    assert (
        client.free_slots(["alice"], start.date(), start.date(), 30, not_after=datetime(2026, 1, 1, 12).time())[0].hour
        < 12
    )
    with pytest.raises(UnknownEvent):
        client.get_event("ev-9999")
    with pytest.raises(UnknownPerson):
        client.free_slots(["zed"], start.date(), start.date(), 30)
    with pytest.raises(InvalidSlot):
        client.book(["alice"], datetime(2026, 11, 7, 10), 30, "client-key-003")
    client.reset() if False else None
```

- Checks that `client.cancel(booked.event.id, 'client-key-002').event.cancelled` is true; if it is not, the test fails with an `AssertionError`.
  - The method `cancel` of `client`.
- Checks that `client.free_slots(['alice'], start.date(), start.date(), 30, not_after=dateti...` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `free_slots` of `client`.
  - The method `date` of `start`.
  - The method `time` of `datetime(2026, 1, 1, 12)`.
  - `datetime` from the standard library module `datetime`.
- A `with` block: it sets up `pytest.raises(UnknownEvent)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `get_event` of `client` with 1 argument(s); the result is not kept.
  - The method `get_event` of `client`.
- A `with` block: it sets up `pytest.raises(UnknownPerson)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `free_slots` of `client` with 4 argument(s); the result is not kept.
  - The method `free_slots` of `client`.
  - The method `date` of `start`.
- A `with` block: it sets up `pytest.raises(InvalidSlot)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `book` of `client` with 4 argument(s); the result is not kept.
  - The method `book` of `client`.
  - `datetime` from the standard library module `datetime`.
- Evaluates `client.reset() if False else None`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - The method `reset` of `client`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 229 to 238:

```python
def test_the_client_retries_a_dropped_connection_and_a_5xx_but_not_a_4xx():
    attempts = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise httpx.ConnectError("refused")
        if attempts["n"] == 2:
            return httpx.Response(503)
        return httpx.Response(200, json=[])
```

- Defines the function `test_the_client_retries_a_dropped_connection_and_a_5xx_but_not_a_4xx`.
- It takes no parameters.
- Stores a dictionary with 1 entry under the name `attempts`.
- Defines the function `flaky`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.
- Updates `attempts['n']` in place: `+=` applies `+` with the number `1` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `attempts['n'] == 1` is true.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `httpx.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx.ConnectError` from the installed package module `httpx`.
- Decision: the indented lines below run only when `attempts['n'] == 2` is true.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.
- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 240 to 252:

```python
    client = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(flaky)), "http://cal", attempts=3, sleep=lambda s: None
    )
    assert client.active_events() == []
    assert attempts["n"] == 3
    never = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))),
        "http://cal",
        attempts=2,
        sleep=lambda s: None,
    )
    with pytest.raises(CalendarError, match="HTTP 503"):
        never.active_events()
```

- Stores the result of calling `HttpCalendar` under the name `client`.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
  - `httpx.Client` makes an HTTP client.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.MockTransport` from the installed package module `httpx`.
- Checks that `client.active_events() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `active_events` of `client`.
- Checks that `attempts['n'] == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `HttpCalendar` under the name `never`.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
  - `httpx.Client` makes an HTTP client.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.MockTransport` from the installed package module `httpx`.
  - `httpx.Response` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(CalendarError, match='HTTP 503')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `active_events` of `never`; the result is not kept.
  - The method `active_events` of `never`.

`tests/unit/infrastructure/test_calendar_service.py`, lines 253 to 266:

```python
    bad = HttpCalendar(
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400, text="no"))), "http://cal", attempts=3
    )
    with pytest.raises(CalendarError, match="HTTP 400"):
        bad.active_events()


def test_init_creates_and_seeds_once_and_a_reset_restores_the_seed():
    db = connect(":memory:")
    init_calendar(db, REPO / "sql")
    first = db.execute("SELECT count(*) FROM events").fetchone()[0]
    init_calendar(db, REPO / "sql")
    assert db.execute("SELECT count(*) FROM events").fetchone()[0] == first
    db.execute("DELETE FROM idempotency_keys")
```

- Stores the result of calling `HttpCalendar` under the name `bad`.
  - `HttpCalendar` from the project's `scheduling_agent.infrastructure.calendar_client` (Talks to the calendar service. Every call is safe to repeat: reads are reads and writes carry their key.).
  - `httpx.Client` makes an HTTP client.
  - `httpx.MockTransport` from the installed package module `httpx`.
  - `lambda args: expression` is a small unnamed function written inline.
  - `httpx.Response` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(CalendarError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `active_events` of `bad`; the result is not kept.
  - The method `active_events` of `bad`.
- Defines the function `test_init_creates_and_seeds_once_and_a_reset_restores_the_seed`.
- It takes no parameters.
- Stores the result of calling `connect` under the name `db`.
  - `connect` from the project's `scheduling_agent.infrastructure.sqlite` (Open a database with the settings every store here relies on.).
- Calls `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.) with 2 argument(s); the result is not kept.
  - `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.).
  - `/` is divide.
- Stores the part of `db.execute('SELECT count(*)...` picked by `0` under the name `first`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.fetchone(...)` reads one row of a query result.
  - `.execute(...)` runs one SQL statement.
- Calls `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.) with 2 argument(s); the result is not kept.
  - `init_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Create the tables and load the seed if the database has no people yet.).
  - `/` is divide.
- Checks that `db.execute('SELECT count(*) FROM events').fetchone()[0] == first` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.fetchone(...)` reads one row of a query result.
  - `.execute(...)` runs one SQL statement.
- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.

`tests/unit/infrastructure/test_calendar_service.py`, lines 267 to 269:

```python
    db.execute("UPDATE events SET cancelled = 1")
    reset_calendar(db, REPO / "sql")
    assert db.execute("SELECT count(*) FROM events WHERE cancelled = 0").fetchone()[0] == first
```

- Calls `.execute(...)` runs one SQL statement with 1 argument(s); the result is not kept.
  - `.execute(...)` runs one SQL statement.
- Calls `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).) with 2 argument(s); the result is not kept.
  - `reset_calendar` from the project's `scheduling_agent.infrastructure.calendar_seed` (Delete every row and load the seed again (the demo and test aid behind POST /admin/reset).).
  - `/` is divide.
- Checks that `db.execute('SELECT count(*) FROM events WHERE cancelled = 0').fetchone()[0] =...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.fetchone(...)` reads one row of a query result.
  - `.execute(...)` runs one SQL statement.

### `tests/unit/infrastructure/test_openai_compatible.py`

102 non-blank lines; it defines `model`, `ok`, `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, `test_tool_specs_calls_and_results_use_the_function_calling_shape`, `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`, `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`, `test_a_length_finish_reason_is_kept`, `test_rate_limits_and_server_errors_are_transient`, `test_a_client_error_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_openai_compatible.py`, lines 1 to 14:

```python
import json
from typing import Any

import httpx
import pytest

from scheduling_agent.domain.errors import PermanentModelError, TransientModelError
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from scheduling_agent.infrastructure.openai_compatible import OpenAICompatibleChatModel
from tests.conftest import FixedClock


def model(handler, api_key=None):
    http = httpx.Client(transport=httpx.MockTransport(handler))
```

- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `scheduling_agent.domain.llm`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `scheduling_agent.infrastructure.openai_compatible`.
- Brings in `FixedClock` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.) from the project module `tests.conftest`.
- Defines the function `model`.
- Its parameters:
    - `handler`.
    - `api_key`; if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
  - `httpx.MockTransport` from the installed package module `httpx`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 15 to 21:

```python
    return OpenAICompatibleChatModel(http, "http://local/v1/", "small-model", FixedClock(), api_key)


def ok(content="hello", finish="stop", tool_calls=None, prompt_tokens=11, completion_tokens=3):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
```

- Ends the function and gives back the result of calling `OpenAICompatibleChatModel` to the caller.
  - `OpenAICompatibleChatModel` from the project's `scheduling_agent.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so; `monotonic` advances by `tick` on every call.).
- Defines the function `ok`.
- Its parameters:
    - `content`; if the caller leaves it out it is the text `hello`.
    - `finish`; if the caller leaves it out it is the text `stop`.
    - `tool_calls`; if the caller leaves it out it is nothing (`None`).
    - `prompt_tokens`; if the caller leaves it out it is the number `11`.
    - `completion_tokens`; if the caller leaves it out it is the number `3`.
- Stores a dictionary with 2 entries under the name `message`.
- Decision: the indented lines below run only when `tool_calls` is true.
- Stores the value named `tool_calls` under the name `message['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 22 to 35:

```python
    return httpx.Response(
        200,
        json={
            "model": "small-model-0",
            "choices": [{"message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        },
    )


def test_a_reply_becomes_text_usage_stop_reason_and_latency():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
```

- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_reply_becomes_text_usage_stop_reason_and_latency`.
- It takes no parameters.
- Declares `seen` as a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 36 to 49:

```python
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        return ok()  # type: ignore[no-any-return]

    response = model(handler, api_key="k").complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=50, temperature=0.7, top_p=0.9)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 11, 3)
    assert response.stop_reason is StopReason.END
    assert response.latency_seconds == 0.25
    assert response.model == "small-model-0"
    assert seen["url"] == "http://local/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
```

- Stores the result of calling `str` under the name `seen['url']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `str` turns a value into text.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `request.headers.get` under the name `seen['auth']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `ok` to the caller.
  - `ok`, a function of this file.
- Stores the result of calling `model(handler, api_key='k').complete` under the name `response`.
  - The method `complete` of `model(handler, api_key='k')`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.latency_seconds == 0.25` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.model == 'small-model-0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['url'] == 'http://local/v1/chat/completions'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['auth'] == 'Bearer k'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 50 to 63:

```python
    assert seen["body"]["messages"][0] == {"role": "system", "content": "be brief"}
    assert (seen["body"]["max_tokens"], seen["body"]["temperature"], seen["body"]["top_p"]) == (50, 0.7, 0.9)


def test_unset_sampling_is_left_out_of_the_body():
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),)))
    assert "temperature" not in body
    assert "top_p" not in body
    assert body["model"] == "small-model"


def test_a_schema_becomes_a_json_schema_response_format():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),), response_schema=schema))
```

- Checks that `seen['body']['messages'][0] == {'role': 'system', 'content': 'be brief'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `(seen['body']['max_tokens'], seen['body']['temperature'], seen['body']['top_p...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_unset_sampling_is_left_out_of_the_body`.
- It takes no parameters.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `'temperature' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'top_p' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `body['model'] == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_becomes_a_json_schema_response_format`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 64 to 77:

```python
    assert body["response_format"]["json_schema"]["schema"] == schema
    assert body["response_format"]["type"] == "json_schema"


def test_tool_specs_calls_and_results_use_the_function_calling_shape():
    spec = ToolSpec("lookup", "find one", {"type": "object"})
    history = (
        ChatMessage.user("find 4"),
        ChatMessage(Role.ASSISTANT, "", (ToolCall("c1", "lookup", {"id": 4}),)),
        ChatMessage(Role.TOOL, '{"ok": true}', tool_call_id="c1"),
    )
    body = model(lambda r: ok()).build_payload(ChatRequest(history, tools=(spec,)))
    assert body["tools"][0]["function"]["name"] == "lookup"
    assert body["messages"][1]["tool_calls"][0]["function"]["arguments"] == '{"id": 4}'
```

- Checks that `body['response_format']['json_schema']['schema'] == schema` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['response_format']['type'] == 'json_schema'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_specs_calls_and_results_use_the_function_calling_shape`.
- It takes no parameters.
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `scheduling_agent.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores a tuple of 3 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `scheduling_agent.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `body['tools'][0]['function']['name'] == 'lookup'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['messages'][1]['tool_calls'][0]['function']['arguments'] == '{"id": 4}'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 78 to 91:

```python
    assert body["messages"][2] == {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'}


def test_tool_calls_in_the_reply_are_parsed_with_json_arguments():
    calls = [{"id": "c9", "function": {"name": "lookup", "arguments": '{"id": 7}'}}]
    response = model(lambda r: ok(content=None, finish="stop", tool_calls=calls)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("c9", "lookup", {"id": 7}),)
    assert response.text == ""


def test_arguments_may_already_be_an_object_and_missing_ids_are_numbered():
```

- Checks that `body['messages'][2] == {'role': 'tool', 'tool_call_id': 'c1', 'content': '{"o...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`.
- It takes no parameters.
- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(content=None, finish='stop',...` under the name `response`.
  - The method `complete` of `model(lambda r: ok(content=None, fini...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('c9', 'lookup', {'id': 7}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `scheduling_agent.domain.llm` (A tool call the model asked for.).
- Checks that `response.text == ''` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 92 to 102:

```python
    calls = [{"function": {"name": "lookup", "arguments": {"id": 1}}}]
    response = model(lambda r: ok(tool_calls=calls)).complete(ChatRequest((ChatMessage.user("x"),)))
    assert response.tool_calls[0].id == "call_0"
    assert response.tool_calls[0].arguments == {"id": 1}


def test_a_length_finish_reason_is_kept():
    assert (
        model(lambda r: ok(finish="length")).complete(ChatRequest((ChatMessage.user("x"),))).stop_reason
        is StopReason.LENGTH
    )
```

- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(tool_calls=calls)).complete` under the name `response`.
  - The method `complete` of `model(lambda r: ok(tool_calls=calls))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.tool_calls[0].id == 'call_0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `response.tool_calls[0].arguments == {'id': 1}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_length_finish_reason_is_kept`.
- It takes no parameters.
- Checks that `model(lambda r: ok(finish='length')).complete(ChatRequest((ChatMessage.user('...` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `complete` of `model(lambda r: ok(finish='length'))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 105 to 116:

```python
@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError, match=str(status)):
        model(lambda r: httpx.Response(status)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_client_error_is_permanent():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        model(lambda r: httpx.Response(400, text="bad")).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_dropped_connection_is_transient():
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match=str(status))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `str` turns a value into text.
- Calls the method `complete` of `model(lambda r: httpx.Response(status))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(status))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_client_error_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(400, t...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(400, t...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 117 to 129:

```python
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        model(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_an_unexpected_shape_is_permanent():
    with pytest.raises(PermanentModelError, match="unexpected response shape"):
        model(lambda r: httpx.Response(200, json={"choices": []})).complete(ChatRequest((ChatMessage.user("x"),)))
    bad_args = [{"id": "c", "function": {"name": "t", "arguments": "[1]"}}]
    with pytest.raises(PermanentModelError):
        model(lambda r: ok(tool_calls=bad_args)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.
- Raises an error: the result of calling `httpx.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx.ConnectError` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match='ConnectError')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(handler)`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_an_unexpected_shape_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='unexpected resp...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(200, j...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(200, j...`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Stores a list of 1 item(s) under the name `bad_args`.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: ok(tool_calls=bad_args))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: ok(tool_calls=bad_args))`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 132 to 135:

```python
def test_the_model_reports_its_name_and_that_it_accepts_sampling():
    adapter = model(lambda r: ok())
    assert adapter.name == "small-model"
    assert adapter.supports_sampling
```

- Defines the function `test_the_model_reports_its_name_and_that_it_accepts_sampling`.
- It takes no parameters.
- Stores the result of calling `model` under the name `adapter`.
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `adapter.name == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `adapter.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

### `tests/unit/infrastructure/test_recording.py`

45 non-blank lines; it defines `request`, `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`, `test_a_folder_of_recordings_is_loaded_as_one_store`, `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.

`tests/unit/infrastructure/test_recording.py`, lines 1 to 12:

```python
import json

import pytest

from scheduling_agent.domain.errors import RecordingMissing
from scheduling_agent.domain.llm import ChatMessage, ChatRequest
from scheduling_agent.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from tests.conftest import ScriptedModel


def request(text="hi", tag="a"):
    return ChatRequest((ChatMessage.user(text),), max_output_tokens=10, tag=tag)
```

- Makes the module `json` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `scheduling_agent.domain.llm`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `scheduling_agent.infrastructure.recording`.
- Brings in `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Defines the function `request`.
- Its parameters:
    - `text`; if the caller leaves it out it is the text `hi`.
    - `tag`; if the caller leaves it out it is the text `a`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.

`tests/unit/infrastructure/test_recording.py`, lines 15 to 26:

```python
def test_recording_then_replaying_returns_the_same_response(tmp_path):
    path = tmp_path / "r.jsonl"
    live = ScriptedModel(lambda r: ("live answer", 12, 4))
    recorder = RecordingChatModel(live, RecordingStore(path), {"provider": "test"})
    first = recorder.complete(request())
    replay = RecordedChatModel(RecordingStore(path))
    assert replay.complete(request()) == first
    assert len(live.requests) == 1


def test_a_request_already_recorded_is_not_sent_again(tmp_path):
    live = ScriptedModel()
```

- Defines the function `test_recording_then_replaying_returns_the_same_response`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `recorder.complete` under the name `first`.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `scheduling_agent.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Checks that `replay.complete(request()) == first` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_request_already_recorded_is_not_sent_again`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).

`tests/unit/infrastructure/test_recording.py`, lines 27 to 38:

```python
    recorder = RecordingChatModel(live, RecordingStore(tmp_path / "r.jsonl"), {})
    recorder.complete(request())
    recorder.complete(request())
    assert len(live.requests) == 1


def test_an_unrecorded_request_names_the_tag_and_the_fix(tmp_path):
    replay = RecordedChatModel(RecordingStore(tmp_path / "missing.jsonl"))
    with pytest.raises(RecordingMissing, match=r"tag='zzz'.*make record"):
        replay.complete(request(tag="zzz"))
    assert replay.name == "recorded"
    assert replay.supports_sampling
```

- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_an_unrecorded_request_names_the_tag_and_the_fix`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `scheduling_agent.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- A `with` block: it sets up `pytest.raises(RecordingMissing, match="tag='zzz'.*make re...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `replay` with 1 argument(s); the result is not kept.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `replay.name == 'recorded'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `replay.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_recording.py`, lines 41 to 52:

```python
def test_the_note_about_what_produced_the_answer_is_kept_in_the_file(tmp_path):
    path = tmp_path / "r.jsonl"
    RecordingChatModel(ScriptedModel(), RecordingStore(path), {"provider": "test"}).complete(request())
    entry = json.loads(path.read_text().splitlines()[0])
    assert entry["recorded_with"] == {"provider": "test", "model": "scripted"}
    assert entry["tag"] == "a"


def test_a_folder_of_recordings_is_loaded_as_one_store(tmp_path):
    for name, text in (("one.jsonl", "q1"), ("two.jsonl", "q2")):
        RecordingChatModel(ScriptedModel(), RecordingStore(tmp_path / name), {}).complete(request(text))
    store = RecordingStore(tmp_path)
```

- Defines the function `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Checks that `entry['recorded_with'] == {'provider': 'test', 'model': 'scripted'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `entry['tag'] == 'a'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_folder_of_recordings_is_loaded_as_one_store`.
- Its parameters:
    - `tmp_path`.
- Loop: the indented lines below run once for each item of `(('one.jsonl', 'q1'), ('two.jsonl', 'q2'))`; `(name, text)` names the current item.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Stores the result of calling `RecordingStore` under the name `store`.
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).

`tests/unit/infrastructure/test_recording.py`, lines 53 to 61:

```python
    assert len(store) == 2
    RecordedChatModel(store).complete(request("q1"))
    RecordedChatModel(store).complete(request("q2"))


def test_the_recorder_reports_the_wrapped_models_name_and_sampling_support(tmp_path):
    recorder = RecordingChatModel(ScriptedModel(sampling=False), RecordingStore(tmp_path / "r.jsonl"), {})
    assert recorder.name == "scripted"
    assert not recorder.supports_sampling
```

- Checks that `len(store) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `scheduling_agent.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `scheduling_agent.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Defines the function `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `scheduling_agent.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `scheduling_agent.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Checks that `recorder.name == 'scripted'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `not recorder.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

### `tests/unit/infrastructure/test_resilience_logging_factory.py`

134 non-blank lines; it defines `Flaky`, `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, `test_retry_needs_at_least_one_attempt_and_caps_the_delay`, `test_log_lines_are_logfmt_with_fields_and_quote_spaces`, `test_an_exception_is_logged_on_the_same_line`, `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`, `test_the_system_clock_moves_forward`, `test_the_recorded_provider_replays_the_fixtures`, `test_the_local_provider_builds_a_retrying_openai_compatible_model`, `test_record_mode_wraps_a_live_model_in_a_recorder`, ....

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 1 to 14:

```python
import io
import logging
import random
import signal

import pytest

from scheduling_agent.domain.errors import PermanentModelError, TransientModelError
from scheduling_agent.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, Usage
from scheduling_agent.infrastructure.clock import SystemClock
from scheduling_agent.infrastructure.env import ConfigurationError
from scheduling_agent.infrastructure.logging import configure_logging, fields
from scheduling_agent.infrastructure.model_factory import ModelSettings, build_chat_model
from scheduling_agent.infrastructure.recording import RecordedChatModel, RecordingChatModel
```

- Makes the module `io` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `scheduling_agent.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `scheduling_agent.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `scheduling_agent.infrastructure.clock`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `scheduling_agent.infrastructure.env`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.), `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `scheduling_agent.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `scheduling_agent.infrastructure.model_factory`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.) from the project module `scheduling_agent.infrastructure.recording`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 15 to 28:

```python
from scheduling_agent.infrastructure.resilient import RetryingChatModel
from scheduling_agent.infrastructure.retry import retry
from scheduling_agent.infrastructure.shutdown import ShutdownSignal

REQUEST = ChatRequest((ChatMessage.user("hi"),), tag="r")


class Flaky:
    name = "flaky"
    supports_sampling = True

    def __init__(self, failures, error=TransientModelError):
        self.calls = 0
        self._failures = failures
```

- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `scheduling_agent.infrastructure.resilient`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `scheduling_agent.infrastructure.retry`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `scheduling_agent.infrastructure.shutdown`.
- Stores the result of calling `ChatRequest` under the name `REQUEST`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the class `Flaky`.
- Stores the text `flaky` under the name `name`.
- Stores the value `True` under the name `supports_sampling`.
- Defines the method `__init__`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `failures`.
    - `error`; if the caller leaves it out it is the value named `TransientModelError`.
- Stores the number `0` under the name `self.calls` (as an attribute of this object, so other methods can use it).
- Stores the value named `failures` under the name `self._failures` (as an attribute of this object, so other methods can use it).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 29 to 42:

```python
        self._error = error

    def complete(self, request):
        self.calls += 1
        if self.calls <= self._failures:
            raise self._error("boom")
        return ChatResponse("ok", StopReason.END, Usage(1, 1), 0.1, "flaky")


def test_a_transient_failure_is_retried_with_backoff_and_then_succeeds():
    pauses: list[float] = []
    flaky = Flaky(2)
    model = RetryingChatModel(flaky, attempts=3, base_delay_seconds=1.0, sleep=pauses.append, rng=random.Random(1))
    assert model.complete(REQUEST).text == "ok"
```

- Stores the value named `error` under the name `self._error` (as an attribute of this object, so other methods can use it).
- Defines the method `complete`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request`.
- Updates `self.calls` in place: `+=` applies `+` with the number `1` and stores the result back.
- Decision: the indented lines below run only when `self.calls <= self._failures` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `self._error`. Execution jumps out to the nearest matching `except`.
  - The method `_error` of `self`.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `scheduling_agent.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `scheduling_agent.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the function `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`.
- It takes no parameters.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `RetryingChatModel` under the name `model`.
  - `RetryingChatModel` from the project's `scheduling_agent.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Checks that `model.complete(REQUEST).text == 'ok'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `model`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 43 to 54:

```python
    assert flaky.calls == 3
    assert 0.5 <= pauses[0] <= 1.0
    assert 1.0 <= pauses[1] <= 2.0
    assert model.name == "flaky"
    assert model.supports_sampling


def test_the_last_transient_failure_is_raised_after_the_attempts_run_out():
    flaky = Flaky(9)
    with pytest.raises(TransientModelError):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 2
```

- Checks that `flaky.calls == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `0.5 <= pauses[0] <= 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `1.0 <= pauses[1] <= 2.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `model.name == 'flaky'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
- Defines the function `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `scheduling_agent.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 57 to 67:

```python
def test_a_permanent_failure_is_not_retried():
    flaky = Flaky(9, PermanentModelError)
    with pytest.raises(PermanentModelError):
        RetryingChatModel(flaky, attempts=5, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 1


def test_retry_needs_at_least_one_attempt_and_caps_the_delay():
    with pytest.raises(ValueError, match=r"at least 1"):
        retry(lambda: 1, attempts=0, base_delay_seconds=1, retry_on=(ValueError,))
    pauses: list[float] = []
```

- Defines the function `test_a_permanent_failure_is_not_retried`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=5, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=5, ...`.
  - `RetryingChatModel` from the project's `scheduling_agent.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_retry_needs_at_least_one_attempt_and_caps_the_delay`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(ValueError, match='at least 1')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 4 argument(s); the result is not kept.
  - `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 69 to 81:

```python
    def fail() -> int:
        raise ValueError

    with pytest.raises(ValueError, match=r"^$"):
        retry(fail, attempts=6, base_delay_seconds=4, retry_on=(ValueError,), sleep=pauses.append, max_delay_seconds=5)
    assert max(pauses) <= 5


def test_log_lines_are_logfmt_with_fields_and_quote_spaces():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("t").info("two words", extra=fields(count=3, note="a b", empty=""))
    line = stream.getvalue().strip()
```

- Defines the function `fail`. It returns a whole number.
- It takes no parameters.
- Raises an error: the value named `ValueError`. Execution jumps out to the nearest matching `except`.
- A `with` block: it sets up `pytest.raises(ValueError, match='^$')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 6 argument(s); the result is not kept.
  - `retry` from the project's `scheduling_agent.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
- Checks that `max(pauses) <= 5` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `max` picks the largest value.
- Defines the function `test_log_lines_are_logfmt_with_fields_and_quote_spaces`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Calls the method `info` of `logging.getLogger('t')` with 2 argument(s); the result is not kept.
  - The method `info` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.
  - `fields` from the project's `scheduling_agent.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
- Stores the result of calling `stream.getvalue().strip` under the name `line`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - The method `getvalue` of `stream`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 82 to 95:

```python
    assert 'msg="two words"' in line
    assert "count=3" in line
    assert 'note="a b"' in line
    assert 'empty=""' in line
    assert line.startswith("ts=")


def test_an_exception_is_logged_on_the_same_line():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    try:
        raise RuntimeError("bad")
    except RuntimeError:
        logging.getLogger("t").exception("failed")
```

- Checks that `'msg="two words"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'count=3' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'note="a b"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'empty=""' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `line.startswith('ts=')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
- Defines the function `test_an_exception_is_logged_on_the_same_line`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `scheduling_agent.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Raises an error: the result of calling `RuntimeError`. Execution jumps out to the nearest matching `except`.
  - `RuntimeError` a general error raised while running.
- `except` handler: it runs when the `try` block raised `RuntimeError`.
- Calls the method `exception` of `logging.getLogger('t')` with 1 argument(s); the result is not kept.
  - The method `exception` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 96 to 109:

```python
    assert "exc=" in stream.getvalue()


def test_shutdown_flag_is_set_by_a_request_and_by_a_signal():
    shutdown = ShutdownSignal()
    assert not shutdown.requested
    shutdown.install()
    signal.raise_signal(signal.SIGTERM)
    assert shutdown.requested
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    other = ShutdownSignal()
    other.request()
    assert other.requested
```

- Checks that `'exc=' in stream.getvalue()` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `getvalue` of `stream`.
- Defines the function `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`.
- It takes no parameters.
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `scheduling_agent.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Checks that `not shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Calls `signal.raise_signal` from the standard library module `signal` with 1 argument(s); the result is not kept.
  - `signal.raise_signal` from the standard library module `signal`.
- Checks that `shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Stores the result of calling `ShutdownSignal` under the name `other`.
  - `ShutdownSignal` from the project's `scheduling_agent.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `request` of `other`; the result is not kept.
  - The method `request` of `other`.
- Checks that `other.requested` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 112 to 123:

```python
def test_the_system_clock_moves_forward():
    clock = SystemClock()
    assert clock.monotonic() <= clock.monotonic()
    assert clock.now().date() == clock.today()


def test_the_recorded_provider_replays_the_fixtures(tmp_path):
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "recorded", "RECORDINGS_PATH": str(tmp_path)})
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)


def test_the_local_provider_builds_a_retrying_openai_compatible_model():
```

- Defines the function `test_the_system_clock_moves_forward`.
- It takes no parameters.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `clock.monotonic() <= clock.monotonic()` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - The method `monotonic` of `clock`.
- Checks that `clock.now().date() == clock.today()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `date` of `clock.now()`.
  - The method `today` of `clock`.
  - The method `now` of `clock`.
- Defines the function `test_the_recorded_provider_replays_the_fixtures`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_local_provider_builds_a_retrying_openai_compatible_model`.
- It takes no parameters.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 124 to 135:

```python
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"})
    model = build_chat_model(settings, SystemClock(), {})
    assert isinstance(model, RetryingChatModel)
    assert model.name == "qwen2.5:1.5b"
    assert settings.openai_base_url == "http://localhost:11434/v1"


def test_record_mode_wraps_a_live_model_in_a_recorder(tmp_path):
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "openai-compatible", "RECORD": "on", "RECORDINGS_PATH": str(tmp_path / "r.jsonl")}
    )
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)
```

- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `model.name == 'qwen2.5:1.5b'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.openai_base_url == 'http://localhost:11434/v1'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_record_mode_wraps_a_live_model_in_a_recorder`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
  - `/` is divide.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 138 to 149:

```python
def test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"})
    assert settings.model == "claude-haiku-5-5"
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings, SystemClock(), {})


def test_the_anthropic_provider_builds_when_a_key_is_present():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic", "ANTHROPIC_THINKING": "omit"})
    model = build_chat_model(settings, SystemClock(), {"ANTHROPIC_API_KEY": "present-but-not-real"})
    assert isinstance(model, RetryingChatModel)
    assert not model.supports_sampling
```

- Defines the function `test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Checks that `settings.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match='ANTHROPIC_API_KEY')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) with 3 argument(s); the result is not kept.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_anthropic_provider_builds_when_a_key_is_present`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `scheduling_agent.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `scheduling_agent.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 152 to 163:

```python
@pytest.mark.parametrize(
    "environ",
    [
        {"MODEL_PROVIDER": "carrier-pigeon"},
        {"RECORD": "maybe"},
        {"MODEL_ATTEMPTS": "0"},
        {"MODEL_TIMEOUT_SECONDS": "0"},
    ],
)
def test_bad_model_settings_name_the_variable(environ):
    with pytest.raises(ConfigurationError, match=next(iter(environ))):
        ModelSettings.from_env(environ)
```

- Defines the function `test_bad_model_settings_name_the_variable`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `environ`.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match=next(iter(environ)))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `next` takes the next item from an iterator.
  - `iter` makes an iterator over a collection.
- Calls the method `from_env` of `ModelSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `ModelSettings`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 166 to 173:

```python
def test_info_logs_of_a_failed_call_never_carry_the_prompt_text(caplog):
    flaky = Flaky(1)
    secret = ChatRequest((ChatMessage.user("my card number is 4111"),), tag="p1/t0/0")
    with caplog.at_level(logging.INFO):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(secret)
    assert caplog.records
    assert "4111" not in caplog.text
    assert "4111" not in " ".join(str(r.__dict__.get("fields", "")) for r in caplog.records)
```

- Defines the function `test_info_logs_of_a_failed_call_never_carry_the_prompt_text`.
- Its parameters:
    - `caplog`.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `ChatRequest` under the name `secret`.
  - `ChatRequest` from the project's `scheduling_agent.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `scheduling_agent.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `caplog.records` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `'4111' not in caplog.text` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'4111' not in ' '.join((str(r.__dict__.get('fields', '')) for r in caplog.rec...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/unit --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/infrastructure/test_resilience_logging_factory.py::test_info_logs_of_a_failed_call_never_carry_the_prompt_text

154 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/unit -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/unit/application/test_memory_and_task_runner.py::test_a_statement_that_is_not_a_calendar_fact_is_not_kept_and_a_person_can_be_forgotten
tests/unit/application/test_memory_and_task_runner.py::test_recall_returns_only_the_facts_of_the_people_the_task_names_best_three_first
tests/unit/application/test_memory_and_task_runner.py::test_the_expected_writes_approver_approves_exactly_the_changes_a_task_expects
tests/unit/application/test_memory_and_task_runner.py::test_the_task_file_has_the_lessons_mix_and_each_expected_state_is_what_the_calendar_search_finds
tests/unit/application/test_memory_and_task_runner.py::test_all_thirty_tasks_reach_their_expected_end_state_with_no_write_lacking_an_approval
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/unit/infrastructure/test_anthropic_chat.py` test?

   *Answer:* It holds the tests for `anthropic chat`.

2. What does `tests/unit/infrastructure/test_calendar_service.py` test?

   *Answer:* It holds the tests for `calendar service`.

3. What does `tests/unit/infrastructure/test_openai_compatible.py` test?

   *Answer:* It holds the tests for `openai compatible`.

4. What does `tests/unit/infrastructure/test_recording.py` test?

   *Answer:* It holds the tests for `recording`.

5. What does `tests/unit/infrastructure/test_resilience_logging_factory.py` test?

   *Answer:* It holds the tests for `resilience logging factory`.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).
