"""
user.py
Defines the User hierarchy. User is the parent class holding shared
account data and behavior. Student, TA, and Professor override
permission-related behavior to demonstrate meaningful inheritance.
"""

from security import hash_password, verify_password


class User:
    """Parent class. Shared account data and default permissions."""

    def __init__(self, name, school_id, email):
        self.name = name
        self.school_id = school_id
        self.email = email
        self.communities = []  # composition: a User has Community memberships
        self.logged_in = False
        self.password_hash = None  # never store the plaintext password

    def set_password(self, password):
        """Hash and store a password (the plaintext is not kept)."""
        self.password_hash = hash_password(password)

    def check_password(self, password):
        """Return True if the given plaintext matches the stored hash."""
        if self.password_hash is None:
            return False
        return verify_password(password, self.password_hash)

    def login(self):
        self.logged_in = True
        print(f"  -> {self.name} logged in.")

    def logout(self):
        self.logged_in = False
        print(f"  -> {self.name} logged out.")

    def join_community(self, community):
        """Asks the community to add this user, then tracks the membership."""
        if community.add_member(self):
            self.communities.append(community)
            print(f"  -> {self.name} joined {community.name}.")
        else:
            print(f"  -> {self.name} could not join {community.name}.")

    def can_verify_resources(self):
        """Default permission: most users cannot verify/pin resources."""
        return False

    def __str__(self):
        return self.name


class Student(User):
    """A standard student account. Uses all default User behavior."""
    pass


class TA(User):
    """A teaching assistant. Can verify resources, same as a Professor."""

    def can_verify_resources(self):
        return True


class Professor(User):
    """A professor account. Can verify resources."""

    def can_verify_resources(self):
        return True