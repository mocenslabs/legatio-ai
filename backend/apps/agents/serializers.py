"""
DRF serializers for the agents app.

Source: 03-DATA-MODEL.md Section 7.1 / MVP API surface
"""

from typing import Any

from rest_framework import serializers

from apps.agents.models import Agent
from core.enums import AgentStatus, AgentType


class AgentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Read serializer for Agent."""

    class Meta:
        model = Agent
        fields = [
            "id",
            "owner",
            "agent_type",
            "name",
            "description",
            "status",
            "external_endpoint_url",
            "capabilities",
            "protocol_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "created_at",
            "updated_at",
        ]


class AgentCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Create a USER_AGENT owned by the authenticated user.

    External/simulated agents are seeded or created by ops — not via this endpoint.
    """

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    capabilities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
    )
    protocol_version = serializers.CharField(max_length=20, required=False, default="1.0")

    def create(self, validated_data: dict[str, Any]) -> Agent:
        request = self.context["request"]
        agent: Agent = Agent.objects.create(
            owner=request.user,
            agent_type=AgentType.USER_AGENT,
            status=AgentStatus.ACTIVE,
            name=validated_data["name"],
            description=validated_data.get("description") or "",
            capabilities=validated_data.get("capabilities") or [],
            protocol_version=validated_data.get("protocol_version") or "1.0",
        )
        return agent


class AgentUpdateSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Partial update for owned USER_AGENT only (enforced in the view)."""

    class Meta:
        model = Agent
        fields = [
            "name",
            "description",
            "status",
            "capabilities",
            "protocol_version",
        ]
