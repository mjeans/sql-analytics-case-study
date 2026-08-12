WITH member_metrics AS (
    SELECT
        date(signup_date, 'start of month') AS signup_month,
        acquisition_channel,
        activated_14d,
        retained_45d
    FROM member_activity_metrics
)
SELECT
    signup_month,
    acquisition_channel,
    COUNT(*) AS signups,
    SUM(activated_14d) AS activated_members,
    ROUND(
        1.0 * SUM(activated_14d) / COUNT(*),
        3
    ) AS activation_rate,
    SUM(retained_45d) AS retained_members,
    ROUND(
        1.0 * SUM(retained_45d) / COUNT(*),
        3
    ) AS retention_rate_45d
FROM member_metrics
GROUP BY
    signup_month,
    acquisition_channel
ORDER BY
    signup_month,
    activation_rate DESC,
    acquisition_channel;
