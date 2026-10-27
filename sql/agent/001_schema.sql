-- DDL for the agent's own state (SQLite): saved runs, approvals, the audit log and long-term memory.
-- `make db` creates out/agent.db from it.

PRAGMA foreign_keys = ON;

-- The whole state of a run after its latest step (messages, pending write, counters), written in one transaction with
-- the step row below. A run with status running or awaiting_approval is resumed from here after a crash.
CREATE TABLE IF NOT EXISTS runs (
    run_id     TEXT PRIMARY KEY,
    task       TEXT NOT NULL,
    session    TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('running', 'awaiting_approval', 'done', 'stopped', 'failed')),
    steps      INTEGER NOT NULL,
    tokens     INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_steps (
    run_id              TEXT NOT NULL REFERENCES runs (run_id),
    step                INTEGER NOT NULL,
    status              TEXT NOT NULL,
    pending_approval_id TEXT,
    saved_at            TEXT NOT NULL,
    PRIMARY KEY (run_id, step)
);

-- A write is a proposal until a person decides. One approval per run and step: asking twice returns the same row.
CREATE TABLE IF NOT EXISTS approvals (
    id            TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL,
    step          INTEGER NOT NULL,
    proposal_json TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at    TEXT NOT NULL,
    decided_at    TEXT,
    decided_by    TEXT,
    UNIQUE (run_id, step)
);

-- Append-only. A replayed write after a crash writes the same line again; the unique key keeps it once.
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    at          TEXT NOT NULL,
    run_id      TEXT NOT NULL,
    step        INTEGER NOT NULL,
    action      TEXT NOT NULL,
    outcome     TEXT NOT NULL CHECK (outcome IN ('refused', 'written', 'failed', 'rejected')),
    approval_id TEXT,
    detail      TEXT NOT NULL,
    UNIQUE (run_id, step, action, outcome)
);

-- Facts a person stated about themselves: one row per person and topic, so a changed preference replaces the old one.
CREATE TABLE IF NOT EXISTS memory_facts (
    person     TEXT NOT NULL,
    topic      TEXT NOT NULL,                          -- earliest_start, latest_end or day:<weekday number>
    kind       TEXT NOT NULL,
    value      TEXT NOT NULL,
    text       TEXT NOT NULL,
    session    TEXT NOT NULL,
    stated_on  TEXT NOT NULL,
    expires_on TEXT,
    PRIMARY KEY (person, topic)
);
