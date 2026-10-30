import hashlib
import secrets


def generate_secure_qr_reference() -> str:
    """
    Generate 256 bits of cryptographically secure randomness encoded as URL-safe string.
    Does not encode PII, Aadhaar, database IDs or predictable metadata.
    """
    return secrets.token_urlsafe(32)


def hash_qr_reference(raw_reference: str) -> str:
    """
    Hash a raw QR reference using SHA-256 for secure storage and lookup.
    The raw reference is never stored in the database.
    """
    return hashlib.sha256(raw_reference.encode("utf-8")).hexdigest()
