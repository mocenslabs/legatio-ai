"""Agent serializers.

This module provides DRF serializers for the Agent model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.agents.models import Agent
from apps.agents.serializers.automation_rule import AutomationRuleSerializer


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model (standard representation)."""

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "description",
            "agent_type",
            "config",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]


class AgentDetailSerializer(serializers.ModelSerializer):
    """Serializer for Agent model with nested rules.

    Extends the standard representation with automation rules and
    computed status flags for detailed views.
    """

    rules = AutomationRuleSerializer(many=True, read_only=True)
    can_execute = serializers.BooleanField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "description",
            "agent_type",
            "config",
            "is_active",
            "created_by",
            "rules",
            "can_execute",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_by",
            "rules",
            "can_execute",
            "created_at",
            "updated_at",
        ]


class AgentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating agents.

    Validates input for agent creation. The agent is created via the
    service layer to ensure audit logging.
    """

    class Meta:
        model = Agent
        fields = [
            "name",
            "description",
            "agent_type",
            "config",
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
