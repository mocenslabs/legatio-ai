"""
UserProfile model for Legatio AI.

Extended profile information for users.
"""

import uuid

from django.db import models

from .user import User


class UserProfile(models.Model):
    """
    Extended profile information for a User.

    One-to-one relationship with User model.
    Contains display preferences and notification settings.
    """

    id: models.UUIDField = models.UUIDField(  # type: ignore[assignment]
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user: models.OneToOneField = models.OneToOneField(  # type: ignore[assignment]
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="The user this profile belongs to.",
    )
    display_name: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=100,
        null=True,
        blank=True,
        help_text="Display name shown in the UI.",
    )
    avatar_url: models.URLField = models.URLField(  # type: ignore[assignment]
        null=True,
        blank=True,
        help_text="URL to user avatar image.",
    )
    notification_preferences: models.JSONField = models.JSONField(  # type: ignore[assignment]
        default=dict,
        blank=True,
        help_text="Notification channel preferences.",
    )
    created_at: models.DateTimeField = models.DateTimeField(  # type: ignore[assignment]
        auto_now_add=True,
        db_index=True,
    )
    updated_at: models.DateTimeField = models.DateTimeField(  # type: ignore[assignment]
        auto_now=True,
    )

    class Meta:
        db_table = "legatio_accounts_userprofile"
        verbose_name = "user profile"
        verbose_name_plural = "user profiles"

    def __str__(self) -> str:
        """Return string representation of the profile."""
        return f"Profile for {self.user.email}"
