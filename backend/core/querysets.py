"""
Reusable QuerySets for Legatio AI.
Provides base QuerySets with ownership filtering and soft-delete support.
Source: 02-ARCHITECTURE.md Section 11.2
"""

from typing import Any

from django.db import models


class OwnershipQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """
    QuerySet that filters by owner (user).
    Assumes the model has an `owner` field pointing to User.
    For models where the owner is nested (e.g., UserProfile.user),
    use the appropriate subclass.
    """

    def for_user(self: Any, user: Any) -> Any:
        """Filter queryset to only include objects owned by the user."""
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)


class UserProfileQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """QuerySet for UserProfile with user-based filtering."""

    def for_user(self: Any, user: Any) -> Any:
        """Filter queryset to only include profiles belonging to the user."""
        if user is None or not user.is_authenticated:
            return self.none()
        return self.filter(user=user)


class SoftDeleteQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """
    QuerySet that excludes soft-deleted records by default.
    Assumes the model has a `deleted_at` field.
    """

    def alive(self: Any) -> Any:
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def dead(self: Any) -> Any:
        """Return only soft-deleted records."""
        return self.filter(deleted_at__isnull=False)

    def delete(self: Any, hard: bool = False) -> Any:
        """
        Soft-delete records by setting deleted_at.
        Args:
            hard: If True, perform actual DELETE. Default is soft delete.
        Returns:
            Number of affected rows or tuple (count, dict) depending on mode.
        """
        if hard:
            return super().delete()
        from django.utils import timezone

        return self.update(deleted_at=timezone.now())


class OwnershipSoftDeleteQuerySet(OwnershipQuerySet):
    """
    Combined QuerySet for models with both ownership and soft-delete.
    Inherits soft-delete methods from SoftDeleteQuerySet via composition
    pattern to avoid mypy conflicts with multiple inheritance.
    """

    def alive(self) -> Any:
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> Any:
        """Return only soft-deleted records."""
        return self.filter(deleted_at__isnull=False)

    def soft_delete(self) -> Any:
        """Soft-delete records by setting deleted_at."""
        from django.utils import timezone

        return self.update(deleted_at=timezone.now())
