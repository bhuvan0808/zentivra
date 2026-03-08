"""Security — password hashing with bcrypt and auth token generation.

Provides password hashing (bcrypt) and verification for user authentication,
plus UUID-based auth token generation for session management.
"""

import uuid

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain: Plaintext password.

    Returns:
        Bcrypt hash string (includes salt).
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain: Plaintext password.
        hashed: Bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def generate_auth_token() -> str:
    """Generate a random UUID v4 string for use as an auth/session token."""
    return str(uuid.uuid4())
