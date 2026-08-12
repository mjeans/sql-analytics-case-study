SELECT
    'duplicate_site_key' AS check_name,
    COUNT(*) AS failed_rows
FROM (
    SELECT site_id
    FROM sites
    GROUP BY site_id
    HAVING COUNT(*) > 1
)

UNION ALL

SELECT
    'duplicate_member_key',
    COUNT(*)
FROM (
    SELECT member_id
    FROM members
    GROUP BY member_id
    HAVING COUNT(*) > 1
)

UNION ALL

SELECT
    'orphan_service_member',
    COUNT(*)
FROM service_events
LEFT JOIN members
    ON service_events.member_id = members.member_id
WHERE members.member_id IS NULL

UNION ALL

SELECT
    'orphan_ticket_member',
    COUNT(*)
FROM support_tickets
LEFT JOIN members
    ON support_tickets.member_id = members.member_id
WHERE members.member_id IS NULL

UNION ALL

SELECT
    'service_before_signup',
    COUNT(*)
FROM service_events
INNER JOIN members
    ON service_events.member_id = members.member_id
WHERE service_events.event_date < members.signup_date

UNION ALL

SELECT
    'invalid_completed_duration',
    COUNT(*)
FROM service_events
WHERE
    completed = 1
    AND (
        duration_minutes IS NULL
        OR duration_minutes NOT BETWEEN 10 AND 180
    );
