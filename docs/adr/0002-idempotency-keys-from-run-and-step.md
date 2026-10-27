# 0002. Idempotency keys are built from the run id and the step, and committed with the write

Date: 2026-10-27. Status: accepted.

## Context

A crash between a booking and the note that it happened makes a resumed run send the booking again. The prompt cannot prevent that; the write path can.

## Decision

The key of a write is `sha256("<run id>:<step>")`; a move gets `:cancel` and `:book` suffixes for its two calls. Nothing random, no clock. The calendar stores the key, a hash of the request and the resulting event id in the same SQLite transaction as the write. A repeated key with the same request returns the first result with `replayed: true` and touches nothing; the same key with a different request is a conflict (409); a failed write stores no key, so its retry can succeed. The check is by key, never by comparing people, time and length, because two real bookings can have identical content.

## Consequences

- A resumed step sends exactly the key it sent before the crash.
- Parallel requests with one key create one event; parallel requests for one slot with different keys let one win and answer the other with a conflict (tested with threads and over HTTP).
- The key has no expiry in this build; a production store would keep keys for the longest retry window.
