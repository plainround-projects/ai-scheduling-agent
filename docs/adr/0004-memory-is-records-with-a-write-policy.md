# 0004. Memory is records with a write policy, not a growing transcript

Date: 2026-10-27. Status: accepted.

## Context

A transcript grows without bound and turns "did this preference change" into a search problem. The lesson asks for facts a person states about themselves, applied later, with the old version gone after a change.

## Decision

A fact is (person, kind, value, the sentence, session, stated date, expiry). Only sentences that state a usable constraint on the person's own calendar are kept (earliest start, latest end, a day to avoid, or a day that is fine again); anything else is not stored. There is one fact per person and topic: a new fact replaces the old one in storage, "Fridays are fine again" retracts the avoid-day fact, lapsed facts are dropped on write and never recalled. Recall considers the facts of the people the task names, scores each as `0.7 * cosine similarity + 0.3 * recency` (half-life 180 days) and returns the best three. `forget` deletes a person's facts from storage.

## Consequences

- A changed preference leaves no trace of the old value in recall or in storage; the tests check the table.
- Parsing is by rules for four sentence shapes. A model-based extractor would cover more shapes and would need its own evaluation.
- The recalled facts are shown to the model in its first message, with who said them and when.
