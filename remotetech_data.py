import json
import secrets
import hashlib
from datetime import datetime, timedelta

import bcrypt

from db import get_connection, adapt, autoincrement_pk, upsert_clause, USE_POSTGRES

# How long a password-reset token stays valid.
RESET_TOKEN_TTL_MINUTES = 30
EMAIL_VERIFICATION_TTL_HOURS = 24

# The fixed account used for the "Try the Demo" flow. Progress made while
# logged in as this account is never persisted (see is_demo handling in
# remote_tech_app.py), so it's safe for it to be shared across visitors.
DEMO_USERNAME = "demo_hero"


def _connect():
    return get_connection()


def _column_exists(cursor, table, column):
    if USE_POSTGRES:
        cursor.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
            (table, column),
        )
        return cursor.fetchone() is not None
    else:
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())


def _ensure_column(cursor, table, column, coltype_sql):
    """Add a column to an already-existing table if it isn't there yet.

    Both SQLite and Postgres support `ALTER TABLE ... ADD COLUMN`, but
    neither lets us combine that with `CREATE TABLE IF NOT EXISTS`, so this
    acts as a tiny migration step that's safe to run on every startup.
    """
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype_sql}")


def init_db():
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {autoincrement_pk()},
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            avatar TEXT DEFAULT '🚀',
            role TEXT NOT NULL DEFAULT 'student',
            points INTEGER NOT NULL DEFAULT 0,
            badges TEXT NOT NULL DEFAULT '[]',
            completed_lessons TEXT NOT NULL DEFAULT '[]'
        )
    ''')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            username TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0,
            badges TEXT DEFAULT '[]',
            completed_lessons TEXT DEFAULT '[]',
            quiz_attempts INTEGER DEFAULT 0,
            total_time INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quest_times (
            username TEXT,
            quest_id TEXT,
            seconds_spent INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (username, quest_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            username TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            username TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress_shares (
            token_hash TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)

    # ---- Migrations for installs created before these columns existed ----
    _ensure_column(cursor, "users", "school", "TEXT DEFAULT ''")
    _ensure_column(cursor, "users", "class_name", "TEXT DEFAULT ''")
    _ensure_column(cursor, "users", "is_demo", "INTEGER DEFAULT 0")
    # Existing accounts are grandfathered as verified so this migration does not
    # unexpectedly lock out current users. All new public registrations explicitly
    # set email_verified=False and must complete verification before login.
    _ensure_column(cursor, "users", "email_verified", "INTEGER NOT NULL DEFAULT 1")

    # Application reviews submitted by registered RemoteTech users.
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS application_feedback (
            id {autoincrement_pk()},
            username TEXT NOT NULL,
            application_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            category TEXT NOT NULL,
            review TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open'
                CHECK (status IN ('Open', 'Under Review', 'Resolved', 'Closed')),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            UNIQUE (username, application_name)
        )
    """)

    conn.commit()
    conn.close()

def _parse_json_list(value):
    if not value:
        return []

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []

def register_user(full_name, username, email, password, avatar, role="student",
                   popia_consent=False, school="", class_name="", is_demo=False,
                   email_verified=True):
    conn = _connect()
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            adapt('''
                INSERT INTO users (full_name, username, email, password, avatar, role, school, class_name, is_demo, email_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''),
            (full_name, username, email, hashed_password, avatar, role,
             school, class_name, 1 if is_demo else 0, 1 if email_verified else 0),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(adapt("""
    SELECT id,
           full_name,
           username,
           password,
           role,
           points,
           badges,
           completed_lessons,
           avatar,
           school,
           class_name,
           is_demo,
           email_verified
    FROM users
    WHERE username = ?
"""), (username,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    (user_id, full_name, stored_username, hashed_password, role, points, badges,
     completed_lessons, avatar, school, class_name, is_demo, email_verified) = row

    # verify password
    if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
        return None

    return {
        'user_id': user_id,
        'full_name': full_name,
        'username': stored_username,
        'role': role,
        'points': points or 0,
        'badges': _parse_json_list(badges),
        'completed_lessons': set(_parse_json_list(completed_lessons)),
        'avatar': avatar,
        'school': school or "",
        'class_name': class_name or "",
        'is_demo': bool(is_demo),
        'email_verified': bool(email_verified),
    }

def update_password(username, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        adapt("UPDATE users SET password=? WHERE username=?"),
        (hashed, username)
    )
    conn.commit()
    conn.close()

def verify_email_matches(username, email):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("SELECT email FROM users WHERE username=?"), (username,))
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0].lower() == email.lower()

def update_profile(username, new_full_name, new_avatar=None, new_class_name=None):
    conn = _connect()
    cur = conn.cursor()
    if new_class_name is not None:
        cur.execute(
            adapt("UPDATE users SET full_name=?, avatar=?, class_name=? WHERE username=?"),
            (new_full_name, new_avatar, new_class_name, username),
        )
    else:
        cur.execute(
            adapt("UPDATE users SET full_name=?, avatar=? WHERE username=?"),
            (new_full_name, new_avatar, username),
        )
    conn.commit()
    conn.close()

def save_user_progress(username, points, badges, completed_lessons):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        adapt('''
            UPDATE users
            SET points = ?,
                badges = ?,
                completed_lessons = ?
            WHERE username = ?
        '''),
        (points, json.dumps(badges), json.dumps(sorted(completed_lessons)), username),
    )

    cursor.execute(adapt(f"""
        INSERT INTO progress (username, points, badges, completed_lessons, last_active)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        {upsert_clause("progress", "username", ["points", "badges", "completed_lessons", "last_active"])}
        """), (username, points, json.dumps(badges), json.dumps(list(completed_lessons))))

    conn.commit()
    conn.close()

def load_user_progress(username):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        adapt('''
            SELECT points, badges, completed_lessons
            FROM users
            WHERE username = ?
        '''),
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        points, badges_json, completed_lessons_json = row
        return {
            'points': points or 0,
            'badges': _parse_json_list(badges_json),
            'completed_lessons': set(_parse_json_list(completed_lessons_json)),
        }
    else:
        return {
            'points': 0,
            'badges': [],
            'completed_lessons': set(),
        }

def save_quest_time(username, quest_id, seconds_spent):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt(f"""
    INSERT INTO quest_times (username, quest_id, seconds_spent)
    VALUES (?, ?, ?)
    {upsert_clause("quest_times", "username, quest_id", ["seconds_spent", "completed_at"])}
    """).replace("excluded.completed_at", "CURRENT_TIMESTAMP"),
    (username, quest_id, seconds_spent))
    conn.commit()
    conn.close()

def get_leaderboard(limit=10, class_name=None):
    """Leaderboard, optionally scoped to a single class/school group.

    class_name=None (or "") returns the unscoped, sitewide leaderboard —
    used as a fallback for students who aren't assigned to a class yet.
    """
    conn = _connect()
    cur = conn.cursor()
    if class_name:
        cur.execute(adapt("""
        SELECT u.full_name, p.points, p.badges
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE u.class_name = ? AND (u.is_demo = 0 OR u.is_demo IS NULL)
        ORDER BY p.points DESC
        LIMIT ?
        """), (class_name, limit))
    else:
        cur.execute(adapt("""
        SELECT u.full_name, p.points, p.badges
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE (u.is_demo = 0 OR u.is_demo IS NULL)
        ORDER BY p.points DESC
        LIMIT ?
        """), (limit,))
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

def get_all_student_progress(class_name=None):
    """Full progress overview for all students, optionally scoped to a class."""
    conn = _connect()
    cur = conn.cursor()
    if class_name:
        cur.execute(adapt("""
        SELECT u.full_name, u.username, p.points, p.badges, p.completed_lessons, u.class_name, u.school, p.last_active
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE u.class_name = ? AND (u.is_demo = 0 OR u.is_demo IS NULL)
        ORDER BY p.points DESC
        """), (class_name,))
    else:
        cur.execute("""
        SELECT u.full_name, u.username, p.points, p.badges, p.completed_lessons, u.class_name, u.school, p.last_active
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE (u.is_demo = 0 OR u.is_demo IS NULL)
        ORDER BY p.points DESC
        """)
    rows = cur.fetchall()
    conn.close()

    students = []
    for full_name, user_name, points, badges_json, lessons_json, class_name_val, school_val, last_active in rows:
        badges = json.loads(badges_json)
        lessons = json.loads(lessons_json)
        students.append({
            "full_name": full_name,
            "user_name": user_name,
            "points": points,
            "badges": badges,
            "completed_lessons": lessons,
            "lessons_count": len(lessons),
            "class_name": class_name_val or "",
            "school": school_val or "",
            "last_active": last_active,
        })
    return students


def get_all_classes():
    """Distinct, non-empty class names — used to populate the admin filter."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT class_name FROM users
        WHERE class_name IS NOT NULL AND class_name != '' AND (is_demo = 0 OR is_demo IS NULL)
        ORDER BY class_name
    """)
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_inactive_students(days=7, class_name=None):
    """Students who haven't logged any progress in X days, optionally scoped to a class."""
    conn = _connect()
    cur = conn.cursor()
    demo_clause = "AND (u.is_demo = 0 OR u.is_demo IS NULL)"
    class_clause = "AND u.class_name = ?" if class_name else ""
    if USE_POSTGRES:
        params = [str(days)] + ([class_name] if class_name else [])
        cur.execute(f"""
        SELECT u.full_name, u.username, p.points, p.last_active
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE (p.last_active < NOW() - (%s || ' days')::interval OR p.last_active IS NULL)
        {demo_clause} {class_clause}
        ORDER BY p.last_active ASC
        """, params)
    else:
        params = [f'-{days} days'] + ([class_name] if class_name else [])
        cur.execute(f"""
        SELECT u.full_name, u.username, p.points, p.last_active
        FROM progress p
        JOIN users u ON u.username = p.username
        WHERE (p.last_active < datetime('now', ?) OR p.last_active IS NULL)
        {demo_clause} {class_clause}
        ORDER BY p.last_active ASC
        """, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_quest_completion_stats(class_name=None, quest_ids=None):
    """How many students completed each quest, optionally scoped to a class.

    quest_ids: pass the current list of quest ids (e.g. from
    quests_store.get_all_quests()) so the stats cover however many quests
    exist today — the content library can grow without this function
    needing a code change. Falls back to whatever ids show up in the data
    if not provided, so old callers keep working.
    """
    conn = _connect()
    cur = conn.cursor()
    if class_name:
        cur.execute(adapt("""
            SELECT p.completed_lessons
            FROM progress p
            JOIN users u ON u.username = p.username
            WHERE u.class_name = ? AND (u.is_demo = 0 OR u.is_demo IS NULL)
        """), (class_name,))
    else:
        cur.execute("""
            SELECT p.completed_lessons
            FROM progress p
            JOIN users u ON u.username = p.username
            WHERE (u.is_demo = 0 OR u.is_demo IS NULL)
        """)
    rows = cur.fetchall()
    conn.close()

    if quest_ids is not None:
        quest_counts = {qid: 0 for qid in quest_ids}
        for (lessons_json,) in rows:
            for lesson in json.loads(lessons_json):
                if lesson in quest_counts:
                    quest_counts[lesson] += 1
        return quest_counts

    # No quest_ids given — build the dict from whatever appears in the data.
    quest_counts = {}
    for (lessons_json,) in rows:
        for lesson in json.loads(lessons_json):
            quest_counts[lesson] = quest_counts.get(lesson, 0) + 1
    return quest_counts

def delete_user_data(username):
    """Delete a user and all their associated data."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("DELETE FROM users WHERE username=?"), (username,))
    cur.execute(adapt("DELETE FROM progress WHERE username=?"), (username,))
    cur.execute(adapt("DELETE FROM quest_times WHERE username=?"), (username,))
    cur.execute(adapt("DELETE FROM password_resets WHERE username=?"), (username,))
    cur.execute(adapt("DELETE FROM progress_shares WHERE username=?"), (username,))
    conn.commit()
    conn.close()


def create_progress_share(username, days=30):
    """Create a revocable, read-only token for a student's progress summary."""
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=days)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("""
        INSERT INTO progress_shares (token_hash, username, expires_at)
        VALUES (?, ?, ?)
    """), (token_hash, username, expires_at))
    conn.commit()
    conn.close()
    return token


def get_shared_progress(token):
    """Return a minimal progress summary for a valid share token."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("""
        SELECT u.full_name, u.school, u.class_name, p.points, p.badges,
               p.completed_lessons, s.expires_at
        FROM progress_shares s
        JOIN users u ON u.username = s.username
        LEFT JOIN progress p ON p.username = s.username
        WHERE s.token_hash = ?
    """), (_hash_token(token),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    full_name, school, class_name, points, badges, lessons, expires_at = row
    if expires_at and datetime.fromisoformat(str(expires_at)) < datetime.utcnow():
        return None
    return {
        "full_name": full_name,
        "school": school or "",
        "class_name": class_name or "",
        "points": points or 0,
        "badges": _parse_json_list(badges),
        "completed_lessons": _parse_json_list(lessons),
        "expires_at": expires_at,
    }


# =============================================================================
# EMAIL VERIFICATION
# Tokens are random, stored as hashes, expire, and are single-use.
# =============================================================================

def create_email_verification_token(username, email):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("SELECT username, email, email_verified FROM users WHERE username = ?"), (username,))
    row = cur.fetchone()
    if not row or row[1].strip().lower() != email.strip().lower() or bool(row[2]):
        conn.close()
        return None

    cur.execute(adapt("DELETE FROM email_verifications WHERE username = ?"), (username,))
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS)
    cur.execute(
        adapt("INSERT INTO email_verifications (username, token_hash, expires_at, used) VALUES (?, ?, ?, 0)"),
        (username, _hash_token(token), expires_at),
    )
    conn.commit()
    conn.close()
    return token


def verify_email_token(token):
    """Verify an email token once, using a conditional update to prevent replay races."""
    if not token:
        return False
    token_hash = _hash_token(token)
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(adapt("SELECT username, expires_at, used FROM email_verifications WHERE token_hash = ?"),
                    (token_hash,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        username, expires_at, used = row
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                conn.close()
                return False
        if used or expires_at < datetime.utcnow():
            conn.close()
            return False

        cur.execute(adapt("UPDATE email_verifications SET used = 1 WHERE token_hash = ? AND used = 0"),
                    (token_hash,))
        if cur.rowcount != 1:
            conn.rollback()
            conn.close()
            return False
        cur.execute(adapt("UPDATE users SET email_verified = 1 WHERE username = ?"), (username,))
        if cur.rowcount != 1:
            conn.rollback()
            conn.close()
            return False
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_email_verification_status(school_name=None):
    """Return account verification details, scoped to a linked school when provided."""
    conn = _connect()
    cur = conn.cursor()
    query = "SELECT full_name, username, email, role, school, class_name, email_verified FROM users WHERE COALESCE(is_demo, 0) = 0"
    if school_name:
        cur.execute(adapt(query + " AND school = ? ORDER BY role, full_name"), (school_name,))
    else:
        cur.execute(query + " ORDER BY role, full_name")
    rows = cur.fetchall()
    conn.close()
    return [{"full_name": r[0], "username": r[1], "email": r[2], "role": r[3],
             "school": r[4] or "", "class_name": r[5] or "", "email_verified": bool(r[6])} for r in rows]


# =============================================================================
# PASSWORD RESET
#
# We never store the raw token — only a sha256 hash of it — the same way
# passwords are never stored in plaintext. The raw token only ever exists
# in the reset link (emailed, or shown once in "offline" mode).
# =============================================================================

def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_password_reset_token(username, email):
    """
    If username+email match an existing account, create a fresh reset
    token (invalidating any earlier ones for that user) and return the
    raw token. Returns None if the username/email pair doesn't match —
    callers should show the same generic message either way, so this
    can't be used to enumerate which usernames/emails exist.
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("SELECT username, email FROM users WHERE username = ?"), (username,))
    row = cur.fetchone()

    if not row or row[1].strip().lower() != email.strip().lower():
        conn.close()
        return None

    # Invalidate any earlier outstanding tokens for this user.
    cur.execute(adapt("DELETE FROM password_resets WHERE username = ?"), (username,))

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    cur.execute(
        adapt("INSERT INTO password_resets (username, token_hash, expires_at, used) VALUES (?, ?, ?, 0)"),
        (username, _hash_token(token), expires_at),
    )
    conn.commit()
    conn.close()
    return token


def verify_reset_token(token):
    """Return the username for a valid, unexpired, unused token — else None."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        adapt("SELECT username, expires_at, used FROM password_resets WHERE token_hash = ?"),
        (_hash_token(token),),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    username, expires_at, used = row
    if used:
        return None

    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at < datetime.utcnow():
        return None

    return username


def consume_reset_token(token, new_password):
    """Atomically consume a valid reset token and update the account password."""
    if not token:
        return False
    token_hash = _hash_token(token)
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(adapt("SELECT username, expires_at, used FROM password_resets WHERE token_hash = ?"),
                    (token_hash,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        username, expires_at, used = row
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                conn.close()
                return False
        if used or expires_at < datetime.utcnow():
            conn.close()
            return False

        # Conditional update makes token consumption single-use under concurrent requests.
        cur.execute(adapt("UPDATE password_resets SET used = 1 WHERE token_hash = ? AND used = 0"),
                    (token_hash,))
        if cur.rowcount != 1:
            conn.rollback()
            conn.close()
            return False
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        cur.execute(adapt("UPDATE users SET password = ? WHERE username = ?"), (hashed, username))
        if cur.rowcount != 1:
            conn.rollback()
            conn.close()
            return False
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# DEMO / TRIAL ACCOUNT
# =============================================================================

def get_or_create_demo_account():
    """
    Ensure the shared demo account exists (creating it with some sample
    progress the first time it's needed) and return its login() dict.

    Progress made while logged in as this account is intentionally never
    written back to the database — see `is_demo` handling in
    remote_tech_app.py — so it's safe for every visitor to share it.
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("SELECT username FROM users WHERE username = ?"), (DEMO_USERNAME,))
    exists = cur.fetchone() is not None
    conn.close()

    if not exists:
        register_user(
            full_name="Demo Hero",
            username=DEMO_USERNAME,
            email="demo@remotetech.example",
            password=secrets.token_urlsafe(16),  # nobody needs to know this
            avatar="🌟",
            role="student",
            popia_consent=True,
            school="Demo School",
            class_name="Demo Class",
            is_demo=True,
        )
        save_user_progress(
            DEMO_USERNAME,
            points=300,
            badges=["🛒 Spaza Tycoon"],
            completed_lessons={"1", "2"},
        )

    conn = _connect()
    cur = conn.cursor()
    cur.execute(adapt("""
        SELECT id, full_name, username, role, points, badges, completed_lessons, avatar, school, class_name
        FROM users WHERE username = ?
    """), (DEMO_USERNAME,))
    row = cur.fetchone()
    conn.close()

    (user_id, full_name, username, role, points, badges,
     completed_lessons, avatar, school, class_name) = row

    return {
        'user_id': user_id,
        'full_name': full_name,
        'username': username,
        'role': role,
        'points': points or 0,
        'badges': _parse_json_list(badges),
        'completed_lessons': set(_parse_json_list(completed_lessons)),
        'avatar': avatar,
        'school': school or "",
        'class_name': class_name or "",
        'is_demo': True,
    }


# ====================== APPLICATION FEEDBACK ======================

FEEDBACK_STATUSES = ("Open", "Under Review", "Resolved", "Closed")
FEEDBACK_CATEGORIES = (
    "General Feedback",
    "Bug or Technical Problem",
    "User Interface and Design",
    "Performance",
    "Feature Request",
)


def save_application_feedback(username, application_name, rating, category, review):
    """Create or update a registered user's one review per application."""
    if not isinstance(username, str) or not username.strip():
        raise ValueError("You must be logged in to submit feedback.")

    application_name = application_name.strip() if isinstance(application_name, str) else ""
    category = category.strip() if isinstance(category, str) else ""
    review = review.strip() if isinstance(review, str) else ""

    if not application_name:
        raise ValueError("Please select an application.")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5.")
    if category not in FEEDBACK_CATEGORIES:
        raise ValueError("Please select a valid feedback category.")
    if not review:
        raise ValueError("Please enter your feedback.")
    if len(review) > 2000:
        raise ValueError("Feedback cannot exceed 2000 characters.")

    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            adapt("SELECT username, is_demo FROM users WHERE username = ?"),
            (username.strip(),),
        )
        user = cursor.fetchone()
        if not user or bool(user[1]) or username.strip() == DEMO_USERNAME:
            raise ValueError("Only registered, non-demo users can submit feedback.")

        cursor.execute(
            adapt("""
                INSERT INTO application_feedback
                    (username, application_name, rating, category, review)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (username, application_name) DO UPDATE SET
                    rating = excluded.rating,
                    category = excluded.category,
                    review = excluded.review,
                    status = 'Open',
                    created_at = CURRENT_TIMESTAMP
            """),
            (username.strip(), application_name, rating, category, review),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_application_feedback(username):
    """Return only the feedback owned by the given registered username."""
    if not username:
        return []
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(adapt("""
            SELECT id, application_name, rating, category, review, status, created_at
            FROM application_feedback
            WHERE username = ?
            ORDER BY created_at DESC, id DESC
        """), (username,))
        columns = ("id", "application_name", "rating", "category", "review", "status", "created_at")
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_application_feedback(application_name=None, status=None):
    """Return feedback for use by the authorised staff dashboard."""
    conn = _connect()
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, username, application_name, rating, category, review, status, created_at
            FROM application_feedback WHERE 1 = 1
        """
        params = []
        if application_name:
            query += " AND application_name = ?"
            params.append(application_name)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC, id DESC"
        cursor.execute(adapt(query), tuple(params))
        columns = ("id", "username", "application_name", "rating", "category", "review", "status", "created_at")
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_application_feedback_status(feedback_id, status):
    """Update status; the Streamlit page must verify staff role first."""
    if status not in FEEDBACK_STATUSES:
        raise ValueError("Invalid feedback status.")
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(adapt("""
            UPDATE application_feedback SET status = ? WHERE id = ?
        """), (status, feedback_id))
        if cursor.rowcount == 0:
            raise ValueError("Feedback entry was not found.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
