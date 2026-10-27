# 0005. Step, token and time caps are separate and say which one fired

Date: 2026-10-27. Status: accepted.

## Context

One "limit" hides which resource a task exhausts. A task that blows its tokens before its steps tells you the constraint is spend; a task that stops at the step cap tells you it is looping.

## Decision

`Budget` holds three counters and checks each before every model call (not only at the top of a loop): steps (default 12), tokens (4,000) and wall-clock seconds (30). `BudgetExceeded` carries the name of the cap. The run is saved as `stopped` with that cap in `stop_reason` and a final text of the form "Stopped: step cap reached: 12/12. Done so far: 12 step(s), no write was made. Not done: the task was not completed."

## Consequences

- The unsolvable task in the set stops at `steps` having spent 1,572 tokens, well under the 4,000-token cap, as the lesson describes (the lesson's own run spent 1,440).
- The caps are settings (`MAX_STEPS`, `MAX_TOKENS`, `MAX_SECONDS`).
- A single slow tool call between checks can overshoot the time cap by its own duration; the HTTP client's timeout bounds it.
