"""Constitution serializer.

This module provides DRF serializers for the Constitution model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.constitutions.models import Constitution


class ConstitutionSerializer(serializers.ModelSerializer[Constitution]):
    """Serializer for Constitution model.

    Provides full CRUD capabilities for constitution management.
    """

    class Meta:
        model = Constitution
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        """Validate constitution name is unique.

        Args:
            value: The name value to validate.

        Returns:
            The validated name.

        Raises:
            serializers.ValidationError: If name already exists.
        """
        instance = self.instance
        queryset = Constitution.objects.filter(name=value)

        # Exclude current instance if updating
        if instance is not None and hasattr(instance, "pk"):
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A constitution with this name already exists.")

        return value
