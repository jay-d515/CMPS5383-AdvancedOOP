"""
security.py
Password hashing helpers built on hashlib (standard library).

Passwords are never stored. Instead we store one self-describing string:

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

- salt: random per user, so two users with the same password get
  different hashes
- iterations: slows down brute-force guessing. Stored in the string so
  it can be raised later without breaking existing accounts.
  (200,000 is fine for a class project; production systems use more.)
"""

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000
SALT_BYTES = 16


def hash_password(password, salt=None, iterations=ITERATIONS):
    """Return a salted hash string for the given plaintext password."""
    if salt is None:
        salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    """Check a plaintext password against a stored hash string."""
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = bytes.fromhex(salt_hex)
        iterations = int(iterations)
    except (ValueError, AttributeError):
        return False  # malformed or missing hash

    candidate = hash_password(password, salt=salt, iterations=iterations)
    # compare_digest avoids leaking information through comparison timing
    return hmac.compare_digest(candidate, stored_hash)