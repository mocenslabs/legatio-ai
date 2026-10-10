"""
Custom managers for the proposals app.
"""

from typing import Any

from django.db import models


class AppendOnlyQuerySet(models.QuerySet[Any]):
    """QuerySet that prevents updates and deletes (append-only)."""

    def update(self, **kwargs: Any) -> int:
        raise RuntimeError("This model is append-only. UPDATE not allowed.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise RuntimeError("This model is append-only. DELETE not allowed.")


class AppendOnlyManager(models.Manager[Any]):
    """Manager that enforces append-only behavior."""

    def get_queryset(self) -> AppendOnlyQuerySet:
        return AppendOnlyQuerySet(self.model, using=self._db)
