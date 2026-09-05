"""AutomationRule serializers.

This module provides DRF serializers for the AutomationRule model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.agents.models import AutomationRule


class AutomationRuleSerializer(serializers.ModelSerializer):
    """Serializer for AutomationRule model (standard representation)."""

    can_fire = serializers.BooleanField(read_only=True)
    has_condition = serializers.BooleanField(read_only=True)

    class Meta:
        model = AutomationRule
        fields = [
            "id",
            "agent",
            "name",
            "trigger_type",
            "condition",
            "action_type",
            "action_config",
            "priority",
            "is_active",
            "created_by",
            "can_fire",
            "has_condition",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_by",
            "can_fire",
            "has_condition",
            "created_at",
            "updated_at",
        ]


class AutomationRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating automation rules.

    Validates input for rule creation. The rule is created via the
    service layer to ensure audit logging.
    """

    class Meta:
        model = AutomationRule
        fields = [
            "agent",
            "name",
            "trigger_type",
            "condition",
            "action_type",
            "action_config",
            "priority",
        ]

    def validate_name(self, value: str) -> str:
        """Validate name is not empty.

        Args:
            value: The name value to validate.

        Returns:
            The validated name.

        Raises:
            serializers.ValidationError: If name is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("name cannot be empty.")
        return value


class ExecuteRuleSerializer(serializers.Serializer):
    """Serializer for executing an automation rule manually."""

    # NOTE: DRF type stubs have a known incompatibility with JSONField
    # declared as class attributes on plain Serializer subclasses.
    context = serializers.JSONField(  # type: ignore[assignment]
        help_text="Event context data for condition evaluation and action execution.",
    )
