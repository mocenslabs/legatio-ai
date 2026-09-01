"""Proposal serializers.

This module provides DRF serializers for the Proposal model, including
list, detail, and creation variants.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.approvals.serializers import ApprovalRequestSerializer
from apps.proposals.models import Proposal


class ProposalSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model (standard representation).

    Provides fields for listing and retrieving proposals. The status,
    policy_decision, and created_by fields are read-only as they are
    managed by the service layer.
    """

    class Meta:
        model = Proposal
        fields = [
            "id",
            "title",
            "description",
            "action_type",
            "target_resource",
            "payload",
            "status",
            "policy_decision",
            "created_by",
            "constitution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "policy_decision",
            "created_by",
            "created_at",
            "updated_at",
        ]


class ProposalDetailSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model with nested approval requests.

    Extends the standard representation with approval requests and
    computed status flags for detailed views.
    """

    approval_requests = ApprovalRequestSerializer(many=True, read_only=True)
    requires_approval = serializers.BooleanField(read_only=True)
    can_be_executed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id",
            "title",
            "description",
            "action_type",
            "target_resource",
            "payload",
            "status",
            "policy_decision",
            "created_by",
            "constitution",
            "approval_requests",
            "requires_approval",
            "can_be_executed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "policy_decision",
            "created_by",
            "approval_requests",
            "requires_approval",
            "can_be_executed",
            "created_at",
            "updated_at",
        ]


class ProposalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating proposals.

    Validates input for proposal creation. All proposals are created in
    DRAFT status via the service layer.
    """

    class Meta:
        model = Proposal
        fields = [
            "title",
            "description",
            "action_type",
            "target_resource",
            "payload",
            "constitution",
        ]

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
