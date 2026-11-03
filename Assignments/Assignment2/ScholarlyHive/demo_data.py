"""
demo_data.py
Sample accounts, communities, and resources for demos. This stands in for the
school's real roster (the project simulates school-account login), which is
also why staff accounts (TA/Professor) can only come from here and not from
the registration menu.
"""

import contextlib
import io

from user import Student, TA, Professor
from community import DepartmentCommunity, CourseCommunity
from resource import FileResource, LinkResource, DiscussionPost

# (school id, password, name, role) - shown to the person running the demo
DEMO_ACCOUNTS = [
    ("S1001", "alice-pw", "Alice", "Student"),
    ("S1002", "bob-pw", "Bob", "Student"),
    ("P2001", "lee-pw", "Dr. Lee", "Professor"),
    ("T3001", "tim-pw", "Tim", "TA"),
]


def seed_demo_data(platform, quiet=True):
    """Create the demo users, communities, memberships, and resources."""
    sink = io.StringIO() if quiet else None
    with contextlib.redirect_stdout(sink) if quiet else contextlib.nullcontext():
        alice = Student("Alice", "S1001", "alice@school.edu")
        bob = Student("Bob", "S1002", "bob@school.edu")
        lee = Professor("Dr. Lee", "P2001", "lee@school.edu")
        tim = TA("Tim", "T3001", "tim@school.edu")
        passwords = {a[0]: a[1] for a in DEMO_ACCOUNTS}
        for user in (alice, bob, lee, tim):
            platform.register_user(user, passwords[user.school_id])

        cs = DepartmentCommunity("Computer Science", "CS")
        oop = CourseCommunity("CMPS5383 - Advanced OOP", "CMPS5383",
                              enrolled_ids=["S1001", "P2001", "T3001"])  # Bob is not enrolled
        platform.register_community(cs)
        platform.register_community(oop)

        platform.join_community(alice, cs)
        platform.join_community(bob, cs)
        platform.join_community(alice, oop)
        platform.join_community(lee, oop)
        platform.join_community(tim, oop)

        notes = FileResource("Inheritance Notes", alice, "inheritance_notes.pdf")
        platform.post_resource(alice, oop, notes)
        platform.post_resource(bob, cs, LinkResource(
            "Python OOP Tutorial", bob, "https://docs.python.org/3/tutorial/classes.html"))
        platform.post_resource(alice, oop, DiscussionPost(
            "Help with Assignment 1", alice, "Anyone else stuck on the matches() bug?"))
        platform.verify_resource(lee, notes)