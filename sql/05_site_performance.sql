WITH performance AS (
    SELECT
        site_id,
        site_name,
        region,
        month_start,
        monthly_target,
        scheduled_events,
        completed_services,
        active_members,
        completion_rate,
        target_attainment,
        LAG(completed_services) OVER (
            PARTITION BY site_id
            ORDER BY month_start
        ) AS prior_month_services,
        AVG(completed_services) OVER (
            PARTITION BY site_id
            ORDER BY month_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3m_services
    FROM site_monthly_metrics
)
SELECT
    site_id,
    site_name,
    region,
    month_start,
    scheduled_events,
    completed_services,
    active_members,
    completion_rate,
    target_attainment,
    prior_month_services,
    ROUND(
        CASE
            WHEN prior_month_services > 0
            THEN 1.0
                * (completed_services - prior_month_services)
                / prior_month_services
        END,
        3
    ) AS month_over_month_change,
    ROUND(rolling_3m_services, 1)
        AS rolling_3m_services,
    RANK() OVER (
        PARTITION BY month_start
        ORDER BY target_attainment DESC
    ) AS monthly_site_rank
FROM performance
ORDER BY
    month_start,
    monthly_site_rank,
    site_id;
