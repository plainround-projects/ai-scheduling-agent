-- The queries the service and the lesson's checks run, each with a line on what it shows.

-- 1. Active events per person: what each person's week looks like.
SELECT ep.person, count(*) AS meetings, sum(e.minutes) AS minutes
FROM events e JOIN event_people ep ON ep.event_id = e.id
WHERE e.cancelled = 0 GROUP BY ep.person ORDER BY ep.person;

-- 2. Double bookings: two active events that overlap for the same person. Must return no rows.
SELECT a.id, b.id, pa.person
FROM events a
JOIN events b ON a.id < b.id AND a.cancelled = 0 AND b.cancelled = 0
 AND a.start < strftime('%Y-%m-%dT%H:%M', b.start, '+' || b.minutes || ' minutes')
 AND b.start < strftime('%Y-%m-%dT%H:%M', a.start, '+' || a.minutes || ' minutes')
JOIN event_people pa ON pa.event_id = a.id
JOIN event_people pb ON pb.event_id = b.id AND pb.person = pa.person;

-- 3. Replays: how many writes were answered from an idempotency key instead of being applied twice.
SELECT operation, count(*) AS keys FROM idempotency_keys GROUP BY operation;

-- 4. Events that were created by an agent run (their keys are 64 hex characters, built from run id and step).
SELECT e.id, e.start, e.minutes, k.key
FROM events e JOIN idempotency_keys k ON k.event_id = e.id AND k.operation = 'book'
ORDER BY e.id;

-- 5. Cancelled events and when their cancellation was recorded.
SELECT e.id, e.start, k.created_at AS cancelled_at
FROM events e JOIN idempotency_keys k ON k.event_id = e.id AND k.operation = 'cancel'
WHERE e.cancelled = 1 ORDER BY e.id;
