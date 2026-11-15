# Observation-window-aware cohort metrics

The [executed June 30 snapshot](../outputs/as-of-report.md) adds a parameterized event-time view without changing the original full-history metrics or figures.

The question is: **as of a specified date, which members have had enough follow-up to evaluate activation or retention?** Counting a person who joined yesterday as a 45-day retention failure would conflate incomplete observation with nonretention.

## Rules

- Include signups on or before cutoff.
- A 14-day denominator includes only signups whose day 14 is on or before cutoff.
- A 45-day denominator independently requires day 45 to be on or before cutoff.
- Activation requires at least one completed service during inclusive days 0-14.
- Retention requires activation plus at least one completed service during inclusive days 15-45; its denominator is all mature 45-day members.
- Every event must also occur on or before cutoff. EXISTS preserves one-person-one-count even with repeated services.
- Show still-observing counts. A rate with no mature members is NULL, not zero.

The original full-history results and this snapshot answer different questions; their differences are not metric regressions. Data must be complete through cutoff. Without arrival timestamps, this is **event-time filtering, not a historical reconstruction of what the organization knew**. Late-arriving revisions would require a separate ingestion-time/versioning design.

## Reproduce

```bash
python scripts/build_demo_database.py
python scripts/run_as_of.py --as-of 2025-06-30
python -m unittest discover -s tests -v
```

The runner validates a real ISO date, binds it as a SQL parameter, and opens the database read-only. Choose another output directory to retain several snapshots. The tests cover day 14/day 45 boundaries, empty/immature denominators, duplicated events, incomplete/pre-signup events, and future information. No new packages are required.
