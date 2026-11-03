"""
cli.py
Command-line interface (Week 5).

The CLI only collects input and shows menus. Every real action goes
through the Platform coordinator, so the rules (who may join, who may
verify, how sessions work) live in one place and a future web front end
can reuse them unchanged.

Input functions are injected (input_fn / password_fn) so tests can feed
scripted keystrokes instead of needing a person at the keyboard.
"""

import getpass

from user import Student
from resource import FileResource, LinkResource, DiscussionPost

MIN_PASSWORD_LENGTH = 8

# (menu label, resource class, prompt for that type's extra field)
RESOURCE_TYPES = [
    ("File", FileResource, "File name (for example notes.pdf)"),
    ("Link", LinkResource, "URL (starting with http:// or https://)"),
    ("Discussion post", DiscussionPost, "Post text"),
]


class CLI:
    def __init__(self, platform, input_fn=input, password_fn=getpass.getpass):
        self.platform = platform
        self._input = input_fn
        self._password = password_fn
        self.token = None      # session token while logged in
        self.user = None       # the User for that session
        self.running = True

    # ---------------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------------
    def run(self):
        print("\n" + "=" * 46)
        print("  ScholarlyHive - campus communities")
        print("=" * 46)
        try:
            while self.running:
                if self.token is None:
                    self._logged_out_menu()
                else:
                    self.user = self._current_user()
                    if self.user is not None:
                        self._logged_in_menu()
        except (EOFError, KeyboardInterrupt):
            print("\n  Input closed.")
        finally:
            if self.token is not None:  # leave no session open on exit
                self.platform.logout(self.token)
                self.token = None
                self.user = None
        print("  Goodbye!")

    def _logged_out_menu(self):
        self._menu("Welcome", [
            ("Log in", self._login),
            ("Register a student account", self._register),
            ("Quit", self._quit),
        ])

    def _logged_in_menu(self):
        options = [
            ("List communities", self._list_communities),
            ("Join a community", self._join_community),
            ("My communities", self._my_communities),
            ("Browse resources", self._browse_resources),
            ("Post a resource", self._post_resource),
        ]
        if self.user.can_verify_resources():
            options.append(("Verify a resource", self._verify_resource))
        options.append(("Log out", self._logout))
        role = type(self.user).__name__
        self._menu(f"Main menu - {self.user.name} ({role})", options, require_session=True)

    # ---------------------------------------------------------------
    # Input helpers
    # ---------------------------------------------------------------
    def _menu(self, title, options, require_session=False):
        """Show numbered options, read a choice, run the chosen handler.

        With require_session=True the session is checked AFTER the choice is
        made, so a session that expired while the menu sat open cannot be used.
        """
        print(f"\n=== {title} ===")
        for number, (label, _) in enumerate(options, start=1):
            print(f"  {number}. {label}")
        raw = self._input("Choose an option: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(options):
            print("  Please enter a number from the menu.")
            return
        if require_session:
            self.user = self._current_user()
            if self.user is None:
                return
        options[int(raw) - 1][1]()

    def _pick(self, prompt, items, label=str):
        """Show numbered items and return the chosen one, or None if cancelled."""
        for number, item in enumerate(items, start=1):
            print(f"  {number}. {label(item)}")
        print("  0. Cancel")
        while True:
            raw = self._input(f"{prompt} (0 to cancel): ").strip()
            if raw in ("", "0"):
                print("  Cancelled.")
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(items):
                return items[int(raw) - 1]
            print("  Invalid choice, try again.")

    def _ask(self, prompt):
        """Read a line of text. Returns None if the user left it blank."""
        value = self._input(f"{prompt}: ").strip()
        return value or None

    def _current_user(self):
        """The User for the active session, or None (and reset) if it expired."""
        user = self.platform.validate_session(self.token)
        if user is None:
            print("  Your session has expired. Please log in again.")
            self.token = None
            self.user = None
        return user

    @staticmethod
    def _community_label(community):
        kind = type(community).__name__.replace("Community", "")
        return f"{community.name} [{kind}] - {len(community.members)} member(s)"

    # ---------------------------------------------------------------
    # Logged-out actions
    # ---------------------------------------------------------------
    def _login(self):
        school_id = self._ask("School ID")
        if school_id is None:
            print("  Cancelled.")
            return
        password = self._password("Password: ")
        session = self.platform.login(school_id, password)
        if session is not None:
            self.token = session.token
            print(f"  Welcome, {session.user.name}!")

    def _register(self):
        name = self._ask("Full name")
        school_id = self._ask("School ID")
        email = self._ask("School email")
        if None in (name, school_id, email):
            print("  Registration cancelled: every field is required.")
            return
        if "@" not in email:
            print("  Registration cancelled: that doesn't look like an email address.")
            return
        if self.platform.find_user(school_id):
            print(f"  School ID {school_id} is already registered.")
            return
        password = self._password(f"Password (at least {MIN_PASSWORD_LENGTH} characters): ")
        if len(password) < MIN_PASSWORD_LENGTH:
            print(f"  Password must be at least {MIN_PASSWORD_LENGTH} characters.")
            return
        if password != self._password("Confirm password: "):
            print("  Passwords did not match.")
            return
        # Self-registration only creates students; staff accounts come from the
        # school's roster (simulated by the demo data), not from a menu choice.
        self.platform.register_user(Student(name, school_id, email), password)
        print("  Account created. You can log in now.")

    def _quit(self):
        self.running = False

    # ---------------------------------------------------------------
    # Logged-in actions
    # ---------------------------------------------------------------
    def _logout(self):
        self.platform.logout(self.token)
        self.token = None
        self.user = None
        print("  You are logged out.")

    def _list_communities(self):
        if not self.platform.communities:
            print("  There are no communities yet.")
            return
        print("\n  All communities:")
        for community in self.platform.communities:
            joined = "  (joined)" if community in self.user.communities else ""
            print(f"  - {self._community_label(community)}{joined}")

    def _join_community(self):
        available = [c for c in self.platform.communities if c not in self.user.communities]
        if not available:
            print("  There are no more communities to join.")
            return
        community = self._pick("Community to join", available, self._community_label)
        if community is not None:
            self.platform.join_community(self.user, community)

    def _my_communities(self):
        if not self.user.communities:
            print("  You haven't joined any communities yet.")
            return
        print("\n  Your communities:")
        for community in self.user.communities:
            print(f"  - {community.name}: {len(community.members)} member(s), "
                  f"{len(community.resources)} resource(s)")

    def _choose_joined_community(self, prompt):
        if not self.user.communities:
            print("  You haven't joined any communities yet. Choose 'Join a community' first.")
            return None
        return self._pick(prompt, self.user.communities, lambda c: c.name)

    def _browse_resources(self):
        community = self._choose_joined_community("Community to browse")
        if community is not None:
            print(f"\n  Resources in {community.name}:")
            community.show_resources()  # polymorphic: each type displays itself

    def _post_resource(self):
        community = self._choose_joined_community("Post to which community")
        if community is None:
            return
        print("  What are you sharing?")
        kind = self._pick("Resource type", RESOURCE_TYPES, lambda t: t[0])
        if kind is None:
            return
        _, resource_class, detail_prompt = kind
        title = self._ask("Title")
        if title is None:
            print("  Cancelled: a title is required.")
            return
        detail = self._ask(detail_prompt)
        if detail is None:
            print("  Cancelled: that field is required.")
            return
        if resource_class is LinkResource and not detail.startswith(("http://", "https://")):
            print("  Cancelled: a link must start with http:// or https://")
            return
        self.platform.post_resource(self.user, community, resource_class(title, self.user, detail))

    def _verify_resource(self):
        community = self._choose_joined_community("Community to review")
        if community is None:
            return
        pending = [r for r in community.resources if not r.verified]
        if not pending:
            print("  There is nothing waiting to be verified in that community.")
            return
        resource = self._pick("Resource to verify", pending,
                              lambda r: f"{r.title} (by {r.uploader.name})")
        if resource is not None:
            self.platform.verify_resource(self.user, resource)