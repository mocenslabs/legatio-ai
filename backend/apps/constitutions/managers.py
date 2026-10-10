"""
Custom managers for the constitutions app.
Provides managers with soft-delete support and immutability enforcement.
Source: 03-DATA-MODEL.md Section 8
"""

from typing import Any

from django.db import models


class ConstitutionSoftDeleteQuerySet(models.QuerySet[Any]):
    """QuerySet for Constitution with soft-delete support."""

    def alive(self) -> Any:
        """Return only non-deleted constitutions."""
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> Any:
        """Return only soft-deleted constitutions."""
        return self.filter(deleted_at__isnull=False)

    def delete(self, hard: bool = False) -> tuple[int, dict[str, int]]:
        """
        Soft-delete constitutions.
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


class ConstitutionSoftDeleteManager(models.Manager[Any]):
    """Manager that filters out soft-deleted constitutions by default."""

    def get_queryset(self) -> Any:
        """Return queryset excluding soft-deleted constitutions."""
        return ConstitutionSoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self) -> Any:
        """Return all constitutions including soft-deleted ones."""
        return ConstitutionSoftDeleteQuerySet(self.model, using=self._db)

    def dead(self) -> Any:
        """Return only soft-deleted constitutions."""
        return ConstitutionSoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=False
        )


class ImmutableVersionQuerySet(models.QuerySet[Any]):
    """QuerySet that prevents modifications to activated/archived versions."""

    def update(self, **kwargs: Any) -> int:
        """Prevent bulk updates."""
        for obj in self:
            if obj.status in ["ACTIVE", "ARCHIVED"]:
                raise RuntimeError(
                    f"ConstitutionVersion {obj.id} is immutable " f"(status={obj.status})."
                )
        return super().update(**kwargs)


class ImmutableVersionManager(models.Manager[Any]):
    """Manager that enforces immutability for ConstitutionVersion."""

    def get_queryset(self) -> Any:
        """Return immutable queryset."""
        return ImmutableVersionQuerySet(self.model, using=self._db)
