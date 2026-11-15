-- Event-time snapshot. :as_of_date must be an ISO date validated by the runner.
-- This does not reconstruct ingestion time: the fixture has no arrival timestamps.
WITH eligible AS (
    SELECT member_id, site_id, acquisition_channel, signup_date,
           date(signup_date, '+14 days') <= :as_of_date AS mature_14d,
           date(signup_date, '+45 days') <= :as_of_date AS mature_45d
    FROM members
    WHERE signup_date <= :as_of_date
), activity AS (
    SELECT e.*,
           EXISTS (
               SELECT 1 FROM service_events s
               WHERE s.member_id = e.member_id AND s.completed = 1
                 AND s.event_date BETWEEN e.signup_date AND date(e.signup_date, '+14 days')
                 AND s.event_date <= :as_of_date
           ) AS activation_observed,
           EXISTS (
               SELECT 1 FROM service_events s
               WHERE s.member_id = e.member_id AND s.completed = 1
                 AND s.event_date BETWEEN date(e.signup_date, '+15 days') AND date(e.signup_date, '+45 days')
                 AND s.event_date <= :as_of_date
           ) AS continued_use_observed
    FROM eligible e
)
SELECT :as_of_date AS as_of_date,
       site_id, acquisition_channel,
       COUNT(*) AS signed_up_by_cutoff,
       SUM(mature_14d) AS eligible_14d_denominator,
       SUM(1 - mature_14d) AS still_observing_14d,
       SUM(mature_14d AND activation_observed) AS activated_14d_numerator,
       1.0 * SUM(mature_14d AND activation_observed) / NULLIF(SUM(mature_14d), 0) AS activation_14d_rate,
       SUM(mature_45d) AS eligible_45d_denominator,
       SUM(1 - mature_45d) AS still_observing_45d,
       SUM(mature_45d AND activation_observed AND continued_use_observed) AS retained_45d_numerator,
       1.0 * SUM(mature_45d AND activation_observed AND continued_use_observed) / NULLIF(SUM(mature_45d), 0) AS retention_45d_rate
FROM activity
GROUP BY site_id, acquisition_channel
ORDER BY site_id, acquisition_channel;
