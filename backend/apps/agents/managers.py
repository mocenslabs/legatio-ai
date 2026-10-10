"""
Custom managers for the agents app.
Provides SoftDeleteManager that filters out soft-deleted records by default.
Source: 03-DATA-MODEL.md Section 4.3
"""

from typing import Any

from django.db import models


class SoftDeleteQuerySet(models.QuerySet[Any]):
    """QuerySet that excludes soft-deleted records by default."""

    def alive(self) -> Any:
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> Any:
        """Return only soft-deleted records."""
        return self.filter(deleted_at__isnull=False)

    def delete(self, hard: bool = False) -> tuple[int, dict[str, int]]:
        """
        Soft-delete records by setting deleted_at.
        Args:
            hard: If True, perform actual DELETE. Default is soft delete.
        Returns:
            Tuple of (number of affected rows, dict of affected models).
        """
        if hard:
            return super().delete()
        from django.utils import timezone

        count = self.update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}


class SoftDeleteManager(models.Manager[Any]):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self) -> Any:
        """Return queryset excluding soft-deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self) -> Any:
        """Return all records including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted(self) -> Any:
        """Return only soft-deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).dead()
