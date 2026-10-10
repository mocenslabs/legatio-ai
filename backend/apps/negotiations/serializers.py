"""
DRF serializers for the negotiations app.

Handles validation and serialization for NegotiationRoom, NegotiationMessage,
and related proposal/decision entities.

Source: 05-ROADMAP.md Section 7.3
"""

from typing import Any

from rest_framework import serializers

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from apps.proposals.models import CounterProposal, PolicyDecision, Proposal


class PolicyDecisionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for PolicyDecision (read-only)."""

    class Meta:
        model = PolicyDecision
        fields = [
            "id",
            "proposal",
            "constitution_version",
            "outcome",
            "risk_level",
            "reason",
            "matched_rules",
            "evaluation_duration_ms",
            "engine_version",
            "created_at",
        ]
        read_only_fields = fields


class CounterProposalSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for CounterProposal (read-only)."""

    class Meta:
        model = CounterProposal
        fields = [
            "id",
            "proposal",
            "sender",
            "adjustments",
            "reasoning",
            "created_at",
        ]
        read_only_fields = fields


class ProposalSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for Proposal (read-only)."""

    decisions = PolicyDecisionSerializer(many=True, read_only=True)
    counter_proposals = CounterProposalSerializer(many=True, read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id",
            "room",
            "sender",
            "action_type",
            "amount",
            "currency",
            "data_fields_requested",
            "contract_length_months",
            "auto_renewal",
            "terms",
            "status",
            "round_number",
            "superseded_by",
            "decisions",
            "counter_proposals",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class NegotiationMessageSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for NegotiationMessage (read-only)."""

    class Meta:
        model = NegotiationMessage
        fields = [
            "id",
            "room",
            "sender_type",
            "sender_id",
            "message_type",
            "content",
            "round_number",
            "created_at",
        ]
        read_only_fields = fields


class NegotiationRoomSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for NegotiationRoom."""

    user_agent_name = serializers.CharField(source="user_agent.name", read_only=True)
    external_agent_name = serializers.CharField(source="external_agent.name", read_only=True)
    constitution_name = serializers.CharField(source="constitution.name", read_only=True)
    messages_count = serializers.SerializerMethodField()
    proposals_count = serializers.SerializerMethodField()

    class Meta:
        model = NegotiationRoom
        fields = [
            "id",
            "reference_code",
            "user_agent",
            "user_agent_name",
            "external_agent",
            "external_agent_name",
            "constitution",
            "constitution_name",
            "title",
            "user_instruction",
            "status",
            "max_rounds",
            "current_round",
            "ttl_hours",
            "started_at",
            "completed_at",
            "cancelled_at",
            "messages_count",
            "proposals_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference_code",
            "status",
            "current_round",
            "started_at",
            "completed_at",
            "cancelled_at",
            "messages_count",
            "proposals_count",
            "created_at",
            "updated_at",
        ]

    def get_messages_count(self, obj: NegotiationRoom) -> int:
        """Return the number of messages in the room."""
        return obj.messages.count()

    def get_proposals_count(self, obj: NegotiationRoom) -> int:
        """Return the number of proposals in the room."""
        return obj.proposals.count()


class NegotiationRoomCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Serializer for creating a NegotiationRoom."""

    user_agent_id = serializers.UUIDField()
    external_agent_id = serializers.UUIDField()
    constitution_id = serializers.UUIDField()
    title = serializers.CharField(max_length=200)
    user_instruction = serializers.CharField()
    max_rounds = serializers.IntegerField(default=10, min_value=1, max_value=100)
    ttl_hours = serializers.IntegerField(default=24, min_value=1, max_value=168)

    def validate_user_agent_id(self, value: str) -> str:
        """Validate that the user owns the user_agent."""
        request = self.context.get("request")
        try:
            agent = Agent.objects.get(id=value)
        except Agent.DoesNotExist:
            raise serializers.ValidationError("User agent not found.") from None

        if request and hasattr(request, "user") and agent.owner != request.user:
            raise serializers.ValidationError("You can only use your own agents.")
        return value

    def validate_external_agent_id(self, value: str) -> str:
        """Validate that the external_agent exists."""
        try:
            Agent.objects.get(id=value)
        except Agent.DoesNotExist:
            raise serializers.ValidationError("External agent not found.") from None
        return value

    def validate_constitution_id(self, value: str) -> str:
        """Validate that the constitution exists and is active."""
        try:
            constitution = Constitution.objects.get(id=value)
        except Constitution.DoesNotExist:
            raise serializers.ValidationError("Constitution not found.") from None

        if constitution.status != "ACTIVE":
            raise serializers.ValidationError("Constitution must be ACTIVE to start a negotiation.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that user_agent and external_agent are different."""
        if attrs["user_agent_id"] == attrs["external_agent_id"]:
            raise serializers.ValidationError("User agent and external agent must be different.")
        return attrs
