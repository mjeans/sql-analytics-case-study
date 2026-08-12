WITH member_support AS (
    SELECT
        support_tickets.member_id,
        AVG(support_tickets.resolution_hours)
            AS avg_resolution_hours,
        AVG(support_tickets.satisfaction_score)
            AS avg_satisfaction,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY support_tickets.member_id
),
ranked_support AS (
    SELECT
        member_support.*,
        member_activity_metrics.retained_45d,
        NTILE(4) OVER (
            ORDER BY member_support.avg_resolution_hours
        ) AS resolution_quartile
    FROM member_support
    INNER JOIN member_activity_metrics
        ON member_support.member_id =
            member_activity_metrics.member_id
)
SELECT
    resolution_quartile,
    COUNT(*) AS members_with_tickets,
    ROUND(AVG(avg_resolution_hours), 1)
        AS mean_resolution_hours,
    ROUND(AVG(avg_satisfaction), 2)
        AS mean_satisfaction,
    ROUND(AVG(ticket_count), 2)
        AS mean_ticket_count,
    ROUND(AVG(retained_45d), 3)
        AS retention_rate_45d
FROM ranked_support
GROUP BY resolution_quartile
ORDER BY resolution_quartile;
