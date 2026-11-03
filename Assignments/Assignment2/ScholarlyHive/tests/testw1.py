"""
test_week1.py
Week 1 milestone tests: core objects can be created and behave correctly.
Run with:  python -m unittest tests.testw1 -v
"""

import unittest

from user import User, Student, TA, Professor
from community import Community, DepartmentCommunity, CourseCommunity
from resource import Resource, FileResource, LinkResource, DiscussionPost, Commentable
from campus import Platform


class TestUserHierarchy(unittest.TestCase):
    def setUp(self):
        self.student = Student("Alice", "S1001", "alice@school.edu")
        self.ta = TA("Tim", "T3001", "tim@school.edu")
        self.prof = Professor("Dr. Lee", "P2001", "lee@school.edu")

    def test_subclasses_inherit_from_user(self):
        for user in (self.student, self.ta, self.prof):
            self.assertIsInstance(user, User)

    def test_student_cannot_verify(self):
        self.assertFalse(self.student.can_verify_resources())

    def test_ta_and_professor_can_verify(self):
        self.assertTrue(self.ta.can_verify_resources())
        self.assertTrue(self.prof.can_verify_resources())

    def test_login_and_logout(self):
        self.student.login()
        self.assertTrue(self.student.logged_in)
        self.student.logout()
        self.assertFalse(self.student.logged_in)


class TestCommunities(unittest.TestCase):
    def setUp(self):
        self.alice = Student("Alice", "S1001", "alice@school.edu")
        self.bob = Student("Bob", "S1002", "bob@school.edu")
        self.dept = DepartmentCommunity("Computer Science", "CS")
        self.course = CourseCommunity("Advanced OOP", "CMPS5383", enrolled_ids=["S1001"])

    def test_department_community_is_open(self):
        self.bob.join_community(self.dept)
        self.assertIn(self.bob, self.dept.members)
        self.assertIn(self.dept, self.bob.communities)

    def test_course_community_accepts_enrolled_student(self):
        self.alice.join_community(self.course)
        self.assertIn(self.alice, self.course.members)

    def test_course_community_rejects_unenrolled_student(self):
        self.bob.join_community(self.course)
        self.assertNotIn(self.bob, self.course.members)
        self.assertNotIn(self.course, self.bob.communities)

    def test_duplicate_join_is_ignored(self):
        self.alice.join_community(self.dept)
        self.alice.join_community(self.dept)
        self.assertEqual(self.dept.members.count(self.alice), 1)
        self.assertEqual(self.alice.communities.count(self.dept), 1)


class TestResources(unittest.TestCase):
    def setUp(self):
        self.alice = Student("Alice", "S1001", "alice@school.edu")
        self.bob = Student("Bob", "S1002", "bob@school.edu")

    def test_resource_subclasses(self):
        file_r = FileResource("Notes", self.alice, "notes.pdf")
        link_r = LinkResource("Docs", self.alice, "https://example.com")
        post = DiscussionPost("Help", self.alice, "Question here")
        for r in (file_r, link_r, post):
            self.assertIsInstance(r, Resource)
            self.assertFalse(r.verified)

    def test_discussion_post_is_commentable(self):
        post = DiscussionPost("Help", self.alice, "Question here")
        self.assertIsInstance(post, Commentable)
        post.add_comment(self.bob, "Try the docs.")
        self.assertEqual(post.comments, [("Bob", "Try the docs.")])

    def test_file_and_link_are_not_commentable_yet(self):
        self.assertNotIsInstance(FileResource("N", self.alice, "n.pdf"), Commentable)
        self.assertNotIsInstance(LinkResource("L", self.alice, "http://x"), Commentable)


class TestPlatformCoordination(unittest.TestCase):
    def setUp(self):
        self.platform = Platform()
        self.alice = Student("Alice", "S1001", "alice@school.edu")
        self.bob = Student("Bob", "S1002", "bob@school.edu")
        self.prof = Professor("Dr. Lee", "P2001", "lee@school.edu")
        self.dept = DepartmentCommunity("Computer Science", "CS")
        for u in (self.alice, self.bob, self.prof):
            self.platform.register_user(u)
        self.platform.register_community(self.dept)

    def test_register_user_and_community(self):
        self.assertEqual(len(self.platform.users), 3)
        self.assertEqual(len(self.platform.communities), 1)

    def test_member_can_post_resource(self):
        self.alice.join_community(self.dept)
        note = FileResource("Notes", self.alice, "notes.pdf")
        self.platform.post_resource(self.alice, self.dept, note)
        self.assertIn(note, self.dept.resources)

    def test_non_member_cannot_post_resource(self):
        note = FileResource("Notes", self.bob, "notes.pdf")
        self.platform.post_resource(self.bob, self.dept, note)
        self.assertNotIn(note, self.dept.resources)

    def test_professor_can_verify_resource(self):
        note = FileResource("Notes", self.alice, "notes.pdf")
        self.platform.verify_resource(self.prof, note)
        self.assertTrue(note.verified)

    def test_student_cannot_verify_resource(self):
        note = FileResource("Notes", self.alice, "notes.pdf")
        self.platform.verify_resource(self.bob, note)
        self.assertFalse(note.verified)


if __name__ == "__main__":
    unittest.main()