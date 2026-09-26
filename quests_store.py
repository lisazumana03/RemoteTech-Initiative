"""
Storage for quest *content and grading rules* (see quest_engine.py for how
the rules are interpreted). This used to be a hardcoded QUESTS list plus a
few hundred lines of if/elif in remote_tech_app.py; now it's rows in a
`quest_definitions` table, each holding one quest as a JSON blob.

Why a DB table and not just a JSON file on disk: most low-cost hosts for a
Streamlit app (Render, Railway free/hobby tiers, etc.) have an ephemeral
filesystem — anything written to disk at runtime disappears on the next
deploy or restart. The Postgres/SQLite database already used for users and
progress (see db.py) does persist, so quest definitions live there too.
The JSON file (quests_seed.json) is only the *seed* — the one-time
starting content — not the source of truth after that.
"""

import json
import os

from db import get_connection, adapt, USE_POSTGRES

_SEED_PATH = os.path.join(os.path.dirname(__file__), "quests_seed.json")


def init_quests_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quest_definitions (
            id TEXT PRIMARY KEY,
            quest_set TEXT NOT NULL DEFAULT 'foundations',
            sort_order INTEGER NOT NULL DEFAULT 0,
            definition TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM quest_definitions")
    count = cur.fetchone()[0]
    conn.close()

    if count == 0:
        _seed_from_file()


def _seed_from_file():
    with open(_SEED_PATH, "r", encoding="utf-8") as f:
        quests = json.load(f)
    for quest in quests:
        save_quest(quest)


def get_all_quests(include_set=None):
    """All quests, ordered for display. Pass include_set to filter to one set."""
    conn = get_connection()
    cur = conn.cursor()
    if include_set:
        cur.execute(
            adapt("SELECT definition FROM quest_definitions WHERE quest_set = ? ORDER BY sort_order"),
            (include_set,),
        )
    else:
        cur.execute("SELECT definition FROM quest_definitions ORDER BY sort_order")
    rows = cur.fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]


def get_quest(quest_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("SELECT definition FROM quest_definitions WHERE id = ?"), (quest_id,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def get_all_sets():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT quest_set FROM quest_definitions ORDER BY quest_set")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def save_quest(quest):
    """Create or update a quest. `quest` must at least have 'id'; sort_order
    and quest_set default sensibly if omitted so a teacher can add a quest
    from the admin JSON editor without filling in every field."""
    quest_id = str(quest["id"])
    quest_set = quest.get("quest_set", "foundations")
    sort_order = quest.get("sort_order", 999)

    conn = get_connection()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute(adapt("""
            INSERT INTO quest_definitions (id, quest_set, sort_order, definition, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                quest_set = excluded.quest_set,
                sort_order = excluded.sort_order,
                definition = excluded.definition,
                updated_at = CURRENT_TIMESTAMP
        """), (quest_id, quest_set, sort_order, json.dumps(quest)))
    else:
        cur.execute(adapt("""
            INSERT INTO quest_definitions (id, quest_set, sort_order, definition, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                quest_set = excluded.quest_set,
                sort_order = excluded.sort_order,
                definition = excluded.definition,
                updated_at = CURRENT_TIMESTAMP
        """), (quest_id, quest_set, sort_order, json.dumps(quest)))
    conn.commit()
    conn.close()


def delete_quest(quest_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("DELETE FROM quest_definitions WHERE id = ?"), (str(quest_id),))
    conn.commit()
    conn.close()
