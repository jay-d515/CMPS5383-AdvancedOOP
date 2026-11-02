"""
session.py
Defines the Session class. A Session records when a user logged in and
when that login expires. Time-based logic lives here (not in User) so the
rest of the system just asks session.is_valid().
"""

import secrets
from datetime import datetime, timedelta


class Session:
    DEFAULT_DURATION = timedelta(minutes=30)

    def __init__(self, user, duration=None, start_time=None):
        self.user = user
        self.token = secrets.token_hex(16)  # unguessable session identifier
        self.start_time = start_time or datetime.now()
        self.expires_at = self.start_time + (duration or self.DEFAULT_DURATION)

    def is_valid(self, now=None):
        """A session is valid until its expiration time passes."""
        now = now or datetime.now()
        return now < self.expires_at

    def __str__(self):
        return (f"Session({self.user.name}, started "
                f"{self.start_time:%H:%M:%S}, expires {self.expires_at:%H:%M:%S})")