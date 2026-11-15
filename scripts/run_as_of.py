"""Generate event-time cohort metrics without treating immature windows as failures."""
import argparse
import csv
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_date(value):
    try:
        parsed = date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("as_of_date must be a real calendar date in YYYY-MM-DD form") from None
    if parsed.isoformat() != value:
        raise ValueError("as_of_date must use exact YYYY-MM-DD form")
    return value


def query_as_of(connection, cutoff):
    validate_date(cutoff)
    connection.row_factory = sqlite3.Row
    return connection.execute((ROOT / "sql/08_as_of_cohorts.sql").read_text(), {"as_of_date": cutoff})


def run(database, cutoff, output):
    if not database.is_file():
        raise FileNotFoundError("Build the demo database first")
    validate_date(cutoff)
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as conn:
        cursor = query_as_of(conn, cutoff)
        columns = [x[0] for x in cursor.description]
        rows = cursor.fetchall()
    with (output / "as-of-cohorts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    total = lambda key: sum(r[key] for r in rows)
    rate = lambda num, den: f"{100 * total(num) / total(den):.1f}%" if total(den) else "Not yet estimable"
    text = f"""# Event-time cohort snapshot

Cutoff: **{cutoff}**. All source records are synthetic. The database is opened read-only; existing result tables and graphics are unchanged.

| Measure | Count / rate |
|---|---:|
| Members signed up by cutoff | {total('signed_up_by_cutoff')} |
| Full 14-day observation window | {total('eligible_14d_denominator')} |
| Still observing the 14-day window | {total('still_observing_14d')} |
| Activated among mature 14-day members | {total('activated_14d_numerator')} |
| Mature-cohort 14-day activation | {rate('activated_14d_numerator', 'eligible_14d_denominator')} |
| Full 45-day observation window | {total('eligible_45d_denominator')} |
| Still observing the 45-day window | {total('still_observing_45d')} |
| Retained among mature 45-day members | {total('retained_45d_numerator')} |
| Mature-cohort 45-day retention | {rate('retained_45d_numerator', 'eligible_45d_denominator')} |

Retention requires activation on days 0-14 and a completed service on days 15-45, inclusive. Its denominator is all members with a complete 45-day window, not only activated members. New members are excluded from a rate until the entire corresponding window has elapsed; their count remains visible. A zero denominator yields a missing rate, not zero performance.

Events after cutoff and signups after cutoff are not used. Multiple qualifying services cannot duplicate a member. Event-time filtering assumes the source feed is complete through cutoff; without ingestion timestamps it cannot reconstruct exactly what was known on that historical date. A genuinely missing feed must not be interpreted as zero activity.

[Site/channel results](as-of-cohorts.csv) · [Query](../sql/08_as_of_cohorts.sql) · [Boundary tests](../tests/test_as_of.py) · [Policy](../docs/as-of-metrics.md)
"""
    (output / "as-of-report.md").write_text(text, encoding="utf-8", newline="\n")
    print(f"Published {len(rows)} as-of site/channel rows for {cutoff}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default="2025-06-30")
    parser.add_argument("--database", type=Path, default=ROOT / "data/analytics_demo.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    run(args.database, args.as_of, args.output)
