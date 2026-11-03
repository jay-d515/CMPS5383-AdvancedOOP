"""
main.py  (Week 5: interactive CLI)

    python main.py            # start the app
    python main.py --reset    # delete the database and start over

The first run creates the database (scholarlyhive.db) and fills it with demo
accounts. After that, everything you do is saved and is still there next time.
"""

import os
import sys

from database import Database
from campus import Platform
from cli import CLI
from demo_data import seed_demo_data, DEMO_ACCOUNTS

DB_FILE = "scholarlyhive.db"
SHOW_DEMO_ACCOUNTS = True  # set to False to hide the login hints


def print_demo_accounts():
    print("\n  Demo accounts (school ID / password):")
    for school_id, password, name, role in DEMO_ACCOUNTS:
        print(f"    {school_id}  {password:<9} {name} ({role})")


def main():
    if "--reset" in sys.argv:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"Deleted {DB_FILE}.")
        else:
            print("Nothing to delete.")
        return

    db = Database(DB_FILE)
    try:
        platform = Platform(database=db)
        if not platform.users:
            seed_demo_data(platform)
            print("  -> Created the demo accounts, communities and resources.")
        if SHOW_DEMO_ACCOUNTS and platform.find_user("S1001"):
            print_demo_accounts()
        CLI(platform).run()
    finally:
        db.close()


if __name__ == "__main__":
    main()