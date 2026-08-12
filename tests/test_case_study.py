"""Integration tests for the generated database and analytical outputs."""

from __future__ import annotations

import csv
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SqlCaseStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        temporary_root = Path(cls.temporary_directory.name)
        cls.database = temporary_root / "case-study.sqlite"
        cls.output = temporary_root / "outputs"

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "build_demo_database.py"),
                "--database",
                str(cls.database),
            ],
            check=True,
            cwd=ROOT,
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_queries.py"),
                "--database",
                str(cls.database),
                "--output",
                str(cls.output),
            ],
            check=True,
            cwd=ROOT,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_database_grain_and_integrity(self) -> None:
        connection = sqlite3.connect(self.database)
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) FROM sites"
            ).fetchone()[0],
            8,
        )
        self.assertEqual(
            connection.execute(
                "SELECT COUNT(*) FROM members"
            ).fetchone()[0],
            480,
        )
        self.assertGreater(
            connection.execute(
                "SELECT COUNT(*) FROM service_events"
            ).fetchone()[0],
            1000,
        )
        self.assertEqual(
            connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall(),
            [],
        )
        connection.close()

    def test_quality_query_has_zero_failures(self) -> None:
        with (
            self.output / "02_data_quality.csv"
        ).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertTrue(rows)
        self.assertTrue(
            all(int(row["failed_rows"]) == 0 for row in rows)
        )

    def test_rates_are_bounded(self) -> None:
        with (
            self.output / "03_activation_funnel.csv"
        ).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertTrue(rows)
        for row in rows:
            self.assertGreaterEqual(
                float(row["activation_rate"]),
                0,
            )
            self.assertLessEqual(
                float(row["activation_rate"]),
                1,
            )
            self.assertGreaterEqual(
                float(row["retention_rate_45d"]),
                0,
            )
            self.assertLessEqual(
                float(row["retention_rate_45d"]),
                1,
            )

    def test_anomaly_query_identifies_summit(self) -> None:
        with (
            self.output / "07_anomaly_review.csv"
        ).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertTrue(rows)
        self.assertIn(
            "S007",
            {row["site_id"] for row in rows},
        )

    def test_saved_output_contract(self) -> None:
        expected = {
            query.replace(".sql", ".csv")
            for query in (
                "02_data_quality.sql",
                "03_activation_funnel.sql",
                "04_cohort_retention.sql",
                "05_site_performance.sql",
                "06_support_experience.sql",
                "07_anomaly_review.sql",
            )
        }
        self.assertEqual(
            {path.name for path in self.output.glob("*.csv")},
            expected,
        )


if __name__ == "__main__":
    unittest.main()
