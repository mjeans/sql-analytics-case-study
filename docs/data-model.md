# Data model

## `sites`

One row per service location.

| Column | Type | Description |
|---|---|---|
| site_id | text | Primary key |
| site_name | text | Display name |
| region | text | North, South, East, or West |
| launch_date | date text | Site launch date |
| monthly_target | integer | Completed-service target |

## `members`

One row per member.

| Column | Type | Description |
|---|---|---|
| member_id | text | Primary key |
| site_id | text | Foreign key to `sites` |
| signup_date | date text | Enrollment date |
| acquisition_channel | text | Referral, outreach, web, or partner |
| age_band | text | Nonidentifying analytic band |

## `service_events`

One row per scheduled service event. `completed` equals one when the service occurred. Duration is populated only for completed services.

## `support_tickets`

One row per support contact, with opened date, resolution hours, and optional satisfaction score.

## Grain and joins

Metric definitions preserve table grain explicitly. Member outcomes are first aggregated to one row per member, then joined to dimensions. Site-month metrics aggregate events before window calculations so repeated event rows do not inflate denominators.

Dates use ISO-8601 text because SQLite's built-in date functions operate reliably on that representation.
