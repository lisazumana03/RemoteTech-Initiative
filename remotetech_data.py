import json
import sqlite3

import bcrypt

DB_PATH = 'remotetech.db'

def _connect():
    return sqlite3.connect(DB_PATH)

def _parse_json_list(value):
    if not value:
        return []

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _ensure_progress_columns(cursor):
    cursor.execute('PRAGMA table_info(users)')
    existing_columns = {row[1] for row in cursor.fetchall()}

    required_columns = {
        'points': 'INTEGER NOT NULL DEFAULT 0',
        'badges': "TEXT NOT NULL DEFAULT '[]'",
        'completed_lessons': "TEXT NOT NULL DEFAULT '[]'",
    }

    for column_name, definition in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {definition}')

    cursor.execute(
        '''
            UPDATE users
            SET points = COALESCE(points, 0),
                badges = COALESCE(badges, '[]'),
                completed_lessons = COALESCE(completed_lessons, '[]')
        '''
    )


def init_db():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            user_name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            avatar TEXT DEFAULT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            badges TEXT NOT NULL DEFAULT '[]',
            completed_lessons TEXT NOT NULL DEFAULT '[]'
        )
    ''')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        user_name TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        badges TEXT DEFAULT '[]',
        completed_lessons TEXT DEFAULT '[]',
        quiz_attempts INTEGER DEFAULT 0,
        total_time INTEGER DEFAULT 0
    )
    """)

    _ensure_progress_columns(cursor)
    conn.commit()
    conn.close()

def register_user(full_name, user_name, email, password):
    conn = _connect()
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            '''
                INSERT INTO users (full_name, user_name, email, password, avatar)
                VALUES (?, ?, ?, ?, ?)
            ''',
            (full_name, user_name, email, hashed_password, None),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(user_name, password):
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        '''
            SELECT full_name, user_name, password, points, badges, completed_lessons, avatar
            FROM users
            WHERE user_name = ?
        ''',
        (user_name,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    full_name, stored_user_name, hashed_password, points, badges, completed_lessons, avatar = row

    # verify password
    if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
        return None

    return {
        'full_name': full_name,
        'user_name': stored_user_name,
        'points': points or 0,
        'badges': _parse_json_list(badges),
        'completed_lessons': set(_parse_json_list(completed_lessons)),
    }

def update_password(username, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password=? WHERE user_name=?",
        (hashed, username)
    )
    conn.commit()
    conn.close()

def verify_email_matches(username, email):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE user_name=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0].lower() == email.lower()

def update_profile(username, new_full_name, new_avatar=None):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET full_name=?, avatar=? WHERE user_name=?", (new_full_name, new_avatar, username))
    conn.commit()
    conn.close()

def save_user_progress(user_name, points, badges, completed_lessons):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        '''
            UPDATE users
            SET points = ?,
                badges = ?,
                completed_lessons = ?
            WHERE user_name = ?
        ''',
        (points, json.dumps(badges), json.dumps(sorted(completed_lessons)), user_name),
    )
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
    SELECT u.full_name, p.points, p.badges
    FROM progress p
    JOIN users u ON u.user_name = p.user_name
    ORDER BY p.points DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    leaderboard = []
    for full_name, points, badges_json in rows:
        badges = json.loads(badges_json)
        leaderboard.append({
            "Hero": full_name,
            "Points": points,
            "Badges": ", ".join(badges) if badges else ""
        })
    return leaderboard
