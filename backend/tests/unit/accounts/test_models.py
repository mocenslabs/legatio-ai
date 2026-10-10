"""
Unit tests for User and UserProfile models.

Source: 03-DATA-MODEL.md Section 6
"""

import pytest
from django.db import IntegrityError

from apps.accounts.models import User, UserProfile


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user_with_email(self) -> None:
        """User can be created with email and password."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_verified is False
        assert user.two_factor_enabled is False
        assert user.preferred_language == "en"
        assert user.preferred_timezone == "UTC"

    def test_create_user_without_email_raises(self) -> None:
        """Creating a user without email raises ValueError."""
        with pytest.raises(ValueError, match="Email field must be set"):
            User.objects.create_user(email="", password="testpass123")

    def test_email_is_normalized(self) -> None:
        """Email domain is normalized to lowercase."""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM",
            password="testpass123",
        )
        assert user.email == "Test@example.com"

    def test_email_is_unique(self) -> None:
        """Email must be unique across users."""
        User.objects.create_user(email="test@example.com", password="pass1")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="test@example.com", password="pass2")

    def test_create_superuser(self) -> None:
        """Superuser has is_staff and is_superuser set to True."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_verified is True

    def test_create_superuser_requires_staff(self) -> None:
        """Superuser must have is_staff=True."""
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_staff=False,
            )

    def test_create_superuser_requires_superuser(self) -> None:
        """Superuser must have is_superuser=True."""
        with pytest.raises(ValueError, match="is_superuser=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_superuser=False,
            )

    def test_user_id_is_uuid(self) -> None:
        """User ID is a UUID."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        import uuid as uuid_module

        assert isinstance(user.id, uuid_module.UUID)

    def test_get_full_name(self) -> None:
        """get_full_name returns first + last name."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
            last_name="Doe",
        )
        assert user.get_full_name() == "John Doe"

    def test_get_full_name_fallback_to_email(self) -> None:
        """get_full_name falls back to email if no name set."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert user.get_full_name() == "test@example.com"

    def test_get_short_name(self) -> None:
        """get_short_name returns first name or email prefix."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
        )
        assert user.get_short_name() == "John"

    def test_get_short_name_fallback(self) -> None:
        """get_short_name falls back to email prefix."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert user.get_short_name() == "test"

    def test_str_representation(self) -> None:
        """String representation of User is the email."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert str(user) == "test@example.com"

    def test_username_field_is_email(self) -> None:
        """USERNAME_FIELD is email."""
        assert User.USERNAME_FIELD == "email"

    def test_user_without_password(self) -> None:
        """User can be created without password (unusable password)."""
        user = User.objects.create_user(email="test@example.com")
        assert user.has_usable_password() is False

    def test_user_with_2fa_enabled(self) -> None:
        """User can have 2FA enabled."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            two_factor_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        assert user.two_factor_enabled is True
        assert user.totp_secret == "JBSWY3DPEHPK3PXP"

    def test_user_preferences_defaults(self) -> None:
        """User preferences have correct defaults."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert user.preferred_language == "en"
        assert user.preferred_timezone == "UTC"

    def test_user_custom_preferences(self) -> None:
        """User can have custom preferences."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            preferred_language="es",
            preferred_timezone="Europe/Madrid",
        )
        assert user.preferred_language == "es"
        assert user.preferred_timezone == "Europe/Madrid"

    def test_date_joined_auto_set(self) -> None:
        """date_joined is automatically set on creation."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert user.date_joined is not None

    def test_user_is_not_staff_by_default(self) -> None:
        """Regular user is not staff by default."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        assert user.is_staff is False
        assert user.is_superuser is False


@pytest.mark.django_db
class TestUserProfileModel:
    """Tests for the UserProfile model."""

    def test_create_profile_for_user(self) -> None:
        """UserProfile can be created for a user."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(
            user=user,
            display_name="John Doe",
        )
        assert profile.user == user
        assert profile.display_name == "John Doe"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_profile_str_representation(self) -> None:
        """String representation includes user email."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(user=user)
        assert str(profile) == "Profile of test@example.com"

    def test_profile_user_one_to_one(self) -> None:
        """User can only have one profile."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        UserProfile.objects.create(user=user)
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user)

    def test_profile_cascade_delete(self) -> None:
        """Deleting user deletes profile."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(user=user)
        profile_id = profile.id
        user.delete()
        assert not UserProfile.objects.filter(id=profile_id).exists()

    def test_profile_default_notification_preferences(self) -> None:
        """Profile gets default notification preferences on save."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(user=user)
        prefs = profile.notification_preferences
        assert prefs["version"] == 1
        assert prefs["websocket"] is True
        assert prefs["email"]["approval_required"] is True
        assert prefs["email"]["agreement_signed"] is True
        assert prefs["email"]["daily_digest"] is False

    def test_profile_custom_notification_preferences(self) -> None:
        """Profile can have custom notification preferences."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        custom_prefs = {
            "version": 1,
            "websocket": False,
            "email": {
                "approval_required": False,
                "agreement_signed": True,
                "daily_digest": True,
            },
        }
        profile = UserProfile.objects.create(
            user=user,
            notification_preferences=custom_prefs,
        )
        assert profile.notification_preferences == custom_prefs

    def test_profile_id_is_uuid(self) -> None:
        """Profile ID is a UUID."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(user=user)
        import uuid as uuid_module

        assert isinstance(profile.id, uuid_module.UUID)

    def test_profile_avatar_url(self) -> None:
        """Profile can have an avatar URL."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        profile = UserProfile.objects.create(
            user=user,
            avatar_url="https://example.com/avatar.jpg",
        )
        assert profile.avatar_url == "https://example.com/avatar.jpg"

    def test_user_get_display_name_with_profile(self) -> None:
        """User.get_display_name prefers profile display_name."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
        )
        UserProfile.objects.create(user=user, display_name="Johnny")
        # Refresh to load profile
        user = User.objects.get(id=user.id)
        assert user.get_display_name() == "Johnny"

    def test_user_get_display_name_without_profile(self) -> None:
        """User.get_display_name falls back to full name without profile."""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass",
            first_name="John",
            last_name="Doe",
        )
        assert user.get_display_name() == "John Doe"
