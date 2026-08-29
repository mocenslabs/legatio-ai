"""Policy evaluation serializers.

This module provides serializers for policy evaluation requests and responses.
"""

from __future__ import annotations

from rest_framework import serializers


class PolicyEvaluationRequestSerializer(serializers.Serializer):
    """Serializer for policy evaluation requests.

    Validates the structure of action evaluation requests.
    """

    action_type = serializers.CharField(
        max_length=100,
        help_text="The type of action being proposed (e.g., 'CREATE_PROPOSAL').",
    )
    target_resource = serializers.CharField(
        max_length=100,
        help_text="The resource or entity the action targets.",
    )
    payload = serializers.DictField(
        child=serializers.JSONField(),
        help_text="Arbitrary data associated with the action.",
    )
    actor_id = serializers.UUIDField(
        help_text="The UUID of the user or agent proposing the action.",
    )
    constitution_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional UUID of the constitution to scope rules.",
    )

    def validate_action_type(self, value: str) -> str:
        """Validate action_type is not empty.

        Args:
            value: The action_type value to validate.

        Returns:
            The validated action_type.

        Raises:
            serializers.ValidationError: If action_type is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("action_type cannot be empty.")
        return value

    def validate_target_resource(self, value: str) -> str:
        """Validate target_resource is not empty.

        Args:
            value: The target_resource value to validate.

        Returns:
            The validated target_resource.

        Raises:
            serializers.ValidationError: If target_resource is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("target_resource cannot be empty.")
        return value


class PolicyEvaluationResponseSerializer(serializers.Serializer):
    """Serializer for policy evaluation responses.

    Formats the PolicyDecision for API responses.
    """

    outcome = serializers.CharField(
        help_text="The decision outcome (ALLOW, DENY, REQUIRE_HUMAN_APPROVAL, ERROR).",
    )
    risk_level = serializers.CharField(
        help_text="The assessed risk level (LOW, MEDIUM, HIGH, CRITICAL).",
    )
    reason = serializers.CharField(
        help_text="Human-readable explanation for the decision.",
    )
    matched_rules = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of PolicyRule UUIDs that influenced the decision.",
    )
    requires_approval_from = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of roles or user UUIDs required for approval.",
    )
    timestamp = serializers.DateTimeField(
        help_text="The exact time the decision was made (UTC).",
    )
