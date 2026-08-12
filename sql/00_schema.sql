PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS service_events;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS sites;

CREATE TABLE sites (
    site_id TEXT PRIMARY KEY,
    site_name TEXT NOT NULL,
    region TEXT NOT NULL
        CHECK (region IN ('North', 'South', 'East', 'West')),
    launch_date TEXT NOT NULL,
    monthly_target INTEGER NOT NULL
        CHECK (monthly_target > 0)
);

CREATE TABLE members (
    member_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL
        CHECK (
            acquisition_channel IN (
                'Referral',
                'Outreach',
                'Web',
                'Partner'
            )
        ),
    age_band TEXT NOT NULL
        CHECK (
            age_band IN (
                '18-29',
                '30-44',
                '45-59',
                '60+'
            )
        ),
    FOREIGN KEY (site_id) REFERENCES sites (site_id)
);

CREATE TABLE service_events (
    event_id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL
        CHECK (
            event_type IN (
                'Orientation',
                'Coaching',
                'Check-in'
            )
        ),
    duration_minutes INTEGER,
    completed INTEGER NOT NULL
        CHECK (completed IN (0, 1)),
    CHECK (
        (completed = 0 AND duration_minutes IS NULL)
        OR
        (
            completed = 1
            AND duration_minutes BETWEEN 10 AND 180
        )
    ),
    FOREIGN KEY (member_id) REFERENCES members (member_id)
);

CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    opened_date TEXT NOT NULL,
    resolution_hours REAL NOT NULL
        CHECK (resolution_hours >= 0),
    satisfaction_score INTEGER
        CHECK (satisfaction_score BETWEEN 1 AND 5),
    FOREIGN KEY (member_id) REFERENCES members (member_id)
);

CREATE INDEX idx_members_site
    ON members (site_id);

CREATE INDEX idx_events_member_date
    ON service_events (member_id, event_date);

CREATE INDEX idx_tickets_member
    ON support_tickets (member_id);
