"""
database.py
SQLite persistence layer (Week 3: users and sessions).

Design rules:
- Only the Platform talks to Database. User, Session, etc. never touch it,
  so the domain classes stay unaware of how or where they are stored.
- Every query is parameterized (the ? placeholders). Values are never
  pasted into the SQL string, which prevents SQL injection.
- Database converts between rows and objects: a stored role such as
  "Professor" is turned back into a Professor instance on load.
"""

import sqlite3
from datetime import datetime

from user import Student, TA, Professor
from session import Session

ROLES = {"Student": Student, "TA": TA, "Professor": Professor}


class Database:
    def __init__(self, path="scholarlyhive.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # SQLite leaves this off by default
        self._create_tables()

    def _create_tables(self):
        with self.conn:  # commits on success, rolls back on error
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    school_id     TEXT PRIMARY KEY,
                    name          TEXT NOT NULL,
                    email         TEXT NOT NULL,
                    role          TEXT NOT NULL,
                    password_hash TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token      TEXT PRIMARY KEY,
                    school_id  TEXT NOT NULL REFERENCES users(school_id),
                    start_time TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

    # ---------------------------------------------------------------
    # Users
    # ---------------------------------------------------------------
    def save_user(self, user):
        """Insert or update a user. The role is stored as the class name."""
        with self.conn:
            self.conn.execute(
                """INSERT INTO users (school_id, name, email, role, password_hash)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(school_id) DO UPDATE SET
                       name = excluded.name,
                       email = excluded.email,
                       role = excluded.role,
                       password_hash = excluded.password_hash""",
                (user.school_id, user.name, user.email,
                 type(user).__name__, user.password_hash),
            )

    def get_user(self, school_id):
        """Return one User rebuilt from its row, or None."""
        row = self.conn.execute(
            "SELECT school_id, name, email, role, password_hash "
            "FROM users WHERE school_id = ?", (school_id,)
        ).fetchone()
        return self._row_to_user(row) if row else None

    def load_users(self):
        rows = self.conn.execute(
            "SELECT school_id, name, email, role, password_hash FROM users"
        ).fetchall()
        return [self._row_to_user(row) for row in rows]

    @staticmethod
    def _row_to_user(row):
        school_id, name, email, role, password_hash = row
        user = ROLES[role](name, school_id, email)
        user.password_hash = password_hash  # already hashed - do not hash again
        return user

    # ---------------------------------------------------------------
    # Sessions
    # ---------------------------------------------------------------
    def save_session(self, session):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO sessions (token, school_id, start_time, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (session.token, session.user.school_id,
                 session.start_time.isoformat(), session.expires_at.isoformat()),
            )

    def delete_session(self, token):
        with self.conn:
            self.conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def delete_sessions_for(self, school_id):
        with self.conn:
            self.conn.execute("DELETE FROM sessions WHERE school_id = ?", (school_id,))

    def load_sessions(self, users_by_id):
        """Rebuild Session objects. users_by_id maps school_id -> User object,
        so each restored session points at the same User object Platform holds."""
        rows = self.conn.execute(
            "SELECT token, school_id, start_time, expires_at FROM sessions"
        ).fetchall()
        sessions = []
        for token, school_id, start, expires in rows:
            user = users_by_id.get(school_id)
            if user is None:
                continue
            sessions.append(Session.restore(
                user, token,
                datetime.fromisoformat(start),
                datetime.fromisoformat(expires),
            ))
        return sessions

    def close(self):
        self.conn.close()