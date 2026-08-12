WITH rolling_history AS (
    SELECT
        site_id,
        site_name,
        region,
        month_start,
        completed_services,
        AVG(completed_services) OVER (
            PARTITION BY site_id
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS prior_3m_average,
        COUNT(*) OVER (
            PARTITION BY site_id
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS prior_month_count
    FROM site_monthly_metrics
),
flagged AS (
    SELECT
        site_id,
        site_name,
        region,
        month_start,
        completed_services,
        ROUND(prior_3m_average, 1)
            AS prior_3m_average,
        ROUND(
            1.0 * (completed_services - prior_3m_average)
            / NULLIF(prior_3m_average, 0),
            3
        ) AS relative_change
    FROM rolling_history
    WHERE
        prior_month_count = 3
        AND completed_services < 0.75 * prior_3m_average
)
SELECT
    site_id,
    site_name,
    region,
    month_start,
    completed_services,
    prior_3m_average,
    relative_change,
    'Review operational context' AS recommended_action
FROM flagged
ORDER BY
    relative_change,
    site_id,
    month_start;
