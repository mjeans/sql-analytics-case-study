DROP VIEW IF EXISTS site_monthly_metrics;
DROP VIEW IF EXISTS calendar_months;
DROP VIEW IF EXISTS member_activity_metrics;

CREATE VIEW member_activity_metrics AS
SELECT
    members.member_id,
    members.site_id,
    members.signup_date,
    members.acquisition_channel,
    members.age_band,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM service_events
            WHERE
                service_events.member_id = members.member_id
                AND service_events.completed = 1
                AND service_events.event_date BETWEEN
                    members.signup_date
                    AND date(members.signup_date, '+14 days')
        )
        THEN 1
        ELSE 0
    END AS activated_14d,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM service_events
            WHERE
                service_events.member_id = members.member_id
                AND service_events.completed = 1
                AND service_events.event_date BETWEEN
                    members.signup_date
                    AND date(members.signup_date, '+14 days')
        )
        AND EXISTS (
            SELECT 1
            FROM service_events
            WHERE
                service_events.member_id = members.member_id
                AND service_events.completed = 1
                AND service_events.event_date BETWEEN
                    date(members.signup_date, '+15 days')
                    AND date(members.signup_date, '+45 days')
        )
        THEN 1
        ELSE 0
    END AS retained_45d,
    (
        SELECT MIN(service_events.event_date)
        FROM service_events
        WHERE
            service_events.member_id = members.member_id
            AND service_events.completed = 1
    ) AS first_completed_service
FROM members;

CREATE VIEW calendar_months AS
WITH RECURSIVE months(month_start) AS (
    SELECT date('2025-01-01')
    UNION ALL
    SELECT date(month_start, '+1 month')
    FROM months
    WHERE month_start < date('2025-12-01')
)
SELECT month_start
FROM months;

CREATE VIEW site_monthly_metrics AS
WITH event_rollup AS (
    SELECT
        members.site_id,
        date(
            service_events.event_date,
            'start of month'
        ) AS month_start,
        COUNT(*) AS scheduled_events,
        SUM(service_events.completed) AS completed_services,
        COUNT(
            DISTINCT CASE
                WHEN service_events.completed = 1
                THEN service_events.member_id
            END
        ) AS active_members,
        AVG(
            CASE
                WHEN service_events.completed = 1
                THEN service_events.duration_minutes
            END
        ) AS avg_completed_minutes
    FROM service_events
    INNER JOIN members
        ON service_events.member_id = members.member_id
    GROUP BY
        members.site_id,
        date(service_events.event_date, 'start of month')
)
SELECT
    sites.site_id,
    sites.site_name,
    sites.region,
    calendar_months.month_start,
    sites.monthly_target,
    COALESCE(event_rollup.scheduled_events, 0)
        AS scheduled_events,
    COALESCE(event_rollup.completed_services, 0)
        AS completed_services,
    COALESCE(event_rollup.active_members, 0)
        AS active_members,
    ROUND(event_rollup.avg_completed_minutes, 1)
        AS avg_completed_minutes,
    ROUND(
        1.0 * COALESCE(event_rollup.completed_services, 0)
        / NULLIF(event_rollup.scheduled_events, 0),
        3
    ) AS completion_rate,
    ROUND(
        1.0 * COALESCE(event_rollup.completed_services, 0)
        / sites.monthly_target,
        3
    ) AS target_attainment
FROM sites
CROSS JOIN calendar_months
LEFT JOIN event_rollup
    ON sites.site_id = event_rollup.site_id
    AND calendar_months.month_start = event_rollup.month_start;
