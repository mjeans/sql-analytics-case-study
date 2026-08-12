WITH RECURSIVE month_offsets(month_number) AS (
    SELECT 0
    UNION ALL
    SELECT month_number + 1
    FROM month_offsets
    WHERE month_number < 6
),
cohort_members AS (
    SELECT
        member_id,
        date(signup_date, 'start of month') AS cohort_month
    FROM members
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM cohort_members
    GROUP BY cohort_month
),
completed_member_months AS (
    SELECT DISTINCT
        service_events.member_id,
        date(
            service_events.event_date,
            'start of month'
        ) AS activity_month
    FROM service_events
    WHERE service_events.completed = 1
),
cohort_grid AS (
    SELECT
        cohort_sizes.cohort_month,
        cohort_sizes.cohort_size,
        month_offsets.month_number,
        date(
            cohort_sizes.cohort_month,
            printf('+%d months', month_offsets.month_number)
        ) AS activity_month
    FROM cohort_sizes
    CROSS JOIN month_offsets
    WHERE
        date(
            cohort_sizes.cohort_month,
            printf('+%d months', month_offsets.month_number)
        ) <= date('2025-12-01')
)
SELECT
    cohort_grid.cohort_month,
    cohort_grid.month_number,
    cohort_grid.cohort_size,
    COUNT(DISTINCT completed_member_months.member_id)
        AS active_members,
    ROUND(
        1.0 * COUNT(DISTINCT completed_member_months.member_id)
        / cohort_grid.cohort_size,
        3
    ) AS retention_rate
FROM cohort_grid
LEFT JOIN cohort_members
    ON cohort_grid.cohort_month = cohort_members.cohort_month
LEFT JOIN completed_member_months
    ON cohort_members.member_id =
        completed_member_months.member_id
    AND cohort_grid.activity_month =
        completed_member_months.activity_month
GROUP BY
    cohort_grid.cohort_month,
    cohort_grid.month_number,
    cohort_grid.cohort_size
ORDER BY
    cohort_grid.cohort_month,
    cohort_grid.month_number;
