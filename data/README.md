# Generated database

`scripts/build_demo_database.py` creates `analytics_demo.sqlite` in this directory.

The generated database contains:

- 8 fictional sites
- 480 fictional members
- 3,076 deterministic service-event records
- 252 deterministic support tickets

The SQLite file is ignored because it is reproducible from source. Saved aggregate query outputs are committed in `outputs/` for quick review.
