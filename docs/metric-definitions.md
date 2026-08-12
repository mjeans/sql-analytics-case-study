# Metric definitions

| Metric | Definition | Grain |
|---|---|---|
| 14-day activation | At least one completed service from signup through day 14 | Member |
| 45-day retention | At least one completed service from day 15 through day 45 after signup | Member |
| Monthly active member | At least one completed service during a calendar month | Member-month |
| Completion rate | Completed events divided by all scheduled events | Site-month |
| Target attainment | Completed services divided by the site's monthly target | Site-month |
| Cohort retention | Active members at month N divided by original signup-cohort size | Cohort-month |
| Support-resolution quartile | Member's average resolution hours ranked across members with tickets | Member |
| Activity anomaly | Completed services at least 25% below the prior three-month average, with three prior months available | Site-month |

## Denominator rules

- Activation and retention denominators include every member in the relevant signup group.
- Event completion uses all scheduled events, not only members with completed events.
- Cohort size is fixed at signup and does not shrink when a member becomes inactive.
- Members with no support ticket are excluded from support quartiles and reported separately when needed.
- Months with zero events are materialized through the calendar view so absence is not mistaken for missing data.

## Interpretation

These definitions are operational, not causal. They are written before querying so business logic can be reviewed independently of the code.
