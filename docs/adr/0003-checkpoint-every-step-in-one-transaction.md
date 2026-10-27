# 0003. Save the run after every step, in one transaction

Date: 2026-10-27. Status: accepted.

## Context

A process can die at any line. The run must be resumable from somewhere that is always consistent: not between "messages saved" and "pending write saved".

## Decision

`CheckpointStore.save` writes the run row (status, counters, the whole state as JSON including the messages and the pending write) and a `run_steps` row in one `BEGIN IMMEDIATE` transaction. The agent saves after creating the run, after every tool turn, after recording a proposal, after settling a pending write and when the run ends or is stopped. `resume` loads the last state and continues: a pending write is settled first (wait, reject, or execute with the stable key), then the loop goes on. Wall-clock time is per attempt; steps and tokens accumulate across resumes.

## Consequences

- The window in which a crash loses work is one model call or one calendar call, both of which are safe to repeat (the model call is paid again; the calendar call is keyed).
- The state is a JSON document: simple to inspect, not queryable by message. The queries in `sql/agent/003_queries.sql` use the columns.
- `agent unfinished` lists what a crash left behind.
