"""Constitution service layer.

This module provides business logic for constitution management.
"""

from __future__ import annotations

import uuid

from django.db import transaction
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.constitutions.models import Constitution


class ConstitutionServiceError(Exception):
    """Base exception for constitution service errors."""


class ConstitutionNotFoundError(ConstitutionServiceError):
    """Raised when a constitution is not found."""


class ConstitutionService:
    """Service layer for constitution operations."""

    @staticmethod
    def get_active_constitutions(user: User) -> QuerySet[Constitution]:
        """Get all active constitutions for a user."""
        return Constitution.objects.filter(user=user, is_active=True)

    @staticmethod
    def get_constitution_by_id(constitution_id: uuid.UUID, user: User) -> Constitution:
        """Get a constitution by its ID, ensuring it belongs to the user."""
        try:
            return Constitution.objects.get(id=constitution_id, user=user)
        except Constitution.DoesNotExist as e:
            raise ConstitutionNotFoundError(
                f"Constitution with id {constitution_id} not found for this user"
            ) from e

    @staticmethod
    @transaction.atomic
    def create_constitution(
        user: User,
        name: str,
        description: str = "",
        is_active: bool = True,
    ) -> Constitution:
        """Create a new constitution for a user."""
        if Constitution.objects.filter(user=user, name=name).exists():
            raise ConstitutionServiceError(
                f"A constitution with name '{name}' already exists for this user"
            )

        return Constitution.objects.create(
            user=user,
            name=name,
            description=description,
            is_active=is_active,
        )

    @staticmethod
    @transaction.atomic
    def deactivate_constitution(constitution_id: uuid.UUID, user: User) -> Constitution:
        """Deactivate a constitution."""
        constitution = ConstitutionService.get_constitution_by_id(constitution_id, user)
        constitution.is_active = False
        constitution.save(update_fields=["is_active", "updated_at"])
        return constitution
