"""
campus_platform.py
Defines the Platform coordinator. This is what triggers and sequences
interactions between User, Community, Resource, and Session objects -
none of those classes act on their own.

Week 2 adds authentication: register_user() hashes passwords, login()
verifies credentials and starts a Session, and validate_session() /
logout() manage session lifetime.

Week 3 adds persistence: if a Database is supplied, users and sessions are
loaded from it at startup and written to it on every change (write-through).
With no database the Platform behaves exactly as in Week 2 (in-memory only).
"""

from datetime import timedelta

from session import Session


class Platform:
    def __init__(self, session_minutes=30, database=None):
        self.users = []
        self.communities = []
        self.sessions = {}  # token -> Session (in-memory copy of what is stored)
        self.session_duration = timedelta(minutes=session_minutes)
        self.db = database
        if self.db is not None:
            self._load_from_database()

    def _load_from_database(self):
        """Restore users and still-valid sessions saved by a previous run."""
        self.users = self.db.load_users()
        users_by_id = {u.school_id: u for u in self.users}
        for session in self.db.load_sessions(users_by_id):
            if session.is_valid():
                self.sessions[session.token] = session
                session.user.logged_in = True
            else:
                self.db.delete_session(session.token)  # drop stale rows
        print(f"  -> Loaded {len(self.users)} user(s) and "
              f"{len(self.sessions)} active session(s) from the database.")

    # ---------------------------------------------------------------
    # Registration
    # ---------------------------------------------------------------
    def find_user(self, school_id):
        for user in self.users:
            if user.school_id == school_id:
                return user
        return None

    def register_user(self, user, password=None):
        """Add a user. If a password is given, it is hashed before storing."""
        if self.find_user(user.school_id):
            print(f"  -> Registration failed: ID {user.school_id} already exists.")
            return False
        if password is not None:
            user.set_password(password)
        self.users.append(user)
        if self.db is not None:
            self.db.save_user(user)
        print(f"  -> Registered user {user.name}.")
        return True

    def register_community(self, community):
        self.communities.append(community)
        print(f"  -> Created community '{community.name}'.")

    # ---------------------------------------------------------------
    # Authentication / sessions
    # ---------------------------------------------------------------
    def login(self, school_id, password):
        """Verify credentials and start a session. Returns the Session or None."""
        user = self.find_user(school_id)
        # Same message for unknown ID and wrong password, so a failed
        # login doesn't reveal which IDs exist.
        if user is None or not user.check_password(password):
            print("  -> Login failed: invalid credentials.")
            return None

        self._end_sessions_for(user)  # one active session per user
        session = Session(user, duration=self.session_duration)
        self.sessions[session.token] = session
        if self.db is not None:
            self.db.save_session(session)
        user.login()
        print(f"  -> {session}")
        return session

    def validate_session(self, token):
        """Return the User for a valid session token, or None if missing/expired."""
        session = self.sessions.get(token)
        if session is None:
            return None
        if not session.is_valid():
            print(f"  -> Session for {session.user.name} has expired.")
            self._end_sessions_for(session.user)
            return None
        return session.user

    def logout(self, token):
        session = self.sessions.get(token)
        if session is None:
            return
        self._end_sessions_for(session.user)

    def _end_sessions_for(self, user):
        expired = [t for t, s in self.sessions.items() if s.user is user]
        for token in expired:
            del self.sessions[token]
        if self.db is not None:
            self.db.delete_sessions_for(user.school_id)
        if expired and user.logged_in:
            user.logout()

    # ---------------------------------------------------------------
    # Week 1 coordination (unchanged)
    # ---------------------------------------------------------------
    def post_resource(self, user, community, resource):
        """Coordinates a user posting a resource to a community they belong to."""
        if community not in user.communities:
            print(f"  -> {user.name} must join '{community.name}' before posting there.")
            return
        community.post_resource(resource)
        print(f"  -> {user.name} posted '{resource.title}' to '{community.name}'.")

    def verify_resource(self, user, resource):
        """Coordinates a privileged user verifying a resource."""
        if not user.can_verify_resources():
            print(f"  -> {user.name} does not have permission to verify resources.")
            return
        resource.verified = True
        print(f"  -> {user.name} verified '{resource.title}'.")