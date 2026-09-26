#!/usr/bin/env python3
"""
Reset RemoteTech's database to a clean state, for a fresh Week 4
new-user run-through or before a demo.

This does NOT need separate SQLite/Postgres logic. db.py already decides
the backend for you:

  - DATABASE_URL not set  -> local SQLite file (remotetech.db by default)
  - DATABASE_URL set      -> whatever hosted Postgres instance it points to

So to reset your LOCAL dev copy, just run this with no env vars set.
To reset the DEPLOYED database, run it in an environment where
DATABASE_URL is exported to that Postgres connection string (e.g. a
Railway/Render shell, or locally with the var exported for one run) --
same script, same code path as the live app.

*** Be careful with --full against a database real schools use. ***
Prefer keeping a separate throwaway Postgres instance for Week 4 testing
rather than running this against data a real customer is relying on.

Usage:
    python reset_db.py            # wipe users/progress/test data only
                                   #   (keeps quest content + branding)
    python reset_db.py --full     # also wipe quest_definitions,
                                   #   school_branding, licenses, then
                                   #   re-seed quests from quests_seed.json
"""

import argparse
import sys

from db import get_connection, USE_POSTGRES, SQLITE_PATH, DATABASE_URL
from remotetech_data import init_db
from quests_store import init_quests_table
from billing import init_billing_tables
from branding import init_branding_table

# Per-user / per-session data -- always wiped.
USER_DATA_TABLES = [
    "quest_times",
    "progress_shares",
    "password_resets",
    "progress",
    "users",
]

# App content / config -- only wiped with --full.
CONTENT_TABLES = [
    "licenses",
    "school_branding",
    "quest_definitions",
]


def _confirm():
    target = DATABASE_URL if USE_POSTGRES else f"local SQLite file ({SQLITE_PATH})"
    print(f"About to wipe data in: {target}")
    answer = input("Type 'yes' to continue: ").strip().lower()
    if answer != "yes":
        print("Aborted.")
        sys.exit(1)


def _clear_table(cur, table):
    if USE_POSTGRES:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
    else:
        cur.execute(f"DELETE FROM {table}")
        cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full", action="store_true",
        help="also wipe quest content, branding, and licenses, then re-seed quests",
    )
    args = parser.parse_args()

    # Make sure every table exists before touching it -- safe to run
    # against a brand-new database too.
    init_db()
    init_quests_table()
    init_billing_tables()
    init_branding_table()

    _confirm()

    conn = get_connection()
    cur = conn.cursor()

    tables = USER_DATA_TABLES + (CONTENT_TABLES if args.full else [])
    for table in tables:
        try:
            _clear_table(cur, table)
            print(f"  cleared {table}")
        except Exception as e:
            print(f"  ! could not clear {table}: {e}")

    conn.commit()
    conn.close()

    if args.full:
        # quest_definitions is empty again; init_quests_table() only
        # re-seeds from quests_seed.json when the table is empty.
        init_quests_table()
        print("  re-seeded quest_definitions from quests_seed.json")

    print("\nDone. Run seed_admin.py next to create a fresh admin account.")


if __name__ == "__main__":
    main()
