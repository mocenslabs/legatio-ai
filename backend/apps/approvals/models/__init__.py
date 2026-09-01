"""Approvals models.

This module exports all models from the approvals app.
"""

from apps.approvals.models.approval_request import ApprovalRequest, ApprovalStatus

__all__ = ["ApprovalRequest", "ApprovalStatus"]
