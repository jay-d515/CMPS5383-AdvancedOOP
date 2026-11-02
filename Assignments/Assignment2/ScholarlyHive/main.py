"""
main.py
Entry point for CampusConnect (Week 2 demo).

Shows: password hashing at registration, login success/failure,
session start and expiry, and that the Week 1 features (communities,
posting, verification) still work behind an authenticated login.
"""

from datetime import datetime, timedelta

from user import Student, Professor
from community import DepartmentCommunity, CourseCommunity
from resource import FileResource, DiscussionPost
from campus import Platform


if __name__ == "__main__":
    platform = Platform(session_minutes=30)

    # --- Registration: passwords are hashed, never stored as plaintext ---
    print("== Registration ==")
    alice = Student("Alice", "S1001", "alice@school.edu")
    bob = Student("Bob", "S1002", "bob@school.edu")
    prof_lee = Professor("Dr. Lee", "P2001", "lee@school.edu")

    platform.register_user(alice, password="alice-pass")
    platform.register_user(bob, password="bob-pass")
    platform.register_user(prof_lee, password="lee-pass")
    platform.register_user(Student("Imposter", "S1001", "x@school.edu"), password="pw")

    print(f"\n  Alice's stored value: {alice.password_hash[:45]}...")
    print(f"  Bob's stored value:   {bob.password_hash[:45]}...")

    # --- Login: wrong credentials rejected, correct ones start a session ---
    print("\n== Login ==")
    platform.login("S1001", "wrong-password")
    platform.login("S9999", "alice-pass")
    alice_session = platform.login("S1001", "alice-pass")
    prof_session = platform.login("P2001", "lee-pass")

    # --- Session validation ---
    print("\n== Session validation ==")
    user = platform.validate_session(alice_session.token)
    print(f"  Token resolves to: {user}")

    print("\n  (simulating 31 minutes passing...)")
    alice_session.expires_at = datetime.now() - timedelta(seconds=1)
    print(f"  Token resolves to: {platform.validate_session(alice_session.token)}")

    print("\n  Alice logs in again:")
    alice_session = platform.login("S1001", "alice-pass")

    # --- Week 1 features, now behind authentication ---
    print("\n== Communities and resources ==")
    cs_dept = DepartmentCommunity("Computer Science", "CS")
    oop_course = CourseCommunity("CMPS5383 - Advanced OOP", "CMPS5383",
                                 enrolled_ids=["S1001", "P2001"])
    platform.register_community(cs_dept)
    platform.register_community(oop_course)

    alice.join_community(oop_course)
    bob.join_community(oop_course)        # rejected: not enrolled
    prof_lee.join_community(oop_course)

    notes = FileResource("Inheritance Notes", alice, "inheritance_notes.pdf")
    question = DiscussionPost("Help with Assignment 1", alice, "Anyone stuck on matches()?")
    platform.post_resource(alice, oop_course, notes)
    platform.post_resource(alice, oop_course, question)
    platform.verify_resource(prof_lee, notes)

    print(f"\nResources in {oop_course.name}:")
    oop_course.show_resources()

    # --- Logout ---
    print("\n== Logout ==")
    platform.logout(prof_session.token)
    print(f"  Dr. Lee's token resolves to: {platform.validate_session(prof_session.token)}")