"""
test_week2.py
Week 2 milestone tests: password hashing (hashlib) and session
tracking (datetime).
Run with:  python -m unittest tests.testw2 -v
"""

import unittest
from datetime import datetime, timedelta

from security import hash_password, verify_password
from session import Session
from user import Student
from campus import Platform


class TestPasswordHashing(unittest.TestCase):
    def test_hash_is_not_plaintext(self):
        stored = hash_password("hunter2")
        self.assertNotIn("hunter2", stored)

    def test_same_password_gets_different_hashes(self):
        # random salt per hash
        self.assertNotEqual(hash_password("hunter2"), hash_password("hunter2"))

    def test_correct_password_verifies(self):
        stored = hash_password("hunter2")
        self.assertTrue(verify_password("hunter2", stored))

    def test_wrong_password_fails(self):
        stored = hash_password("hunter2")
        self.assertFalse(verify_password("hunter3", stored))

    def test_malformed_hash_fails_safely(self):
        self.assertFalse(verify_password("hunter2", "not-a-real-hash"))
        self.assertFalse(verify_password("hunter2", None))


class TestUserPasswords(unittest.TestCase):
    def test_user_stores_hash_not_plaintext(self):
        alice = Student("Alice", "S1001", "alice@school.edu")
        alice.set_password("secret")
        self.assertNotEqual(alice.password_hash, "secret")
        self.assertTrue(alice.check_password("secret"))
        self.assertFalse(alice.check_password("wrong"))

    def test_user_without_password_cannot_authenticate(self):
        alice = Student("Alice", "S1001", "alice@school.edu")
        self.assertFalse(alice.check_password("anything"))


class TestSession(unittest.TestCase):
    def setUp(self):
        self.alice = Student("Alice", "S1001", "alice@school.edu")

    def test_session_records_start_time_and_expiry(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        s = Session(self.alice, duration=timedelta(minutes=30), start_time=start)
        self.assertEqual(s.start_time, start)
        self.assertEqual(s.expires_at, start + timedelta(minutes=30))

    def test_session_valid_before_expiry(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        s = Session(self.alice, duration=timedelta(minutes=30), start_time=start)
        self.assertTrue(s.is_valid(now=start + timedelta(minutes=29)))

    def test_session_invalid_after_expiry(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        s = Session(self.alice, duration=timedelta(minutes=30), start_time=start)
        self.assertFalse(s.is_valid(now=start + timedelta(minutes=31)))

    def test_tokens_are_unique(self):
        self.assertNotEqual(Session(self.alice).token, Session(self.alice).token)


class TestPlatformAuthentication(unittest.TestCase):
    def setUp(self):
        self.platform = Platform(session_minutes=30)
        self.alice = Student("Alice", "S1001", "alice@school.edu")
        self.platform.register_user(self.alice, password="correct-horse")

    def test_registration_hashes_password(self):
        self.assertIsNotNone(self.alice.password_hash)
        self.assertNotIn("correct-horse", self.alice.password_hash)

    def test_duplicate_school_id_rejected(self):
        imposter = Student("Imposter", "S1001", "x@school.edu")
        self.assertFalse(self.platform.register_user(imposter, password="pw"))
        self.assertEqual(len(self.platform.users), 1)

    def test_login_success_starts_session(self):
        session = self.platform.login("S1001", "correct-horse")
        self.assertIsNotNone(session)
        self.assertTrue(self.alice.logged_in)
        self.assertIn(session.token, self.platform.sessions)

    def test_wrong_password_rejected(self):
        self.assertIsNone(self.platform.login("S1001", "wrong"))
        self.assertFalse(self.alice.logged_in)
        self.assertEqual(self.platform.sessions, {})

    def test_unknown_user_rejected(self):
        self.assertIsNone(self.platform.login("S9999", "correct-horse"))

    def test_valid_session_returns_user(self):
        session = self.platform.login("S1001", "correct-horse")
        self.assertIs(self.platform.validate_session(session.token), self.alice)

    def test_expired_session_is_rejected_and_removed(self):
        session = self.platform.login("S1001", "correct-horse")
        session.expires_at = datetime.now() - timedelta(seconds=1)  # simulate time passing
        self.assertIsNone(self.platform.validate_session(session.token))
        self.assertNotIn(session.token, self.platform.sessions)
        self.assertFalse(self.alice.logged_in)

    def test_logout_ends_session(self):
        session = self.platform.login("S1001", "correct-horse")
        self.platform.logout(session.token)
        self.assertIsNone(self.platform.validate_session(session.token))
        self.assertFalse(self.alice.logged_in)

    def test_relogin_replaces_old_session(self):
        first = self.platform.login("S1001", "correct-horse")
        second = self.platform.login("S1001", "correct-horse")
        self.assertNotIn(first.token, self.platform.sessions)
        self.assertIn(second.token, self.platform.sessions)
        self.assertEqual(len(self.platform.sessions), 1)


if __name__ == "__main__":
    unittest.main()