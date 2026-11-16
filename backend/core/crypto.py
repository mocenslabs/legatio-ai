"""
Cryptographic helpers for at-rest encryption.

Uses Fernet (symmetric authenticated encryption) from the ``cryptography``
package. The key is loaded from the ``ENCRYPTION_KEY`` environment variable
(url-safe base64-encoded 32-byte key).

Primary use today: encrypting TOTP secrets before they are stored in the
database. The same helpers can be reused for other sensitive fields later.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger("legatio.crypto")


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """
    Return a Fernet instance configured with ENCRYPTION_KEY.

    The key must be a url-safe base64-encoded 32-byte key (the format
    produced by ``Fernet.generate_key()``).
    """
    key = getattr(settings, "ENCRYPTION_KEY", None) or ""
    key = key.strip()
    if not key or key.startswith("__") or key == "change-me":
        raise ImproperlyConfigured(
            "ENCRYPTION_KEY is not configured. "
            'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except Exception as exc:
        raise ImproperlyConfigured(
            f"ENCRYPTION_KEY is invalid (must be url-safe base64-encoded 32-byte key): {exc}"
        ) from exc


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string and return a url-safe base64 token.

    Args:
        plaintext: The value to encrypt (e.g. a TOTP secret).

    Returns:
        Fernet token as a UTF-8 string (safe to store in a CharField).

    Raises:
        EncryptionError: If encryption fails.
        ImproperlyConfigured: If ENCRYPTION_KEY is missing/invalid.
    """
    if plaintext is None:
        raise EncryptionError("Cannot encrypt None")
    # Configuration errors must propagate (not wrapped).
    fernet = _get_fernet()
    try:
        token = fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as exc:
        logger.exception("Encryption failed")
        raise EncryptionError(f"Encryption failed: {exc}") from exc


def decrypt_value(token: str) -> str:
    """
    Decrypt a Fernet token and return the original plaintext.

    Args:
        token: The encrypted value previously returned by ``encrypt_value``.

    Returns:
        Original plaintext string.

    Raises:
        EncryptionError: If the token is invalid, tampered, or key is wrong.
        ImproperlyConfigured: If ENCRYPTION_KEY is missing/invalid.
    """
    if not token:
        raise EncryptionError("Cannot decrypt empty token")
    fernet = _get_fernet()
    try:
        plaintext = fernet.decrypt(token.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken as exc:
        logger.warning("Decryption failed: invalid token or wrong key")
        raise EncryptionError("Decryption failed: invalid token or wrong key") from exc
    except Exception as exc:
        logger.exception("Decryption failed")
        raise EncryptionError(f"Decryption failed: {exc}") from exc


def is_encrypted(value: str | None) -> bool:
    """
    Heuristic check whether a value looks like a Fernet token.

    Fernet tokens always start with the version byte ``gAAAAA`` when
    base64-encoded. Useful for transitional code paths.
    """
    if not value:
        return False
    return value.startswith("gAAAAA")
