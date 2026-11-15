import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_as_of import query_as_of, validate_date


class AsOfTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
        CREATE TABLE members (member_id TEXT PRIMARY KEY, site_id TEXT, acquisition_channel TEXT, signup_date TEXT);
        CREATE TABLE service_events (member_id TEXT, event_date TEXT, completed INTEGER);
        """)

    def tearDown(self):
        self.db.close()

    def member(self, name, day):
        self.db.execute("INSERT INTO members VALUES (?, 'S1', 'Web', ?)", (name, day))

    def event(self, name, day, completed=1):
        self.db.execute("INSERT INTO service_events VALUES (?, ?, ?)", (name, day, completed))

    def row(self, cutoff):
        return dict(query_as_of(self.db, cutoff).fetchone())

    def test_immature_windows_are_not_failures(self):
        self.member("new", "2025-01-10")
        r = self.row("2025-01-20")
        self.assertEqual(r["still_observing_14d"], 1)
        self.assertIsNone(r["activation_14d_rate"])
        self.assertIsNone(r["retention_45d_rate"])

    def test_exact_window_endpoints(self):
        self.member("a", "2025-01-01")
        self.event("a", "2025-01-15")  # day 14
        self.event("a", "2025-02-15")  # day 45
        self.assertEqual(self.row("2025-01-15")["activation_14d_rate"], 1)
        self.assertIsNone(self.row("2025-02-14")["retention_45d_rate"])
        self.assertEqual(self.row("2025-02-15")["retention_45d_rate"], 1)

    def test_late_activation_does_not_qualify(self):
        self.member("a", "2025-01-01")
        self.event("a", "2025-01-16")
        self.assertEqual(self.row("2025-02-15")["retention_45d_rate"], 0)

    def test_duplicates_do_not_inflate_members(self):
        self.member("a", "2025-01-01")
        for _ in range(3):
            self.event("a", "2025-01-03")
            self.event("a", "2025-02-01")
        r = self.row("2025-02-15")
        self.assertEqual(r["retained_45d_numerator"], 1)
        self.assertEqual(r["signed_up_by_cutoff"], 1)

    def test_future_signups_and_events_excluded(self):
        self.member("old", "2025-01-01")
        self.member("future", "2025-03-01")
        self.event("old", "2025-01-02")
        self.event("old", "2025-02-01")
        before = self.row("2025-01-15")
        self.db.execute("DELETE FROM service_events WHERE event_date > '2025-01-15'")
        self.assertEqual(before, self.row("2025-01-15"))
        self.assertEqual(before["signed_up_by_cutoff"], 1)

    def test_pre_signup_and_incomplete_events_excluded(self):
        self.member("a", "2025-01-01")
        self.event("a", "2024-12-31")
        self.event("a", "2025-01-02", 0)
        self.assertEqual(self.row("2025-01-15")["activated_14d_numerator"], 0)

    def test_invalid_dates_rejected(self):
        for value in ["2025-02-30", "20250101", "2025-1-1", "2025-01-01'; DROP TABLE members;--"]:
            with self.assertRaises(ValueError):
                validate_date(value)

    def test_empty_cohort(self):
        self.assertEqual(query_as_of(self.db, "2025-01-01").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
