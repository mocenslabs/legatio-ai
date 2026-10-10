"""
Custom managers for the negotiations app.
"""

from typing import Any

from django.db import models


class NegotiationSoftDeleteQuerySet(models.QuerySet[Any]):
    """QuerySet with soft-delete support for NegotiationRoom."""

    def alive(self) -> "NegotiationSoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> "NegotiationSoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=False)

    def delete(self, hard: bool = False) -> tuple[int, dict[str, int]]:
        if hard:
            return super().delete()
        from django.utils import timezone

        count = self.update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}


class NegotiationSoftDeleteManager(models.Manager[Any]):
    """Manager that excludes soft-deleted negotiations."""

    def get_queryset(self) -> NegotiationSoftDeleteQuerySet:
        return NegotiationSoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self) -> NegotiationSoftDeleteQuerySet:
        return NegotiationSoftDeleteQuerySet(self.model, using=self._db)


class AppendOnlyQuerySet(models.QuerySet[Any]):
    """QuerySet that prevents updates and deletes (append-only)."""

    def update(self, **kwargs: Any) -> int:
        raise RuntimeError("NegotiationMessage records are append-only. UPDATE not allowed.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise RuntimeError("NegotiationMessage records are append-only. DELETE not allowed.")


class AppendOnlyManager(models.Manager[Any]):
    """Manager that enforces append-only behavior."""

    def get_queryset(self) -> AppendOnlyQuerySet:
        return AppendOnlyQuerySet(self.model, using=self._db)
