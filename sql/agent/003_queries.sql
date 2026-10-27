-- The queries the lesson's checks run against the agent's own database.

-- 1. Unfinished runs: what `agent resume` would pick up after a crash.
SELECT run_id, status, steps, task FROM runs WHERE status IN ('running', 'awaiting_approval');

-- 2. Pending approvals: what a person still has to decide.
SELECT id, run_id, step, proposal_json FROM approvals WHERE status = 'pending' ORDER BY created_at;

-- 3. No write without an approval: every 'written' line must have an approved approval. Must return no rows.
SELECT l.run_id, l.step, l.action FROM audit_log l
LEFT JOIN approvals a ON a.id = l.approval_id AND a.status = 'approved'
WHERE l.outcome = 'written' AND a.id IS NULL;

-- 4. Refusals: writes that were proposed and not (yet) allowed.
SELECT run_id, step, action, detail FROM audit_log WHERE outcome = 'refused' ORDER BY id;

-- 5. What the agent remembers, per person.
SELECT person, topic, value, text, stated_on, expires_on FROM memory_facts ORDER BY person, topic;
