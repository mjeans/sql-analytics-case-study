"""Build a deterministic SQLite database for the SQL case study."""

from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "analytics_demo.sqlite"

SITES = [
    ("S001", "Harbor", "North", "2024-01-15", 55),
    ("S002", "Riverside", "South", "2024-02-01", 60),
    ("S003", "Cedar", "East", "2024-03-12", 52),
    ("S004", "Lakeside", "West", "2024-01-22", 58),
    ("S005", "Meadow", "North", "2024-04-05", 50),
    ("S006", "Juniper", "South", "2024-02-18", 56),
    ("S007", "Summit", "East", "2024-05-10", 54),
    ("S008", "Park", "West", "2024-03-30", 57),
]

CHANNELS = ["Referral", "Outreach", "Web", "Partner"]
AGE_BANDS = ["18-29", "30-44", "45-59", "60+"]
EVENT_TYPES = ["Orientation", "Coaching", "Check-in"]

ACTIVATION_PROBABILITY = {
    "Referral": 0.88,
    "Partner": 0.80,
    "Web": 0.72,
    "Outreach": 0.65,
}
RETENTION_PROBABILITY = {
    "Referral": 0.75,
    "Partner": 0.69,
    "Web": 0.60,
    "Outreach": 0.55,
}
SITE_EFFECT = {
    "S001": 0.05,
    "S002": 0.02,
    "S003": 0.00,
    "S004": 0.03,
    "S005": -0.02,
    "S006": 0.01,
    "S007": -0.03,
    "S008": 0.02,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="SQLite database to create.",
    )
    return parser.parse_args()


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    return date(year, zero_based_month + 1, 1)


def clamp_probability(value: float) -> float:
    return max(0.05, min(0.95, value))


def build_database(database: Path) -> None:
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        database.unlink()

    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")

    schema = (ROOT / "sql" / "00_schema.sql").read_text(
        encoding="utf-8"
    )
    connection.executescript(schema)
    connection.executemany(
        """
        INSERT INTO sites (
            site_id,
            site_name,
            region,
            launch_date,
            monthly_target
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        SITES,
    )

    rng = random.Random(20260812)
    member_rows: list[tuple[str, str, str, str, str]] = []
    event_rows: list[
        tuple[str, str, str, str, int | None, int]
    ] = []
    ticket_rows: list[
        tuple[str, str, str, float, int | None]
    ] = []

    event_number = 1
    ticket_number = 1
    observation_end = date(2025, 12, 31)

    for member_number in range(1, 481):
        member_id = f"M{member_number:04d}"
        site_id = SITES[(member_number - 1) % len(SITES)][0]
        signup_date = date(2025, 1, 1) + timedelta(
            days=rng.randint(0, 180)
        )
        channel = rng.choices(
            CHANNELS,
            weights=[30, 22, 28, 20],
            k=1,
        )[0]
        age_band = rng.choices(
            AGE_BANDS,
            weights=[22, 38, 27, 13],
            k=1,
        )[0]

        member_rows.append(
            (
                member_id,
                site_id,
                signup_date.isoformat(),
                channel,
                age_band,
            )
        )

        activation_probability = clamp_probability(
            ACTIVATION_PROBABILITY[channel] + SITE_EFFECT[site_id]
        )
        activated = rng.random() < activation_probability
        first_delay = rng.randint(1, 21)

        if activated:
            first_date = signup_date + timedelta(days=first_delay)
            event_rows.append(
                (
                    f"E{event_number:06d}",
                    member_id,
                    first_date.isoformat(),
                    "Orientation",
                    rng.randint(25, 70),
                    1,
                )
            )
            event_number += 1

        retention_probability = clamp_probability(
            RETENTION_PROBABILITY[channel] + SITE_EFFECT[site_id]
        )
        retained_45d = activated and (
            rng.random() < retention_probability
        )
        if retained_45d:
            retained_date = signup_date + timedelta(
                days=rng.randint(15, 45)
            )
            event_rows.append(
                (
                    f"E{event_number:06d}",
                    member_id,
                    retained_date.isoformat(),
                    "Coaching",
                    rng.randint(30, 90),
                    1,
                )
            )
            event_number += 1

        first_month = add_months(
            date(signup_date.year, signup_date.month, 1),
            1,
        )
        month_start = first_month
        month_index = 1

        while month_start <= date(2025, 12, 1):
            activity_probability = (
                0.62
                + SITE_EFFECT[site_id]
                + (0.06 if retained_45d else -0.12)
                - 0.025 * month_index
            )
            if site_id == "S007" and month_start >= date(
                2025,
                9,
                1,
            ):
                activity_probability *= 0.22

            event_date = month_start + timedelta(
                days=rng.randint(0, 26)
            )
            if (
                event_date <= observation_end
                and rng.random()
                < clamp_probability(activity_probability)
            ):
                event_rows.append(
                    (
                        f"E{event_number:06d}",
                        member_id,
                        event_date.isoformat(),
                        rng.choice(["Coaching", "Check-in"]),
                        rng.randint(20, 100),
                        1,
                    )
                )
                event_number += 1

            if event_date <= observation_end and rng.random() < 0.14:
                event_rows.append(
                    (
                        f"E{event_number:06d}",
                        member_id,
                        event_date.isoformat(),
                        rng.choice(EVENT_TYPES),
                        None,
                        0,
                    )
                )
                event_number += 1

            month_start = add_months(month_start, 1)
            month_index += 1

        if rng.random() < 0.40:
            for _ in range(1 + int(rng.random() < 0.22)):
                max_days = max(
                    0,
                    (observation_end - signup_date).days,
                )
                opened_date = signup_date + timedelta(
                    days=rng.randint(0, min(210, max_days))
                )
                base_resolution = {
                    "Referral": 17,
                    "Partner": 21,
                    "Web": 27,
                    "Outreach": 31,
                }[channel]
                resolution = max(
                    0.5,
                    rng.gauss(
                        base_resolution
                        + (0 if retained_45d else 13)
                        + (8 if site_id == "S007" else 0),
                        9,
                    ),
                )
                satisfaction = round(
                    max(
                        1,
                        min(
                            5,
                            5.2
                            - resolution / 16
                            + rng.gauss(0, 0.55),
                        ),
                    )
                )
                ticket_rows.append(
                    (
                        f"T{ticket_number:05d}",
                        member_id,
                        opened_date.isoformat(),
                        round(resolution, 1),
                        satisfaction,
                    )
                )
                ticket_number += 1

    connection.executemany(
        """
        INSERT INTO members (
            member_id,
            site_id,
            signup_date,
            acquisition_channel,
            age_band
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        member_rows,
    )
    connection.executemany(
        """
        INSERT INTO service_events (
            event_id,
            member_id,
            event_date,
            event_type,
            duration_minutes,
            completed
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        event_rows,
    )
    connection.executemany(
        """
        INSERT INTO support_tickets (
            ticket_id,
            member_id,
            opened_date,
            resolution_hours,
            satisfaction_score
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ticket_rows,
    )

    metric_views = (
        ROOT / "sql" / "01_metric_views.sql"
    ).read_text(encoding="utf-8")
    connection.executescript(metric_views)
    connection.commit()

    foreign_key_issues = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
    if foreign_key_issues:
        raise RuntimeError(
            f"Foreign-key validation failed: {foreign_key_issues!r}"
        )

    counts = {
        table: connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        for table in (
            "sites",
            "members",
            "service_events",
            "support_tickets",
        )
    }
    connection.close()

    print(
        "Built database with "
        + ", ".join(
            f"{count:,} {table}"
            for table, count in counts.items()
        )
        + "."
    )


if __name__ == "__main__":
    build_database(parse_args().database)
