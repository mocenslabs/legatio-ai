"""Unit tests for the TOTP service."""

import pyotp
import pytest
from django.contrib.auth import get_user_model

from apps.accounts.services.auth import register_user
from apps.accounts.services.totp import (
    confirm_2fa_setup,
    disable_2fa,
    enable_2fa,
    generate_totp_secret,
    verify_totp_code,
)
from core.exceptions import InvalidTOTPError, TwoFactorRequiredError

User = get_user_model()


@pytest.mark.django_db
class TestGenerateTOTPSecret:
    def test_generate_secret(self) -> None:
        secret = generate_totp_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0


@pytest.mark.django_db
class TestEnable2FA:
    def test_enable_2fa(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, uri = enable_2fa(user)
        assert isinstance(secret, str)
        assert isinstance(uri, str)
        assert "otpauth://" in uri
        assert user.totp_secret == secret
        assert user.two_factor_enabled is False  # Not yet confirmed

    def test_enable_2fa_stores_secret(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        user.refresh_from_db()
        assert user.totp_secret == secret


@pytest.mark.django_db
class TestConfirm2FASetup:
    def test_confirm_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        totp = pyotp.TOTP(secret)
        code = totp.now()
        confirm_2fa_setup(user, code)
        user.refresh_from_db()
        assert user.two_factor_enabled is True

    def test_confirm_invalid_code_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        enable_2fa(user)
        with pytest.raises(InvalidTOTPError):
            confirm_2fa_setup(user, "000000")

    def test_confirm_without_secret_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        with pytest.raises(InvalidTOTPError, match="No TOTP secret"):
            confirm_2fa_setup(user, "123456")


@pytest.mark.django_db
class TestVerifyTOTPCode:
    def test_verify_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        user.refresh_from_db()
        code = pyotp.TOTP(user.totp_secret).now()
        assert verify_totp_code(user, code) is True

    def test_verify_invalid_code(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        user.refresh_from_db()
        assert verify_totp_code(user, "000000") is False

    def test_verify_without_2fa_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        with pytest.raises(TwoFactorRequiredError):
            verify_totp_code(user, "123456")


@pytest.mark.django_db
class TestDisable2FA:
    def test_disable_success(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        user.refresh_from_db()
        code = pyotp.TOTP(user.totp_secret).now()
        disable_2fa(user, code)
        user.refresh_from_db()
        assert user.two_factor_enabled is False
        assert user.totp_secret is None

    def test_disable_invalid_code_raises(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        secret, _ = enable_2fa(user)
        confirm_2fa_setup(user, pyotp.TOTP(secret).now())
        user.refresh_from_db()
        with pytest.raises(InvalidTOTPError):
            disable_2fa(user, "000000")

    def test_disable_without_2fa_is_noop(self) -> None:
        user = register_user(email="test@example.com", password="testpass123")
        disable_2fa(user, "123456")  # Should not raise
        user.refresh_from_db()
        assert user.two_factor_enabled is False
