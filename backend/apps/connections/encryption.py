import base64

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    """Build a Fernet instance from the FIELD_ENCRYPTION_KEY setting."""
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
    if not key:
        raise ValueError(
            "FIELD_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    # Fernet requires a 32-byte url-safe base64-encoded key
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string, return base64-encoded ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext, return plaintext string."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # If decryption fails, the value may be a legacy plaintext password
        return ciphertext
