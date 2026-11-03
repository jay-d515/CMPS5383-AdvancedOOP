"""
test_week5.py
Week 5 milestone tests: a user can log in through the CLI and navigate the
menus interactively. Keystrokes are scripted, so no one needs to type.

Run from the project root:  python -m unittest discover -s tests -v
"""

import contextlib
import io
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from cli import CLI
from campus import Platform
from community import DepartmentCommunity, CourseCommunity
from database import Database
from demo_data import seed_demo_data, DEMO_ACCOUNTS
from resource import FileResource, LinkResource, DiscussionPost
from security import hash_password
from user import Student, TA, Professor

PASSWORD = "password1"
HASH = hash_password(PASSWORD)  # hashed once; hashing is deliberately slow

# Menu numbers. Students have 6 options, staff have 7 (extra "Verify").
LOGIN, REGISTER, QUIT = "1", "2", "3"
LIST, JOIN, MINE, BROWSE, POST = "1", "2", "3", "4", "5"
VERIFY, STAFF_LOGOUT, STUDENT_LOGOUT = "6", "7", "6"


class ScriptedInput:
    """Stands in for input(): hands back scripted lines, then raises EOFError.

    hooks maps a call number to a function run just before that call returns,
    which lets a test change the world mid-session (for example, expire it).
    """

    def __init__(self, *lines, hooks=None):
        self.lines = list(lines)
        self.hooks = hooks or {}
        self.calls = 0
        self.prompts = []

    def __call__(self, prompt=""):
        self.prompts.append(prompt)
        if self.calls in self.hooks:
            self.hooks[self.calls]()
        self.calls += 1
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


class CLITestCase(unittest.TestCase):
    """A platform on a temp database file with three users and two communities."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "test.db")
        self.dbs = []
        self.platform = self.open_platform()

        self.alice = self.make_user(Student, "Alice", "S1001")
        self.bob = self.make_user(Student, "Bob", "S1002")
        self.lee = self.make_user(Professor, "Dr. Lee", "P2001")
        self.dept = DepartmentCommunity("Computer Science", "CS")
        self.course = CourseCommunity("Advanced OOP", "CMPS5383",
                                      enrolled_ids=["S1001", "P2001"])  # Bob not enrolled
        quiet(self.platform.register_community, self.dept)
        quiet(self.platform.register_community, self.course)

    def tearDown(self):
        for db in self.dbs:
            try:
                db.close()
            except sqlite3.ProgrammingError:
                pass

    def open_platform(self):
        db = Database(self.path)
        self.dbs.append(db)
        return quiet(Platform, database=db)

    def restart(self):
        self.dbs[-1].close()
        return self.open_platform()

    def make_user(self, user_class, name, school_id):
        user = user_class(name, school_id, f"{name.split()[-1].lower()}@school.edu")
        user.password_hash = HASH
        quiet(self.platform.register_user, user)
        return user

    def run_cli(self, lines, passwords=(), hooks=None, platform=None):
        """Run the CLI on scripted input. Returns (printed output, cli)."""
        cli = CLI(platform or self.platform,
                  input_fn=ScriptedInput(*lines, hooks=hooks),
                  password_fn=ScriptedInput(*passwords))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.run()
        return buffer.getvalue(), cli


class TestLoggedOutMenu(CLITestCase):
    def test_login_then_logout_then_quit(self):
        out, cli = self.run_cli([LOGIN, "S1001", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Welcome, Alice!", out)
        self.assertIn("Main menu - Alice (Student)", out)
        self.assertIn("You are logged out.", out)
        self.assertIsNone(cli.token)
        self.assertEqual(self.platform.sessions, {})

    def test_wrong_password_stays_logged_out(self):
        out, cli = self.run_cli([LOGIN, "S1001", QUIT], ["not-the-password"])
        self.assertIn("invalid credentials", out)
        self.assertNotIn("Main menu", out)
        self.assertIsNone(cli.token)

    def test_unknown_id_gets_the_same_message(self):
        out, _ = self.run_cli([LOGIN, "NOPE", QUIT], ["whatever1"])
        self.assertIn("invalid credentials", out)

    def test_blank_school_id_cancels_login(self):
        out, _ = self.run_cli([LOGIN, "", QUIT])
        self.assertIn("Cancelled.", out)

    def test_bad_menu_input_does_not_crash(self):
        out, _ = self.run_cli(["abc", "9", "", "-1", QUIT])
        self.assertEqual(out.count("Please enter a number from the menu."), 4)
        self.assertIn("Goodbye!", out)

    def test_input_running_out_exits_cleanly(self):
        out, _ = self.run_cli([])
        self.assertIn("Goodbye!", out)

    def test_ctrl_c_while_logged_in_ends_the_session(self):
        def interrupt():
            raise KeyboardInterrupt
        out, cli = self.run_cli([LOGIN, "S1001"], [PASSWORD], hooks={2: interrupt})
        self.assertIn("Goodbye!", out)
        self.assertIsNone(cli.token)
        self.assertEqual(self.platform.sessions, {})


class TestRegistration(CLITestCase):
    def test_new_student_can_register_then_log_in(self):
        out, _ = self.run_cli(
            [REGISTER, "New Person", "S5000", "np@school.edu",
             LOGIN, "S5000", STUDENT_LOGOUT, QUIT],
            ["longenough1", "longenough1", "longenough1"])
        user = self.platform.find_user("S5000")
        self.assertIsInstance(user, Student)
        self.assertIn("Account created", out)
        self.assertIn("Welcome, New Person!", out)

    def test_registration_is_saved_to_the_database(self):
        self.run_cli([REGISTER, "New Person", "S5000", "np@school.edu", QUIT],
                     ["longenough1", "longenough1"])
        restarted = self.restart()
        self.assertIsNotNone(restarted.find_user("S5000"))

    def test_short_password_is_rejected(self):
        out, _ = self.run_cli([REGISTER, "New Person", "S5000", "np@school.edu", QUIT],
                              ["short"])
        self.assertIn("at least 8 characters", out)
        self.assertIsNone(self.platform.find_user("S5000"))

    def test_mismatched_confirmation_is_rejected(self):
        out, _ = self.run_cli([REGISTER, "New Person", "S5000", "np@school.edu", QUIT],
                              ["longenough1", "different-pw1"])
        self.assertIn("did not match", out)
        self.assertIsNone(self.platform.find_user("S5000"))

    def test_duplicate_id_is_rejected_before_asking_for_a_password(self):
        out, cli = self.run_cli([REGISTER, "Imposter", "S1001", "x@school.edu", QUIT])
        self.assertIn("already registered", out)
        self.assertEqual(cli._password.prompts, [])
        self.assertEqual(self.platform.find_user("S1001").name, "Alice")

    def test_blank_field_cancels(self):
        out, _ = self.run_cli([REGISTER, "New Person", "", "np@school.edu", QUIT])
        self.assertIn("every field is required", out)

    def test_email_without_at_sign_is_rejected(self):
        out, _ = self.run_cli([REGISTER, "New Person", "S5000", "not-an-email", QUIT])
        self.assertIn("doesn't look like an email", out)
        self.assertIsNone(self.platform.find_user("S5000"))

    def test_registration_only_ever_creates_students(self):
        self.run_cli([REGISTER, "Sneaky", "S5001", "s@school.edu", QUIT],
                     ["longenough1", "longenough1"])
        self.assertIs(type(self.platform.find_user("S5001")), Student)


class TestMenuByRole(CLITestCase):
    def test_student_menu_has_no_verify_option(self):
        out, _ = self.run_cli([LOGIN, "S1001", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertNotIn("Verify a resource", out)

    def test_professor_menu_has_verify_option(self):
        out, _ = self.run_cli([LOGIN, "P2001", STAFF_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Verify a resource", out)
        self.assertIn("Main menu - Dr. Lee (Professor)", out)

    def test_students_cannot_reach_the_verify_slot(self):
        out, _ = self.run_cli([LOGIN, "S1001", VERIFY, STUDENT_LOGOUT, QUIT], [PASSWORD])
        # "6" on the student menu is Log out, and there is no 7th option
        out2, _ = self.run_cli([LOGIN, "S1001", "7", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Please enter a number from the menu.", out2)


class TestCommunityMenus(CLITestCase):
    def test_list_communities_marks_joined_ones(self):
        quiet(self.platform.join_community, self.alice, self.dept)
        out, _ = self.run_cli([LOGIN, "S1001", LIST, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Computer Science [Department] - 1 member(s)  (joined)", out)
        self.assertIn("Advanced OOP [Course] - 0 member(s)", out)
        self.assertNotIn("Advanced OOP [Course] - 0 member(s)  (joined)", out)

    def test_join_a_community_is_saved(self):
        out, _ = self.run_cli([LOGIN, "S1001", JOIN, "1", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Alice joined Computer Science.", out)
        restarted = self.restart()
        dept = next(c for c in restarted.communities if c.name == "Computer Science")
        self.assertEqual([m.name for m in dept.members], ["Alice"])

    def test_unenrolled_student_is_turned_away_from_a_course(self):
        out, _ = self.run_cli([LOGIN, "S1002", JOIN, "2", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("not enrolled", out)
        self.assertEqual(self.course.members, [])

    def test_invalid_pick_asks_again(self):
        out, _ = self.run_cli(
            [LOGIN, "S1001", JOIN, "abc", "99", "1", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertEqual(out.count("Invalid choice, try again."), 2)
        self.assertIn("Alice joined Computer Science.", out)

    def test_cancelling_a_join_changes_nothing(self):
        out, _ = self.run_cli([LOGIN, "S1001", JOIN, "0", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Cancelled.", out)
        self.assertEqual(self.alice.communities, [])

    def test_joined_communities_disappear_from_the_join_list(self):
        quiet(self.platform.join_community, self.alice, self.dept)
        quiet(self.platform.join_community, self.alice, self.course)
        out, _ = self.run_cli([LOGIN, "S1001", JOIN, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("no more communities to join", out)

    def test_my_communities_when_empty_and_when_joined(self):
        out, _ = self.run_cli([LOGIN, "S1001", MINE, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("haven't joined any communities yet", out)
        quiet(self.platform.join_community, self.alice, self.dept)
        out, _ = self.run_cli([LOGIN, "S1001", MINE, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Computer Science: 1 member(s), 0 resource(s)", out)


class TestPostingAndBrowsing(CLITestCase):
    def setUp(self):
        super().setUp()
        quiet(self.platform.join_community, self.alice, self.dept)

    def post(self, type_choice, title, detail):
        return self.run_cli(
            [LOGIN, "S1001", POST, "1", type_choice, title, detail, STUDENT_LOGOUT, QUIT],
            [PASSWORD])

    def test_each_resource_type_can_be_posted_and_is_saved(self):
        cases = [
            ("1", "Notes", "notes.pdf", FileResource, "filename"),
            ("2", "Docs", "https://docs.python.org", LinkResource, "url"),
            ("3", "Question", "Anyone free to study?", DiscussionPost, "body"),
        ]
        for type_choice, title, detail, resource_class, field in cases:
            with self.subTest(resource=resource_class.__name__):
                out, _ = self.post(type_choice, title, detail)
                self.assertIn(f"posted '{title}' to 'Computer Science'", out)
        restarted = self.restart()
        dept = next(c for c in restarted.communities if c.name == "Computer Science")
        self.assertEqual(len(dept.resources), 3)
        for resource, (_, title, detail, resource_class, field) in zip(dept.resources, cases):
            self.assertIsInstance(resource, resource_class)
            self.assertEqual(resource.title, title)
            self.assertEqual(getattr(resource, field), detail)
            self.assertEqual(resource.uploader.name, "Alice")

    def test_link_must_look_like_a_url(self):
        out, _ = self.post("2", "Bad link", "ftp://nope")
        self.assertIn("must start with http://", out)
        self.assertEqual(self.dept.resources, [])

    def test_blank_title_cancels(self):
        out, _ = self.post("1", "", "notes.pdf")
        self.assertIn("a title is required", out)
        self.assertEqual(self.dept.resources, [])

    def test_blank_detail_cancels(self):
        out, _ = self.post("1", "Notes", "")
        self.assertIn("that field is required", out)
        self.assertEqual(self.dept.resources, [])

    def test_cancelling_at_the_type_prompt_posts_nothing(self):
        out, _ = self.run_cli([LOGIN, "S1001", POST, "1", "0", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Cancelled.", out)
        self.assertEqual(self.dept.resources, [])

    def test_posting_with_no_joined_community_explains_why(self):
        out, _ = self.run_cli([LOGIN, "S1002", POST, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Choose 'Join a community' first", out)

    def test_browse_shows_each_resource_in_its_own_format(self):
        quiet(self.platform.post_resource, self.alice, self.dept,
              FileResource("Notes", self.alice, "notes.pdf"))
        quiet(self.platform.post_resource, self.alice, self.dept,
              LinkResource("Docs", self.alice, "https://docs.python.org"))
        out, _ = self.run_cli([LOGIN, "S1001", BROWSE, "1", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("[File] Notes", out)
        self.assertIn("[Link] Docs", out)

    def test_browse_requires_a_joined_community(self):
        out, _ = self.run_cli([LOGIN, "S1002", BROWSE, STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("haven't joined any communities yet", out)

    def test_full_journey_in_one_session(self):
        """Log in, join, post, browse, log out - then check it all survived a restart."""
        out, _ = self.run_cli(
            [LOGIN, "S1001",
             JOIN, "1",                        # joins the only community left: Advanced OOP
             POST, "2", "3", "Study group", "Meet Friday at noon",
             BROWSE, "2",
             STUDENT_LOGOUT, QUIT],
            [PASSWORD])
        self.assertIn("[Discussion] Study group", out)
        restarted = self.restart()
        course = next(c for c in restarted.communities if c.name == "Advanced OOP")
        self.assertEqual([r.title for r in course.resources], ["Study group"])


class TestVerifyMenu(CLITestCase):
    def setUp(self):
        super().setUp()
        quiet(self.platform.join_community, self.alice, self.course)
        quiet(self.platform.join_community, self.lee, self.course)
        self.notes = FileResource("Notes", self.alice, "notes.pdf")
        quiet(self.platform.post_resource, self.alice, self.course, self.notes)

    def test_professor_can_verify_and_it_is_saved(self):
        out, _ = self.run_cli([LOGIN, "P2001", VERIFY, "1", "1", STAFF_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("Dr. Lee verified 'Notes'", out)
        restarted = self.restart()
        course = next(c for c in restarted.communities if c.name == "Advanced OOP")
        self.assertTrue(course.resources[0].verified)

    def test_verified_resources_leave_the_pending_list(self):
        quiet(self.platform.verify_resource, self.lee, self.notes)
        out, _ = self.run_cli([LOGIN, "P2001", VERIFY, "1", STAFF_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("nothing waiting to be verified", out)

    def test_cancelling_leaves_the_resource_unverified(self):
        self.run_cli([LOGIN, "P2001", VERIFY, "1", "0", STAFF_LOGOUT, QUIT], [PASSWORD])
        self.assertFalse(self.notes.verified)

    def test_verified_discussion_post_shows_the_tag_too(self):
        post = DiscussionPost("Question", self.alice, "Anyone free to study?")
        quiet(self.platform.post_resource, self.alice, self.course, post)
        quiet(self.platform.verify_resource, self.lee, post)
        out, _ = self.run_cli([LOGIN, "S1001", BROWSE, "1", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("[Discussion] Question [VERIFIED]", out)

    def test_verified_tag_shows_when_browsing(self):
        quiet(self.platform.verify_resource, self.lee, self.notes)
        out, _ = self.run_cli([LOGIN, "S1001", BROWSE, "1", STUDENT_LOGOUT, QUIT], [PASSWORD])
        self.assertIn("[File] Notes [VERIFIED]", out)


class TestSessionHandling(CLITestCase):
    def test_session_that_expires_at_the_menu_blocks_the_action(self):
        def expire():
            for session in self.platform.sessions.values():
                session.expires_at = datetime.now() - timedelta(seconds=1)
        # Call 0 = menu, 1 = school ID, 2 = the logged-in menu choice (hook fires first).
        out, cli = self.run_cli([LOGIN, "S1001", JOIN, QUIT], [PASSWORD], hooks={2: expire})
        self.assertIn("expired", out)
        self.assertIsNone(cli.token)
        self.assertEqual(self.alice.communities, [])   # the join never ran
        self.assertIn("=== Welcome ===", out.split("expired")[-1])  # back at the login menu

    def test_logging_in_again_after_expiry_works(self):
        def expire():
            for session in self.platform.sessions.values():
                session.expires_at = datetime.now() - timedelta(seconds=1)
        out, _ = self.run_cli(
            [LOGIN, "S1001", JOIN, LOGIN, "S1001", STUDENT_LOGOUT, QUIT],
            [PASSWORD, PASSWORD], hooks={2: expire})
        self.assertEqual(out.count("Welcome, Alice!"), 2)


class TestDemoData(unittest.TestCase):
    def test_seed_demo_data_builds_the_expected_state_quietly(self):
        platform = Platform()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            seed_demo_data(platform)
        self.assertEqual(buffer.getvalue(), "")
        self.assertEqual({u.school_id for u in platform.users},
                         {account[0] for account in DEMO_ACCOUNTS})
        self.assertEqual(len(platform.communities), 2)
        self.assertEqual(sum(len(c.resources) for c in platform.communities), 3)

    def test_listed_demo_passwords_really_work(self):
        platform = Platform()
        seed_demo_data(platform)
        for school_id, password, _, _ in DEMO_ACCOUNTS:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNotNone(platform.login(school_id, password), school_id)


if __name__ == "__main__":
    unittest.main()