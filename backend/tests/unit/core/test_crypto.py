"""Unit tests for core.crypto helpers."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from core.crypto import (
    EncryptionError,
    _get_fernet,
    decrypt_value,
    encrypt_value,
    is_encrypted,
)

# Real Fernet key (url-safe base64 of 32 random bytes)
VALID_KEY = "8Pxuyu443UVl4gerNpnL2kduLqKdZ9wTFb-_g7Nv1iA="


@pytest.fixture(autouse=True)
def _clear_fernet_cache():
    """Ensure each test starts with a fresh Fernet instance (no cached key)."""
    _get_fernet.cache_clear()
    yield
    _get_fernet.cache_clear()


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_roundtrip() -> None:
    plaintext = "JBSWY3DPEHPK3PXP"
    token = encrypt_value(plaintext)
    assert token != plaintext
    assert is_encrypted(token)
    assert decrypt_value(token) == plaintext


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_different_plaintexts_produce_different_tokens() -> None:
    t1 = encrypt_value("secret-one")
    t2 = encrypt_value("secret-two")
    assert t1 != t2


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_same_plaintext_produces_different_tokens() -> None:
    # Fernet includes a timestamp + random IV → tokens differ
    t1 = encrypt_value("same-secret")
    t2 = encrypt_value("same-secret")
    assert t1 != t2
    assert decrypt_value(t1) == decrypt_value(t2) == "same-secret"


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_encrypt_none_raises() -> None:
    with pytest.raises(EncryptionError):
        encrypt_value(None)  # type: ignore[arg-type]


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_decrypt_empty_raises() -> None:
    with pytest.raises(EncryptionError):
        decrypt_value("")


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_decrypt_invalid_token_raises() -> None:
    with pytest.raises(EncryptionError):
        decrypt_value("not-a-valid-fernet-token")


@override_settings(ENCRYPTION_KEY=VALID_KEY)
def test_is_encrypted_heuristic() -> None:
    token = encrypt_value("hello")
    assert is_encrypted(token) is True
    assert is_encrypted("JBSWY3DPEHPK3PXP") is False
    assert is_encrypted(None) is False
    assert is_encrypted("") is False


@override_settings(ENCRYPTION_KEY="")
def test_missing_key_raises_on_encrypt() -> None:
    with pytest.raises(ImproperlyConfigured):
        encrypt_value("test")


@override_settings(ENCRYPTION_KEY="__ENCRYPTION_KEY__")
def test_placeholder_key_raises() -> None:
    with pytest.raises(ImproperlyConfigured):
        encrypt_value("test")
