"""
main.py  (Week 3 demo: persistence)

Run this script TWICE to see persistence across real restarts:

    python main.py            # 1st run: creates users, logs Alice in
    python main.py            # 2nd run: users are recognized from the database
    python main.py --reset    # delete the database and start over

The database file (scholarlyhive.db) is created next to this script.
"""

import os
import sys

from database import Database
from campus import Platform
from user import Student, TA, Professor

DB_FILE = "scholarlyhive.db"


def seed_users(platform):
    print("\n== First run: registering users ==")
    platform.register_user(Student("Alice", "S1001", "alice@school.edu"), "alice-pw")
    platform.register_user(Student("Bob", "S1002", "bob@school.edu"), "bob-pw")
    platform.register_user(Professor("Dr. Lee", "P2001", "lee@school.edu"), "lee-pw")
    platform.register_user(TA("Tim", "T3001", "tim@school.edu"), "tim-pw")


def show_existing_users(platform):
    print("\n== Restart detected: users loaded from the database ==")
    for user in platform.users:
        role = type(user).__name__
        print(f"  {user.school_id:<6} {user.name:<8} {role:<10} "
              f"verify={user.can_verify_resources()}  "
              f"hash={user.password_hash[:30]}...")


def main():
    if "--reset" in sys.argv:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"Deleted {DB_FILE}.")
        else:
            print("Nothing to delete.")
        return

    print("Starting ScholarlyHive...")
    db = Database(DB_FILE)
    platform = Platform(database=db)

    if platform.users:
        show_existing_users(platform)
    else:
        seed_users(platform)

    print("\n== Login ==")
    platform.login("S1001", "wrong-password")           # rejected
    session = platform.login("S1001", "alice-pw")       # accepted, session saved to DB
    print(f"  Alice's session token: {session.token[:12]}...")

    print("\n== Sessions stored in the database ==")
    rows = db.conn.execute(
        "SELECT school_id, substr(token, 1, 12), expires_at FROM sessions").fetchall()
    for school_id, token, expires in rows:
        print(f"  {school_id}  {token}...  expires {expires[:19]}")

    print("\nDone. Run this script again - the users above will already exist.")
    db.close()


if __name__ == "__main__":
    main()