"""
Unit tests for UserManager.

Source: 03-DATA-MODEL.md Section 6.1
"""

import pytest

from apps.accounts.models import User


@pytest.mark.django_db
class TestUserManager:
    """Tests for the UserManager."""

    def test_create_user_sets_defaults(self) -> None:
        """create_user sets proper defaults."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
        )
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_verified is False
        assert user.two_factor_enabled is False
        assert user.preferred_language == "en"
        assert user.preferred_timezone == "UTC"

    def test_create_user_hash_password(self) -> None:
        """create_user hashes the password."""
        user = User.objects.create_user(
            email="test@example.com",
            password="plainpassword",
        )
        # Password should be hashed, not stored in plain text
        assert user.password != "plainpassword"
        assert user.check_password("plainpassword")

    def test_create_user_without_password(self) -> None:
        """create_user without password sets unusable password."""
        user = User.objects.create_user(email="test@example.com")
        assert user.has_usable_password() is False

    def test_create_user_extra_fields(self) -> None:
        """create_user accepts extra fields."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
            last_name="Doe",
            preferred_language="es",
        )
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.preferred_language == "es"

    def test_create_superuser_sets_flags(self) -> None:
        """create_superuser sets is_staff, is_superuser, is_verified."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_verified is True

    def test_create_superuser_override_is_verified(self) -> None:
        """create_superuser allows overriding is_verified."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            is_verified=False,
        )
        # is_verified was explicitly set to False, but setdefault doesn't override
        # Actually, setdefault won't override, so it stays False
        # This tests the behavior is as expected
        assert user.is_verified is False

    def test_create_user_empty_email_raises(self) -> None:
        """create_user with empty email raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="pass")

    def test_create_user_none_email_raises(self) -> None:
        """create_user with None email raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_user(email=None, password="pass")  # type: ignore[arg-type]
