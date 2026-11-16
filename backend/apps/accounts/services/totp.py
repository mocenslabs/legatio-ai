"""
TOTP (Time-based One-Time Password) service for 2FA.

Handles 2FA setup, verification, and management.
TOTP secrets are encrypted at rest using Fernet (see core.crypto).

Source: 02-ARCHITECTURE.md Section 11.1
"""

from typing import Any

import pyotp
from django.conf import settings

from core.crypto import decrypt_value, encrypt_value
from core.exceptions import InvalidTOTPError, TwoFactorRequiredError


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret.

    Returns:
        Base32-encoded TOTP secret (plaintext).
    """
    return pyotp.random_base32()


def get_totp_uri(user: Any, secret: str) -> str:
    """
    Generate a TOTP URI for QR code generation.

    Args:
        user: The user instance.
        secret: The plaintext TOTP secret.

    Returns:
        TOTP URI in otpauth:// format.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user.email,
        issuer_name=settings.TOTP_ISSUER,
    )


def _get_plaintext_secret(user: Any) -> str | None:
    """
    Return the plaintext TOTP secret for a user, or None if not set.

    Decrypts the value stored in the database.
    """
    if not user.totp_secret:
        return None
    return decrypt_value(user.totp_secret)


def verify_totp_code(user: Any, code: str) -> bool:
    """
    Verify a TOTP code against the user's secret.

    Args:
        user: The user instance.
        code: The TOTP code to verify.

    Returns:
        True if the code is valid, False otherwise.

    Raises:
        TwoFactorRequiredError: If user doesn't have 2FA enabled.
    """
    if not user.two_factor_enabled or not user.totp_secret:
        raise TwoFactorRequiredError("User does not have 2FA enabled.")

    plaintext = _get_plaintext_secret(user)
    if not plaintext:
        raise TwoFactorRequiredError("User does not have 2FA enabled.")

    totp = pyotp.TOTP(plaintext)
    return totp.verify(code, valid_window=1)  # Allow 1 interval before/after


def enable_2fa(user: Any) -> tuple[str, str]:
    """
    Enable 2FA for a user.

    Generates a new TOTP secret and returns it (plaintext) along with the
    provisioning URI. The secret is stored encrypted in the database.
    The user must verify the first code to complete 2FA setup.

    Args:
        user: The user instance.

    Returns:
        Tuple of (plaintext_secret, uri).
    """
    secret = generate_totp_secret()
    uri = get_totp_uri(user, secret)

    # Store the secret encrypted (not yet activated)
    user.totp_secret = encrypt_value(secret)
    user.save(update_fields=["totp_secret"])

    return secret, uri


def confirm_2fa_setup(user: Any, code: str) -> None:
    """
    Confirm 2FA setup by verifying the first TOTP code.

    Args:
        user: The user instance.
        code: The TOTP code to verify.

    Raises:
        InvalidTOTPError: If the code is invalid.
    """
    plaintext = _get_plaintext_secret(user)
    if not plaintext:
        raise InvalidTOTPError("No TOTP secret found. Start 2FA setup first.")

    totp = pyotp.TOTP(plaintext)
    if not totp.verify(code, valid_window=1):
        raise InvalidTOTPError("Invalid TOTP code.")

    user.two_factor_enabled = True
    user.save(update_fields=["two_factor_enabled"])


def disable_2fa(user: Any, code: str) -> None:
    """
    Disable 2FA for a user.

    Requires a valid TOTP code to prevent unauthorized disabling.

    Args:
        user: The user instance.
        code: The TOTP code to verify.

    Raises:
        InvalidTOTPError: If the code is invalid.
    """
    if not user.two_factor_enabled:
        return  # Nothing to disable

    if not verify_totp_code(user, code):
        raise InvalidTOTPError("Invalid TOTP code.")

    user.two_factor_enabled = False
    user.totp_secret = None
    user.save(update_fields=["two_factor_enabled", "totp_secret"])
