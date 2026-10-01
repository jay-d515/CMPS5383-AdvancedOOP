from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime

# -------------------------------------------------------------
# Users
# -------------------------------------------------------------
class User:
    """Parent class. Subclasses overried the permission methods."""
    role = "User"
    
    def __init__(self, name:str, school_id:str, email:str,
                 password:str, department:str):
        self.name = name
        self.school_id = school_id
        self.email = email.lower()
        self.department = department
        self._salt = os.urandom(16)
        self._password_hash = self._hash(password)
        self.communities: list[Community] = []
        
    def _hash(self, password:str) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode(),
                                   self._salt, 100_000)
    
    def check_password(self, password:str) -> bool:
        return self._hash(password) == self._password_hash
    
    # -- Permission methods to be overridden by subclasses --
    def can_create_community(self) -> bool:
        """Can this user create a community?"""
        return False
    
    def can_moderate(self) -> bool:
        """Can this user remove other people's posts?"""
        return False
    
    def profile(self) -> str:
        names = ", ".join(c.name for c in self.communities) or "none yet"
        return (f"{self.name} ({self.role})\n"
                f"  Email: {self.email}\n"
                f"  ID: {self.school_id}\n"
                f"  Department: {self.department}\n"
                f"  Communities: {names}")
    
    def __str__(self) -> str:
        return f"<{self.role} {self.name}>"
    
class Student(User):
    role = "Student"
    
class TA(User):
    role = "TA"
    
    def can_moderate(self) -> bool:
        return True
    
class Professor(User):
    role = "Professor"
    
    def can_create_community(self) -> bool:
        return True
    
    def can_moderate(self) -> bool:
            return True