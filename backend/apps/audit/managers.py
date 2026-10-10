"""
Custom managers for the audit app.
Provides ImmutableManager that prevents modifications to AuditEvent records.
Source: 03-DATA-MODEL.md Section 13.1
"""

from typing import Any

from django.db import models


class ImmutableManager(models.Manager[Any]):
    """
    Manager that prevents UPDATE and DELETE operations on AuditEvent.
    This is a defense-in-depth measure. The primary protection is the
    PostgreSQL trigger, but this manager provides an additional layer
    at the application level.
    """

    def get_queryset(self) -> Any:
        """Return the default queryset."""
        return super().get_queryset()

    def update(self, **kwargs: Any) -> int:
        """Prevent bulk updates."""
        raise RuntimeError("AuditEvent records are immutable. UPDATE is not allowed.")

    def delete(self) -> tuple[int, dict[str, int]]:
        """Prevent bulk deletes."""
        raise RuntimeError("AuditEvent records are immutable. DELETE is not allowed.")


class ImmutableQuerySet(models.QuerySet[Any]):
    """QuerySet that prevents modifications."""

    def update(self, **kwargs: Any) -> int:
        """Prevent bulk updates."""
        raise RuntimeError("AuditEvent records are immutable. UPDATE is not allowed.")

    def delete(self) -> tuple[int, dict[str, int]]:
        """Prevent bulk deletes."""
        raise RuntimeError("AuditEvent records are immutable. DELETE is not allowed.")
