-- DDL for the sample calendar service (SQLite). Run order: 001_schema.sql, 002_seed.sql, 003_queries.sql.
-- `make db` creates out/calendar.db from the first two.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS people (
    name         TEXT PRIMARY KEY,                     -- lowercase first name, the id used in every call
    display_name TEXT NOT NULL
);

-- An event never disappears: a cancelled event keeps its row (cancelled = 1) and stops blocking anyone's time.
CREATE TABLE IF NOT EXISTS events (
    id         TEXT PRIMARY KEY,                       -- ev-0001, ev-0002, ...
    start      TEXT NOT NULL,                          -- local time, YYYY-MM-DDTHH:MM
    minutes    INTEGER NOT NULL CHECK (minutes BETWEEN 30 AND 240 AND minutes % 30 = 0),
    cancelled  INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_people (
    event_id TEXT NOT NULL REFERENCES events (id),
    person   TEXT NOT NULL REFERENCES people (name),
    PRIMARY KEY (event_id, person)
);
CREATE INDEX IF NOT EXISTS event_people_person_idx ON event_people (person);
CREATE INDEX IF NOT EXISTS events_start_idx ON events (start);

-- One row per Idempotency-Key. The write it protects and this row are committed in one transaction, so a key is never
-- "seen" without its write, and a retry returns the first result without touching events at all.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key          TEXT PRIMARY KEY,
    operation    TEXT NOT NULL CHECK (operation IN ('book', 'cancel')),
    request_hash TEXT NOT NULL,                        -- the same key with a different request is a conflict
    event_id     TEXT NOT NULL REFERENCES events (id),
    created_at   TEXT NOT NULL
);
