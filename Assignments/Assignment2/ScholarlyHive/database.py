"""
database.py
SQLite persistence layer.
  Week 3: users and sessions.
  Week 4: communities, enrollments, memberships, and resources.

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
from community import DepartmentCommunity, CourseCommunity
from resource import FileResource, LinkResource, DiscussionPost

ROLES = {"Student": Student, "TA": TA, "Professor": Professor}

# Subclass-specific field stored in the single "detail" column.
# One table per hierarchy ("single-table inheritance"): the `kind` column
# records the class name, and `detail` holds that class's extra field.
COMMUNITY_DETAIL = {"DepartmentCommunity": "department", "CourseCommunity": "course_code"}
RESOURCE_KINDS = {
    "FileResource": (FileResource, "filename"),
    "LinkResource": (LinkResource, "url"),
    "DiscussionPost": (DiscussionPost, "body"),
}


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
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS communities (
                    id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind   TEXT NOT NULL,
                    name   TEXT NOT NULL UNIQUE,
                    detail TEXT
                )
            """)
            # Enrollment lists may name students who have not registered yet,
            # so enrollments deliberately has no foreign key to users.
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    community_id INTEGER NOT NULL REFERENCES communities(id),
                    school_id    TEXT NOT NULL,
                    PRIMARY KEY (community_id, school_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memberships (
                    community_id INTEGER NOT NULL REFERENCES communities(id),
                    school_id    TEXT NOT NULL REFERENCES users(school_id),
                    PRIMARY KEY (community_id, school_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    community_id INTEGER NOT NULL REFERENCES communities(id),
                    kind         TEXT NOT NULL,
                    title        TEXT NOT NULL,
                    uploader_id  TEXT NOT NULL REFERENCES users(school_id),
                    verified     INTEGER NOT NULL DEFAULT 0,
                    detail       TEXT
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

    # ---------------------------------------------------------------
    # Communities, memberships, resources (Week 4)
    # ---------------------------------------------------------------
    def save_community(self, community):
        """Insert a new community (and its enrollment list) and set community.id."""
        if community.id is not None:
            return  # already saved
        kind = type(community).__name__
        if kind not in COMMUNITY_DETAIL:
            raise ValueError(f"Unsupported community type: {kind}")
        detail = getattr(community, COMMUNITY_DETAIL[kind])
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO communities (kind, name, detail) VALUES (?, ?, ?)",
                (kind, community.name, detail),
            )
            new_id = cursor.lastrowid
            for school_id in getattr(community, "enrolled_ids", []):
                self.conn.execute(
                    "INSERT OR IGNORE INTO enrollments (community_id, school_id) VALUES (?, ?)",
                    (new_id, school_id),
                )
        community.id = new_id  # only set once the transaction succeeded

    def save_membership(self, community, user):
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO memberships (community_id, school_id) VALUES (?, ?)",
                (community.id, user.school_id),
            )

    def save_resource(self, resource, community):
        """Insert a new resource into a saved community and set resource.id."""
        if community.id is None:
            raise ValueError(f"Community '{community.name}' has not been saved yet.")
        kind = type(resource).__name__
        if kind not in RESOURCE_KINDS:
            raise ValueError(f"Unsupported resource type: {kind}")
        _, field = RESOURCE_KINDS[kind]
        with self.conn:
            cursor = self.conn.execute(
                """INSERT INTO resources
                   (community_id, kind, title, uploader_id, verified, detail)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (community.id, kind, resource.title, resource.uploader.school_id,
                 int(resource.verified), getattr(resource, field)),
            )
            new_id = cursor.lastrowid
        resource.id = new_id

    def set_resource_verified(self, resource):
        with self.conn:
            self.conn.execute(
                "UPDATE resources SET verified = ? WHERE id = ?",
                (int(resource.verified), resource.id),
            )

    def load_communities(self, users_by_id):
        """Rebuild every community with its members and resources.

        users_by_id maps school_id -> the User objects the Platform already
        holds, so members and uploaders are the same objects, not copies.
        """
        enrolled = {}
        for community_id, school_id in self.conn.execute(
                "SELECT community_id, school_id FROM enrollments"):
            enrolled.setdefault(community_id, []).append(school_id)

        communities = {}
        for community_id, kind, name, detail in self.conn.execute(
                "SELECT id, kind, name, detail FROM communities ORDER BY id").fetchall():
            if kind == "CourseCommunity":
                community = CourseCommunity(name, detail, enrolled.get(community_id, []))
            elif kind == "DepartmentCommunity":
                community = DepartmentCommunity(name, detail)
            else:
                raise ValueError(f"Unknown community type in database: {kind}")
            community.id = community_id
            communities[community_id] = community

        # Memberships are restored directly. Going through add_member() would
        # re-run the enrollment check and print "joined" messages.
        for community_id, school_id in self.conn.execute(
                "SELECT community_id, school_id FROM memberships ORDER BY rowid").fetchall():
            community, user = communities.get(community_id), users_by_id.get(school_id)
            if community is not None and user is not None:
                community.members.append(user)
                user.communities.append(community)

        for (resource_id, community_id, kind, title, uploader_id,
             verified, detail) in self.conn.execute(
                "SELECT id, community_id, kind, title, uploader_id, verified, detail "
                "FROM resources ORDER BY id").fetchall():
            community, uploader = communities.get(community_id), users_by_id.get(uploader_id)
            if community is None or uploader is None:
                continue
            if kind not in RESOURCE_KINDS:
                raise ValueError(f"Unknown resource type in database: {kind}")
            resource = RESOURCE_KINDS[kind][0](title, uploader, detail)
            resource.id = resource_id
            resource.verified = bool(verified)
            community.resources.append(resource)

        return list(communities.values())

    def close(self):
        self.conn.close()