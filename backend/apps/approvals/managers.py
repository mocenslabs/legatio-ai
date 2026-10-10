"""
Custom managers for the approvals app.
"""

from __future__ import annotations

from typing import Any

from django.db import models


class AppendOnlyQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """QuerySet that prevents updates and deletes (append-only)."""

    def update(self, **kwargs: Any) -> int:
        raise RuntimeError("ApprovalDecision records are append-only. UPDATE not allowed.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise RuntimeError("ApprovalDecision records are append-only. DELETE not allowed.")


class AppendOnlyManager(models.Manager):  # type: ignore[type-arg]
    """Manager that enforces append-only behavior."""

    def get_queryset(self) -> AppendOnlyQuerySet:
        return AppendOnlyQuerySet(self.model, using=self._db)
