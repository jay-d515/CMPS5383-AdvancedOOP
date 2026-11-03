"""
testw4.py
Week 4 milestone tests: communities, memberships, and resources persist in
SQLite, so the app's full state survives a restart.

Run from the project root:  python -m unittest discover -s tests -v
"""

import contextlib
import io
import os
import sqlite3
import tempfile
import unittest

from database import Database
from campus import Platform
from community import Community, DepartmentCommunity, CourseCommunity
from resource import Resource, FileResource, LinkResource, DiscussionPost
from user import Student, TA, Professor


class DatabaseTestCase(unittest.TestCase):
    """Fresh temp database file per test, plus a helper that simulates a restart."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "test.db")
        self.opened = []

    def tearDown(self):
        for db in self.opened:
            try:
                db.close()
            except sqlite3.ProgrammingError:
                pass

    def open_platform(self):
        db = Database(self.path)
        self.opened.append(db)
        return Platform(database=db), db

    def restart(self, old_db):
        old_db.close()
        return self.open_platform()


class PopulatedTestCase(DatabaseTestCase):
    """A platform with users, two communities, and joined members."""

    def setUp(self):
        super().setUp()
        self.p, self.db = self.open_platform()
        self.alice = Student("Alice", "S1001", "alice@school.edu")
        self.bob = Student("Bob", "S1002", "bob@school.edu")
        self.prof = Professor("Dr. Lee", "P2001", "lee@school.edu")
        for user in (self.alice, self.bob, self.prof):
            self.p.register_user(user)  # no password: hashing is slow and unneeded here
        self.dept = DepartmentCommunity("Computer Science", "CS")
        self.course = CourseCommunity("Advanced OOP", "CMPS5383",
                                      enrolled_ids=["S1001", "P2001", "S9999"])
        self.p.register_community(self.dept)
        self.p.register_community(self.course)


class TestUpgradeFromWeek3(DatabaseTestCase):
    def test_week3_database_gains_new_tables_and_keeps_users(self):
        """Opening a database made by Week 3 code must not lose its users."""
        raw = sqlite3.connect(self.path)
        raw.executescript("""
            CREATE TABLE users (school_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                email TEXT NOT NULL, role TEXT NOT NULL, password_hash TEXT);
            CREATE TABLE sessions (token TEXT PRIMARY KEY,
                school_id TEXT NOT NULL REFERENCES users(school_id),
                start_time TEXT NOT NULL, expires_at TEXT NOT NULL);
            INSERT INTO users VALUES ('S1001', 'Alice', 'a@s.edu', 'Student', NULL);
        """)
        raw.commit()
        raw.close()

        p, db = self.open_platform()
        tables = {r[0] for r in db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        for name in ("communities", "enrollments", "memberships", "resources"):
            self.assertIn(name, tables)
        self.assertEqual([u.name for u in p.users], ["Alice"])


class TestCommunityPersistence(PopulatedTestCase):
    def test_communities_get_ids(self):
        self.assertIsNotNone(self.dept.id)
        self.assertIsNotNone(self.course.id)
        self.assertNotEqual(self.dept.id, self.course.id)

    def test_department_community_survives_restart(self):
        p2, _ = self.restart(self.db)
        restored = next(c for c in p2.communities if c.name == "Computer Science")
        self.assertIsInstance(restored, DepartmentCommunity)
        self.assertEqual(restored.department, "CS")

    def test_course_community_survives_with_enrollment_list(self):
        p2, _ = self.restart(self.db)
        restored = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertIsInstance(restored, CourseCommunity)
        self.assertEqual(restored.course_code, "CMPS5383")
        self.assertCountEqual(restored.enrolled_ids, ["S1001", "P2001", "S9999"])

    def test_enrollment_rule_still_enforced_after_restart(self):
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        alice, bob = p2.find_user("S1001"), p2.find_user("S1002")
        self.assertTrue(p2.join_community(alice, course))
        self.assertFalse(p2.join_community(bob, course))

    def test_duplicate_community_name_rejected(self):
        before = len(self.p.communities)
        self.assertFalse(self.p.register_community(DepartmentCommunity("Computer Science", "CS")))
        self.assertEqual(len(self.p.communities), before)

    def test_community_order_is_preserved(self):
        p2, _ = self.restart(self.db)
        self.assertEqual([c.name for c in p2.communities], ["Computer Science", "Advanced OOP"])


class TestMembershipPersistence(PopulatedTestCase):
    def test_membership_survives_restart_in_both_directions(self):
        self.p.join_community(self.alice, self.dept)
        p2, _ = self.restart(self.db)
        dept = next(c for c in p2.communities if c.name == "Computer Science")
        alice = p2.find_user("S1001")
        self.assertIn(alice, dept.members)
        self.assertIn(dept, alice.communities)

    def test_restored_members_are_the_platforms_user_objects(self):
        self.p.join_community(self.alice, self.dept)
        p2, _ = self.restart(self.db)
        dept = next(c for c in p2.communities if c.name == "Computer Science")
        self.assertIs(dept.members[0], p2.find_user("S1001"))

    def test_rejected_join_is_not_stored(self):
        self.assertFalse(self.p.join_community(self.bob, self.course))  # not enrolled
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertEqual(course.members, [])

    def test_duplicate_join_stores_one_row(self):
        self.p.join_community(self.alice, self.dept)
        self.p.join_community(self.alice, self.dept)
        count = self.db.conn.execute("SELECT COUNT(*) FROM memberships").fetchone()[0]
        self.assertEqual(count, 1)

    def test_unregistered_user_cannot_join(self):
        stranger = Student("Eve", "S6666", "eve@school.edu")
        self.assertFalse(self.p.join_community(stranger, self.dept))

    def test_cannot_join_unregistered_community(self):
        orphan = DepartmentCommunity("Math", "MATH")
        self.assertFalse(self.p.join_community(self.alice, orphan))


class TestResourcePersistence(PopulatedTestCase):
    def setUp(self):
        super().setUp()
        for user in (self.alice, self.prof):
            self.p.join_community(user, self.course)
        self.p.join_community(self.bob, self.dept)

    def test_all_three_resource_types_survive_restart(self):
        self.p.post_resource(self.alice, self.course,
                             FileResource("Notes", self.alice, "notes.pdf"))
        self.p.post_resource(self.alice, self.course,
                             LinkResource("Docs", self.alice, "https://docs.python.org"))
        self.p.post_resource(self.alice, self.course,
                             DiscussionPost("Help", self.alice, "Stuck on matches()"))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        file_r, link_r, post = course.resources
        self.assertIsInstance(file_r, FileResource)
        self.assertEqual(file_r.filename, "notes.pdf")
        self.assertIsInstance(link_r, LinkResource)
        self.assertEqual(link_r.url, "https://docs.python.org")
        self.assertIsInstance(post, DiscussionPost)
        self.assertEqual(post.body, "Stuck on matches()")

    def test_resources_get_ids_and_keep_posting_order(self):
        titles = ["First", "Second", "Third"]
        for title in titles:
            self.p.post_resource(self.alice, self.course, LinkResource(title, self.alice, "http://x"))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertEqual([r.title for r in course.resources], titles)
        ids = [r.id for r in course.resources]
        self.assertEqual(ids, sorted(ids))
        self.assertTrue(all(i is not None for i in ids))

    def test_resources_attach_to_the_right_community(self):
        self.p.post_resource(self.alice, self.course, FileResource("OOP notes", self.alice, "a.pdf"))
        self.p.post_resource(self.bob, self.dept, LinkResource("CS link", self.bob, "http://cs"))
        p2, _ = self.restart(self.db)
        by_name = {c.name: c for c in p2.communities}
        self.assertEqual([r.title for r in by_name["Advanced OOP"].resources], ["OOP notes"])
        self.assertEqual([r.title for r in by_name["Computer Science"].resources], ["CS link"])

    def test_uploader_is_the_platforms_user_object(self):
        self.p.post_resource(self.alice, self.course, FileResource("Notes", self.alice, "n.pdf"))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertIs(course.resources[0].uploader, p2.find_user("S1001"))

    def test_verified_flag_persists(self):
        notes = FileResource("Notes", self.alice, "n.pdf")
        other = LinkResource("Other", self.alice, "http://x")
        self.p.post_resource(self.alice, self.course, notes)
        self.p.post_resource(self.alice, self.course, other)
        self.assertTrue(self.p.verify_resource(self.prof, notes))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertTrue(course.resources[0].verified)
        self.assertFalse(course.resources[1].verified)

    def test_student_verification_is_denied_and_not_saved(self):
        notes = FileResource("Notes", self.alice, "n.pdf")
        self.p.post_resource(self.alice, self.course, notes)
        self.assertFalse(self.p.verify_resource(self.alice, notes))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertFalse(course.resources[0].verified)

    def test_non_member_post_is_rejected_and_not_saved(self):
        stray = FileResource("Stray", self.bob, "s.pdf")
        self.assertFalse(self.p.post_resource(self.bob, self.course, stray))  # Bob not in course
        self.assertIsNone(stray.id)
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        self.assertEqual(course.resources, [])

    def test_polymorphic_display_works_on_restored_resources(self):
        notes = FileResource("Notes", self.alice, "n.pdf")
        self.p.post_resource(self.alice, self.course, notes)
        self.p.verify_resource(self.prof, notes)
        self.p.post_resource(self.alice, self.course, LinkResource("Docs", self.alice, "http://d"))
        p2, _ = self.restart(self.db)
        course = next(c for c in p2.communities if c.name == "Advanced OOP")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            course.show_resources()
        output = buffer.getvalue()
        self.assertIn("[File] Notes [VERIFIED]", output)
        self.assertIn("[Link] Docs", output)


class TestFullStateRestart(PopulatedTestCase):
    def test_everything_survives_one_restart(self):
        self.p.join_community(self.alice, self.dept)
        self.p.join_community(self.alice, self.course)
        self.p.join_community(self.prof, self.course)
        self.p.post_resource(self.alice, self.course, FileResource("Notes", self.alice, "n.pdf"))
        self.p.post_resource(self.alice, self.dept, DiscussionPost("Hi", self.alice, "Hello"))
        self.p.register_user(Student("Carol", "S3003", "carol@school.edu"), "pw")
        token = self.p.login("S3003", "pw").token

        p2, _ = self.restart(self.db)
        self.assertEqual(len(p2.users), 4)
        self.assertEqual(len(p2.communities), 2)
        self.assertEqual(sum(len(c.members) for c in p2.communities), 3)
        self.assertEqual(sum(len(c.resources) for c in p2.communities), 2)
        self.assertIsNotNone(p2.validate_session(token))


class TestIntegrity(PopulatedTestCase):
    def test_hostile_text_is_stored_as_plain_data(self):
        evil = "x'); DROP TABLE resources; --"
        self.p.join_community(self.alice, self.dept)
        self.p.register_community(DepartmentCommunity(evil, "EVIL"))
        self.p.post_resource(self.alice, self.dept, LinkResource(evil, self.alice, evil))
        p2, _ = self.restart(self.db)
        self.assertTrue(any(c.name == evil for c in p2.communities))
        dept = next(c for c in p2.communities if c.name == "Computer Science")
        self.assertEqual(dept.resources[0].title, evil)

    def test_saving_resource_to_unsaved_community_is_rejected(self):
        orphan = DepartmentCommunity("Math", "MATH")
        with self.assertRaises(ValueError):
            self.db.save_resource(FileResource("F", self.alice, "f.pdf"), orphan)

    def test_foreign_key_blocks_resource_for_missing_community(self):
        ghost = DepartmentCommunity("Ghost", "G")
        ghost.id = 9999  # an id that is not in the table
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_resource(FileResource("F", self.alice, "f.pdf"), ghost)

    def test_foreign_key_blocks_membership_for_unregistered_user(self):
        stranger = Student("Eve", "S6666", "eve@school.edu")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_membership(self.dept, stranger)

    def test_unsupported_resource_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.db.save_resource(Resource("Plain", self.alice), self.dept)

    def test_unsupported_community_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.db.save_community(Community("Plain"))

    def test_platform_without_database_still_works(self):
        p = Platform()
        alice = Student("Alice", "S1001", "a@s.edu")
        p.register_user(alice, "pw")
        dept = DepartmentCommunity("CS", "CS")
        p.register_community(dept)
        self.assertTrue(p.join_community(alice, dept))
        self.assertTrue(p.post_resource(alice, dept, LinkResource("L", alice, "http://l")))
        self.assertEqual(len(dept.resources), 1)


if __name__ == "__main__":
    unittest.main()