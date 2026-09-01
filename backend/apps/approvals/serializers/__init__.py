"""Approvals serializers.

This module exports all serializers from the approvals app.
"""

from apps.approvals.serializers.approval_request import (
    ApprovalRequestSerializer,
    ResolveApprovalSerializer,
)

__all__ = ["ApprovalRequestSerializer", "ResolveApprovalSerializer"]
