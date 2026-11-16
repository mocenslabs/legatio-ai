"""Managers for organizations (soft-delete aware)."""

from typing import Any

from django.db import models


class SoftDeleteQuerySet(models.QuerySet[Any]):
    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(deleted_at__isnull=True)

    def deleted(self) -> "SoftDeleteQuerySet":
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager[Any]):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()
