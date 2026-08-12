"""Execute analytical SQL files and save deterministic CSV outputs."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "analytics_demo.sqlite"
DEFAULT_OUTPUT = ROOT / "outputs"

QUERY_FILES = [
    "02_data_quality.sql",
    "03_activation_funnel.sql",
    "04_cohort_retention.sql",
    "05_site_performance.sql",
    "06_support_experience.sql",
    "07_anomaly_review.sql",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def run_queries(database: Path, output: Path) -> None:
    if not database.exists():
        raise FileNotFoundError(
            f"Database not found: {database}. Build it first."
        )

    output.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    for query_name in QUERY_FILES:
        query_path = ROOT / "sql" / query_name
        sql = query_path.read_text(encoding="utf-8")
        rows = connection.execute(sql).fetchall()

        output_path = output / query_name.replace(".sql", ".csv")
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.writer(handle)
            if rows:
                writer.writerow(rows[0].keys())
                writer.writerows(
                    [tuple(row) for row in rows]
                )
            else:
                description = connection.execute(sql).description
                writer.writerow(
                    column[0] for column in description
                )

        try:
            display_path = output_path.relative_to(ROOT)
        except ValueError:
            display_path = output_path

        print(
            f"Wrote {len(rows):,} rows to {display_path}."
        )

    connection.close()


if __name__ == "__main__":
    arguments = parse_args()
    run_queries(arguments.database, arguments.output)
