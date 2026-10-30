"""
Security utilities and cryptography helpers.
QueueLess 2.3 uses Firebase Authentication for citizens and Admin SDK verification.
"""
import secrets


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)
