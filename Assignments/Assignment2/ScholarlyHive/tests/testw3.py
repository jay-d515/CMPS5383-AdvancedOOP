"""
test_week3.py
Week 3 milestone tests: users, hashed passwords, and sessions persist in
SQLite, so a "restarted" app still recognizes existing users.

Each test uses a temporary database FILE (not :memory:), because closing
an in-memory database erases it, and a restart is exactly what we test.

Run from the project root:  python -m unittest discover -s tests -v
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from database import Database
from campus import Platform
from session import Session
from user import Student, TA, Professor


class DatabaseTestCase(unittest.TestCase):
    """Gives every test a fresh temp database file and a restart helper."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "test.db")
        self.opened = []

    def tearDown(self):
        # Close every connection so Windows can delete the temp file.
        for db in self.opened:
            try:
                db.close()
            except sqlite3.ProgrammingError:
                pass  # already closed

    def open_platform(self, **kwargs):
        """Open the database and build a Platform on it - like launching the app."""
        db = Database(self.path)
        self.opened.append(db)
        return Platform(database=db, **kwargs), db

    def restart(self, old_db, **kwargs):
        """Close the old connection and start a brand-new Platform on the same file."""
        old_db.close()
        return self.open_platform(**kwargs)


class TestSchema(DatabaseTestCase):
    def test_tables_are_created(self):
        _, db = self.open_platform()
        tables = {row[0] for row in db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertIn("users", tables)
        self.assertIn("sessions", tables)

    def test_opening_twice_does_not_wipe_data(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "a@school.edu"), "pw")
        p2, _ = self.restart(db)
        self.assertEqual(len(p2.users), 1)


class TestUserPersistence(DatabaseTestCase):
    def test_user_survives_restart(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "alice@school.edu"), "secret")
        p2, _ = self.restart(db)
        alice = p2.find_user("S1001")
        self.assertIsNotNone(alice)
        self.assertEqual(alice.name, "Alice")
        self.assertEqual(alice.email, "alice@school.edu")

    def test_role_is_restored_as_correct_subclass(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1", "a@s.edu"), "pw")
        p.register_user(TA("Tim", "T1", "t@s.edu"), "pw")
        p.register_user(Professor("Dr. Lee", "P1", "l@s.edu"), "pw")
        p2, _ = self.restart(db)
        self.assertIsInstance(p2.find_user("S1"), Student)
        self.assertIsInstance(p2.find_user("T1"), TA)
        self.assertIsInstance(p2.find_user("P1"), Professor)
        # Role behavior comes back with the subclass, not just the label.
        self.assertFalse(p2.find_user("S1").can_verify_resources())
        self.assertTrue(p2.find_user("P1").can_verify_resources())

    def test_plaintext_password_is_never_stored(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "a@s.edu"), "hunter2-secret")
        row = db.conn.execute("SELECT * FROM users").fetchone()
        self.assertNotIn("hunter2-secret", " ".join(str(c) for c in row))
        self.assertTrue(row[4].startswith("pbkdf2_sha256$"))

    def test_login_works_after_restart(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "a@s.edu"), "correct-pw")
        p2, _ = self.restart(db)
        self.assertIsNotNone(p2.login("S1001", "correct-pw"))

    def test_wrong_password_still_rejected_after_restart(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "a@s.edu"), "correct-pw")
        p2, _ = self.restart(db)
        self.assertIsNone(p2.login("S1001", "wrong-pw"))

    def test_duplicate_id_rejected_after_restart(self):
        p, db = self.open_platform()
        p.register_user(Student("Alice", "S1001", "a@s.edu"), "pw")
        p2, _ = self.restart(db)
        self.assertFalse(p2.register_user(Student("Imposter", "S1001", "x@s.edu"), "pw"))
        self.assertEqual(len(p2.users), 1)
        self.assertEqual(p2.find_user("S1001").name, "Alice")

    def test_get_user_returns_none_for_unknown_id(self):
        _, db = self.open_platform()
        self.assertIsNone(db.get_user("nobody"))


class TestSessionPersistence(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.p, self.db = self.open_platform()
        self.p.register_user(Student("Alice", "S1001", "a@s.edu"), "pw")

    def test_session_survives_restart(self):
        token = self.p.login("S1001", "pw").token
        p2, _ = self.restart(self.db)
        user = p2.validate_session(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Alice")

    def test_restored_session_keeps_original_times(self):
        session = self.p.login("S1001", "pw")
        p2, _ = self.restart(self.db)
        restored = p2.sessions[session.token]
        self.assertEqual(restored.start_time, session.start_time)
        self.assertEqual(restored.expires_at, session.expires_at)

    def test_restored_session_points_at_platform_user_object(self):
        token = self.p.login("S1001", "pw").token
        p2, _ = self.restart(self.db)
        self.assertIs(p2.sessions[token].user, p2.find_user("S1001"))

    def test_expired_session_is_not_restored_and_is_deleted(self):
        user = self.p.find_user("S1001")
        old = Session(user, start_time=datetime.now() - timedelta(hours=2),
                      duration=timedelta(minutes=30))
        self.db.save_session(old)
        p2, db2 = self.restart(self.db)
        self.assertNotIn(old.token, p2.sessions)
        count = db2.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(count, 0)

    def test_logout_removes_session_from_database(self):
        token = self.p.login("S1001", "pw").token
        self.p.logout(token)
        p2, _ = self.restart(self.db)
        self.assertIsNone(p2.validate_session(token))

    def test_relogin_leaves_only_one_session_row(self):
        self.p.login("S1001", "pw")
        self.p.login("S1001", "pw")
        count = self.db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_expiry_during_run_removes_row(self):
        session = self.p.login("S1001", "pw")
        session.expires_at = datetime.now() - timedelta(seconds=1)
        self.assertIsNone(self.p.validate_session(session.token))
        count = self.db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(count, 0)


class TestDatabaseSafety(DatabaseTestCase):
    def test_sql_injection_text_is_stored_as_plain_data(self):
        """Parameterized queries mean hostile input is just a string."""
        p, db = self.open_platform()
        hostile = "S1'; DROP TABLE users; --"
        p.register_user(Student("Mallory", hostile, "m@s.edu"), "pw")
        p2, _ = self.restart(db)
        self.assertIsNotNone(p2.find_user(hostile))
        tables = {r[0] for r in p2.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertIn("users", tables)

    def test_session_for_nonexistent_user_is_rejected(self):
        """The foreign key stops sessions pointing at users that don't exist."""
        _, db = self.open_platform()
        ghost = Student("Ghost", "NOPE", "g@s.edu")
        with self.assertRaises(sqlite3.IntegrityError):
            db.save_session(Session(ghost))

    def test_platform_without_database_still_works(self):
        p = Platform()
        p.register_user(Student("Alice", "S1001", "a@s.edu"), "pw")
        self.assertIsNotNone(p.login("S1001", "pw"))


if __name__ == "__main__":
    unittest.main()