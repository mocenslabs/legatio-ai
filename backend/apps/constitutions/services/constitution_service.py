"""Constitution service layer.

This module provides business logic for constitution management,
separating concerns from views and models.
"""

from __future__ import annotations

import uuid

from django.db import transaction
from django.db.models import QuerySet

from apps.constitutions.models import Constitution


class ConstitutionServiceError(Exception):
    """Base exception for constitution service errors."""


class ConstitutionNotFoundError(ConstitutionServiceError):
    """Raised when a constitution is not found."""


class ConstitutionInactiveError(ConstitutionServiceError):
    """Raised when trying to use an inactive constitution."""


class ConstitutionService:
    """Service layer for constitution operations.

    Provides business logic for creating, retrieving, and managing
    constitutions with proper validation and error handling.
    """

    @staticmethod
    def get_active_constitutions() -> QuerySet[Constitution]:
        """Get all active constitutions.

        Returns:
            QuerySet of active Constitution objects.
        """
        return Constitution.objects.filter(is_active=True)

    @staticmethod
    def get_constitution_by_id(constitution_id: uuid.UUID) -> Constitution:
        """Get a constitution by its ID.

        Args:
            constitution_id: UUID of the constitution.

        Returns:
            The Constitution object.

        Raises:
            ConstitutionNotFoundError: If the constitution doesn't exist.
        """
        try:
            return Constitution.objects.get(id=constitution_id)
        except Constitution.DoesNotExist as e:
            raise ConstitutionNotFoundError(
                f"Constitution with id {constitution_id} not found"
            ) from e

    @staticmethod
    def get_active_constitution_by_id(constitution_id: uuid.UUID) -> Constitution:
        """Get an active constitution by its ID.

        Args:
            constitution_id: UUID of the constitution.

        Returns:
            The active Constitution object.

        Raises:
            ConstitutionNotFoundError: If the constitution doesn't exist.
            ConstitutionInactiveError: If the constitution is not active.
        """
        constitution = ConstitutionService.get_constitution_by_id(constitution_id)

        if not constitution.is_active:
            raise ConstitutionInactiveError(f"Constitution {constitution_id} is not active")

        return constitution

    @staticmethod
    @transaction.atomic
    def create_constitution(
        name: str,
        description: str = "",
        is_active: bool = True,
    ) -> Constitution:
        """Create a new constitution.

        Args:
            name: Name of the constitution.
            description: Optional description.
            is_active: Whether the constitution is active.

        Returns:
            The created Constitution object.

        Raises:
            ConstitutionServiceError: If a constitution with the same name exists.
        """
        if Constitution.objects.filter(name=name).exists():
            raise ConstitutionServiceError(f"A constitution with name '{name}' already exists")

        return Constitution.objects.create(
            name=name,
            description=description,
            is_active=is_active,
        )

    @staticmethod
    @transaction.atomic
    def deactivate_constitution(constitution_id: uuid.UUID) -> Constitution:
        """Deactivate a constitution.

        Args:
            constitution_id: UUID of the constitution to deactivate.

        Returns:
            The updated Constitution object.

        Raises:
            ConstitutionNotFoundError: If the constitution doesn't exist.
        """
        constitution = ConstitutionService.get_constitution_by_id(constitution_id)
        constitution.is_active = False
        constitution.save(update_fields=["is_active", "updated_at"])
        return constitution

    @staticmethod
    @transaction.atomic
    def activate_constitution(constitution_id: uuid.UUID) -> Constitution:
        """Activate a constitution.

        Args:
            constitution_id: UUID of the constitution to activate.

        Returns:
            The updated Constitution object.

        Raises:
            ConstitutionNotFoundError: If the constitution doesn't exist.
        """
        constitution = ConstitutionService.get_constitution_by_id(constitution_id)
        constitution.is_active = True
        constitution.save(update_fields=["is_active", "updated_at"])
        return constitution
