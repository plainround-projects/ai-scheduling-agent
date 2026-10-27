# 0006. A deterministic stand-in for the model drives the offline runs

Date: 2026-10-27. Status: accepted.

## Context

The properties this project proves (a write needs a yes, a crash cannot double-book, a budget stops a loop, memory is applied) belong to the harness around the model. A real small model's tool calling is the least repeatable part of the system, and no model key is available while the repository is built.

## Decision

`ScriptedPolicyModel` implements the `ChatModel` port and speaks the same tool-calling protocol. It parses the task and the recalled facts out of the conversation and decides the next tool call from the tool results so far: search, then propose, then report; move and cancel read the event first; an unknown person ends the run with no write; a task marked "Do not give up" keeps searching later weeks until the step cap stops it. It is selected by `MODEL_PROVIDER=scripted` (the default). The local and Claude adapters are real and are exercised by an opt-in live test that checks the model answers in the protocol the agent expects.

## Consequences

- The 30 tasks run in seconds and give the same result every time, so the end-state check and the crash tests are exact.
- The result "30 of 30" says the harness is right. It says nothing about how well any language model schedules; `make test-live` and a task run with `MODEL_PROVIDER` set to a real model measure that.
- The stand-in is in `infrastructure`, labelled as not a language model, and never imported by `domain` or `application`.
