# 0001. Every write is a proposal, and an approval is bound to its exact content

Date: 2026-10-27. Status: accepted.

## Context

The agent can change other people's calendars. A model can be wrong, can be talked into things, and can repeat a call. The only safe default is that nothing changes until a person says yes, and that the yes is for the change that will happen.

## Decision

The three write tools never act. A write tool call is turned into a `Proposal` (action plus exact arguments, with a snapshot of the event for a move or a cancel). The proposal is stored as a pending approval for (run, step), an audit line `refused` is written, and the run stops in `awaiting_approval`. A person decides with `agent approve` or `agent reject`. Only an approved approval whose proposal digest equals the digest of the proposal about to run opens the write. A missing, pending, rejected, unknown or mismatched approval gives no write and one audit line saying why.

## Consequences

- An approval granted for 9 am cannot be spent on 10 am, and a rejected proposal is reported to the model as rejected.
- The unit of review is a sentence-sized proposal, not a transcript.
- The audit log can be checked by a query: every `written` line has an approved approval (`sql/agent/003_queries.sql`, query 3).
- The model never needs to know an approval id; the harness carries it.
