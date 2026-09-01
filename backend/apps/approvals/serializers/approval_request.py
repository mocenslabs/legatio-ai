"""ApprovalRequest serializers.

This module provides DRF serializers for the ApprovalRequest model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.approvals.models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """Serializer for ApprovalRequest model.

    Approval requests are created automatically by the service layer,
    so all fields are read-only in this serializer.
    """

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "proposal",
            "required_role",
            "assigned_to",
            "status",
            "decided_by",
            "decided_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "proposal",
            "required_role",
            "assigned_to",
            "status",
            "decided_by",
            "decided_at",
            "notes",
            "created_at",
            "updated_at",
        ]


class ResolveApprovalSerializer(serializers.Serializer):
    """Serializer for resolving an approval request.

    Validates the input for approving or rejecting an approval request.
    """

    approved = serializers.BooleanField(
        help_text="True to approve, False to reject.",
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional notes from the approver.",
    )
