"""
Database connection layer.

- If a DATABASE_URL env var is set (Supabase / Railway / Render Postgres
  connection string, e.g. "postgresql://user:pass@host:5432/dbname"),
  connects to that hosted Postgres instance.
- Otherwise falls back to the local SQLite file, so local development
  still works without any extra setup.

Query strings in remotetech_data.py are written with "?" placeholders
(SQLite style); `adapt()` rewrites them to "%s" (Postgres/psycopg2 style)
automatically, so the calling code doesn't need two copies of every query.
"""

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extensions
    # Make psycopg2 return plain Python types the rest of the code expects.
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
else:
    import sqlite3

SQLITE_PATH = os.environ.get("SQLITE_PATH", "remotetech.db")


def get_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(SQLITE_PATH)


def adapt(sql):
    """Rewrite '?' placeholders to '%s' when running against Postgres."""
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def autoincrement_pk():
    """Primary-key column definition, per backend."""
    return "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"


def upsert_clause(table, conflict_col, update_cols):
    """
    Both modern SQLite (3.24+) and Postgres support the same
    "ON CONFLICT (...) DO UPDATE SET ..." syntax, so this is mostly a
    convenience helper for readability at call sites.
    """
    set_clause = ", ".join(f"{c}=excluded.{c}" for c in update_cols)
    return f"ON CONFLICT({conflict_col}) DO UPDATE SET {set_clause}"
