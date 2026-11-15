# Event-time cohort snapshot

Cutoff: **2025-06-30**. All source records are synthetic. The database is opened read-only; existing result tables and graphics are unchanged.

| Measure | Count / rate |
|---|---:|
| Members signed up by cutoff | 480 |
| Full 14-day observation window | 441 |
| Still observing the 14-day window | 39 |
| Activated among mature 14-day members | 228 |
| Mature-cohort 14-day activation | 51.7% |
| Full 45-day observation window | 358 |
| Still observing the 45-day window | 122 |
| Retained among mature 45-day members | 158 |
| Mature-cohort 45-day retention | 44.1% |

Retention requires activation on days 0-14 and a completed service on days 15-45, inclusive. Its denominator is all members with a complete 45-day window, not only activated members. New members are excluded from a rate until the entire corresponding window has elapsed; their count remains visible. A zero denominator yields a missing rate, not zero performance.

Events after cutoff and signups after cutoff are not used. Multiple qualifying services cannot duplicate a member. Event-time filtering assumes the source feed is complete through cutoff; without ingestion timestamps it cannot reconstruct exactly what was known on that historical date. A genuinely missing feed must not be interpreted as zero activity.

[Site/channel results](as-of-cohorts.csv) · [Query](../sql/08_as_of_cohorts.sql) · [Boundary tests](../tests/test_as_of.py) · [Policy](../docs/as-of-metrics.md)
