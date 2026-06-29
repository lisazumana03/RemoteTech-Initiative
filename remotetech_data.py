import sqlite3
import bcrypt
import json

DB_NAME = "remotetech.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        user_name TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def register_user(full_name, username, email, password):

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT INTO users(full_name,user_name,email,password)
        VALUES(?,?,?,?)
        """,
        (full_name, username, email, hashed))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def login_user(username, password):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, full_name, user_name, password
    FROM users
    WHERE user_name=?
    """, (username,))

    user = cur.fetchone()
    conn.close()

    if not user:
        return None

    if bcrypt.checkpw(password.encode(), user[3].encode()):
        return user

    return None

def save_user_progress(user_name, points, badges, completed_lessons):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO progress (user_name, points, badges, completed_lessons)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_name) DO UPDATE SET
        points=excluded.points,
        badges=excluded.badges,
        completed_lessons=excluded.completed_lessons
    """, (
        user_name,
        points,
        json.dumps(badges),
        json.dumps(list(completed_lessons))
    ))

    conn.commit()
    conn.close()

def init_progress_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        user_name TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        badges TEXT DEFAULT '[]',
        completed_lessons TEXT DEFAULT '[]',
        quiz_attempts INTEGER DEFAULT 0,
        total_time INTEGER DEFAULT 0
    )
    """)

def load_user_progress(user_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT points, badges, completed_lessons
    FROM progress
    WHERE user_name=?
    """, (user_name,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "points": row[0],
        "badges": json.loads(row[1]),
        "completed_lessons": set(json.loads(row[2]))
    }
