"""PolicyRule serializer.

This module provides DRF serializers for the PolicyRule model.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.policies.models import PolicyRule


class PolicyRuleSerializer(serializers.ModelSerializer[PolicyRule]):
    """Serializer for PolicyRule model.

    Provides full CRUD capabilities for policy rule management with
    validation for JSON conditions and action types.
    """

    class Meta:
        model = PolicyRule
        fields = [
            "id",
            "name",
            "description",
            "condition",
            "action_type",
            "risk_level",
            "requires_approval_from",
            "priority",
            "is_active",
            "constitution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        """Validate policy rule name is unique.

        Args:
            value: The name value to validate.

        Returns:
            The validated name.

        Raises:
            serializers.ValidationError: If name already exists.
        """
        instance = self.instance
        queryset = PolicyRule.objects.filter(name=value)

        # Exclude current instance if updating
        if instance is not None and hasattr(instance, "pk"):
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A policy rule with this name already exists.")

        return value

    def validate_condition(self, value: dict[str, Any]) -> dict[str, Any]:
        """Validate condition structure.

        Args:
            value: The condition dictionary to validate.

        Returns:
            The validated condition.

        Raises:
            serializers.ValidationError: If condition structure is invalid.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Condition must be a JSON object.")

        required_fields = ["field", "operator"]
        for field_name in required_fields:
            if field_name not in value:
                raise serializers.ValidationError(f"Condition must contain '{field_name}' field.")

        valid_operators = [
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "in",
            "not_in",
            "contains",
            "exists",
        ]
        operator = value.get("operator")
        if operator not in valid_operators:
            raise serializers.ValidationError(
                f"Invalid operator '{operator}'. Must be one of: {', '.join(valid_operators)}"
            )

        # 'exists' operator doesn't require 'value' field
        if operator != "exists" and "value" not in value:
            raise serializers.ValidationError(
                "Condition must contain 'value' field for this operator."
            )

        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate cross-field constraints.

        Args:
            data: The validated data dictionary.

        Returns:
            The validated data.

        Raises:
            serializers.ValidationError: If cross-field validation fails.
        """
        action_type = data.get("action_type")
        requires_approval_from = data.get("requires_approval_from", [])

        # REQUIRE_APPROVAL must have approvers defined
        if action_type == "REQUIRE_APPROVAL" and not requires_approval_from:
            raise serializers.ValidationError(
                {
                    "requires_approval_from": (
                        "This field is required when action_type is REQUIRE_APPROVAL."
                    )
                }
            )

        return data
