"""
DRF serializers for the approvals app.

Handles validation and serialization for ApprovalRequest and ApprovalDecision.

Source: 05-ROADMAP.md Section 8.5
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.approvals.models import ApprovalDecision, ApprovalRequest
from core.enums import ApprovalStatus


class ApprovalDecisionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Serializer for ApprovalDecision (read-only)."""

    decided_by_email = serializers.CharField(
        source="decided_by.email",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ApprovalDecision
        fields = [
            "id",
            "request",
            "decided_by",
            "decided_by_email",
            "decision",
            "modifications",
            "comment",
            "created_at",
        ]
        read_only_fields = fields


class ApprovalRequestSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Full serializer for ApprovalRequest (retrieve)."""

    proposal_details = serializers.SerializerMethodField()
    policy_decision_details = serializers.SerializerMethodField()
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "proposal",
            "proposal_details",
            "room",
            "requested_by",
            "policy_decision",
            "policy_decision_details",
            "status",
            "summary",
            "expires_at",
            "is_expired",
            "decisions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_proposal_details(self, obj: ApprovalRequest) -> dict[str, Any]:
        """Return nested proposal summary."""
        proposal = obj.proposal
        return {
            "id": str(proposal.id),
            "action_type": proposal.action_type,
            "amount": str(proposal.amount) if proposal.amount is not None else None,
            "currency": proposal.currency,
            "data_fields_requested": proposal.data_fields_requested,
            "terms": proposal.terms,
            "round_number": proposal.round_number,
            "status": proposal.status,
        }

    def get_policy_decision_details(self, obj: ApprovalRequest) -> dict[str, Any]:
        """Return nested policy decision summary."""
        decision = obj.policy_decision
        return {
            "id": str(decision.id),
            "outcome": decision.outcome,
            "risk_level": decision.risk_level,
            "reason": decision.reason,
            "matched_rules": decision.matched_rules,
        }


class ApprovalRequestListSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Lightweight serializer for listing approval requests."""

    proposal_amount = serializers.SerializerMethodField()
    proposal_action_type = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "status",
            "summary",
            "proposal_amount",
            "proposal_action_type",
            "risk_level",
            "expires_at",
            "is_expired",
            "created_at",
        ]
        read_only_fields = fields

    def get_proposal_amount(self, obj: ApprovalRequest) -> str | None:
        if obj.proposal.amount is not None:
            return str(obj.proposal.amount)
        return None

    def get_proposal_action_type(self, obj: ApprovalRequest) -> str:
        return str(obj.proposal.action_type)

    def get_risk_level(self, obj: ApprovalRequest) -> str:
        return str(obj.policy_decision.risk_level)


class ApprovalDecisionCreateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Serializer for creating an approval decision.

    ``decision`` is optional in the body when using /approve|/reject|/modify
    endpoints (the path determines the decision). Required when calling a
    generic decide endpoint.
    """

    decision = serializers.ChoiceField(
        choices=[
            ApprovalStatus.APPROVED.value,
            ApprovalStatus.REJECTED.value,
            ApprovalStatus.MODIFIED.value,
        ],
        required=False,
    )
    modifications = serializers.JSONField(required=False, allow_null=True)
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        default="",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Require modifications only when decision is MODIFIED."""
        decision = attrs.get("decision")
        modifications = attrs.get("modifications")

        if decision == ApprovalStatus.MODIFIED.value and not modifications:
            raise serializers.ValidationError(
                {"modifications": "Modifications must be provided when decision is MODIFIED."}
            )

        if decision and decision != ApprovalStatus.MODIFIED.value and modifications:
            raise serializers.ValidationError(
                {
                    "modifications": "Modifications should only be provided when decision is MODIFIED."
                }
            )

        return attrs
