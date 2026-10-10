"""
Models for the accounts app.
Defines the custom User model and UserProfile for Legatio AI.
Source: 03-DATA-MODEL.md Section 6
"""

import uuid
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for Legatio AI.
    Uses email as the unique identifier instead of username.
    Supports 2FA via TOTP and user preferences.
    Source: 03-DATA-MODEL.md Section 6.1
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="email address",
    )
    first_name = models.CharField(max_length=100, blank=True, default="")
    last_name = models.CharField(max_length=100, blank=True, default="")

    # Permissions and status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user has verified their email address.",
    )

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Designates whether the user has enabled 2FA via TOTP.",
    )
    # NOTE: totp_secret will be encrypted in DEL-037 using django-cryptography.
    # For now, stored as plain CharField. Migration to encrypted field is
    # handled in DEL-037 (encryption-at-rest).
    # noqa: DJ001 — null=True is intentional here to allow distinguishing
    # "not configured" from "empty string" until encryption is implemented.
    totp_secret = models.CharField(  # noqa: DJ001
        max_length=32,
        null=True,
        blank=True,
        help_text="Encrypted TOTP secret for 2FA. Encrypted at rest (see DEL-037).",
    )

    # Preferences
    preferred_language = models.CharField(max_length=10, default="en")
    preferred_timezone = models.CharField(max_length=50, default="UTC")

    # Timestamps
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    # Django auth configuration — declared as ClassVar to properly override
    # the class variables from AbstractBaseUser (mypy strict compatibility).
    USERNAME_FIELD: ClassVar[str] = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        db_table = "legatio_accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["-date_joined"], name="idx_user_date_joined"),
        ]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.first_name or self.email.split("@")[0]

    def get_display_name(self) -> str:
        """Return the display name, preferring UserProfile.display_name."""
        try:
            if hasattr(self, "profile") and self.profile.display_name:
                return self.profile.display_name
        except UserProfile.DoesNotExist:
            pass
        return self.get_full_name()


class UserProfile(models.Model):
    """
    Extended profile information for a User.
    Separated from User to keep the authentication model lean
    and allow profile updates without touching auth fields.
    Source: 03-DATA-MODEL.md Section 6.2
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    # noqa: DJ001 — null=True is intentional to allow distinguishing
    # "not set" from "empty string" in the public display name.
    display_name = models.CharField(  # noqa: DJ001
        max_length=100,
        null=True,
        blank=True,
        help_text="Public display name for the user.",
    )
    # noqa: DJ001 — null=True is intentional for URL fields where "not set"
    # has different semantics than "empty URL".
    avatar_url = models.URLField(  # noqa: DJ001
        null=True,
        blank=True,
        help_text="URL to the user's avatar image.",
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "User notification preferences. Schema: "
            '{"version": 1, "websocket": true, "email": {...}}'
        ),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legatio_accounts_userprofile"
        verbose_name = "user profile"
        verbose_name_plural = "user profiles"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Profile of {self.user.email}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to set default notification_preferences if empty."""
        if not self.notification_preferences:
            self.notification_preferences = self.get_default_notification_preferences()
        super().save(*args, **kwargs)

    def get_default_notification_preferences(self) -> dict[str, Any]:
        """Return the default notification preferences schema."""
        return {
            "version": 1,
            "websocket": True,
            "email": {
                "approval_required": True,
                "agreement_signed": True,
                "daily_digest": False,
            },
        }
