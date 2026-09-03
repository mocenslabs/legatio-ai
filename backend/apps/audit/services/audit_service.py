"""Audit Service layer.

This module provides a service for recording audit events throughout the
system, wrapping the AuditLog model with convenient, typed methods.
"""

from __future__ import annotations

import uuid
from typing import Any

from apps.audit.models import AuditLog


class AuditService:
    """Service layer for audit logging operations.

    Provides convenient methods for recording common audit events related
    to proposals and approvals. All methods are fire-safe within the
    caller's transaction.
    """

    @staticmethod
    def _log(
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an audit event.

        Args:
            action: The type of action performed.
            entity_type: The model name of the affected entity.
            entity_id: The UUID of the affected entity.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous state before the transition.
            new_state: New state after the transition.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditLog.log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_proposal_event(
        action: str,
        proposal_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record a proposal-related audit event.

        Args:
            action: The proposal action performed.
            proposal_id: The UUID of the proposal.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous proposal state.
            new_state: New proposal state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="Proposal",
            entity_id=proposal_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_approval_event(
        action: str,
        approval_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an approval-related audit event.

        Args:
            action: The approval action performed.
            approval_id: The UUID of the approval request.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous approval state.
            new_state: New approval state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="ApprovalRequest",
            entity_id=approval_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_policy_rule_event(
        action: str,
        rule_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record a policy-rule-related audit event.

        Args:
            action: The policy rule action performed.
            rule_id: The UUID of the policy rule.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous rule state.
            new_state: New rule state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="PolicyRule",
            entity_id=rule_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_agreement_event(
        action: str,
        agreement_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an agreement-related audit event.

        Args:
            action: The agreement action performed.
            agreement_id: The UUID of the agreement.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous agreement state.
            new_state: New agreement state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="Agreement",
            entity_id=agreement_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_negotiation_event(
        action: str,
        negotiation_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record a negotiation-related audit event.

        Args:
            action: The negotiation action performed.
            negotiation_id: The UUID of the negotiation.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous negotiation state.
            new_state: New negotiation state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="Negotiation",
            entity_id=negotiation_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )

    @staticmethod
    def log_comment_event(
        action: str,
        comment_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        old_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record a comment-related audit event.

        Args:
            action: The comment action performed.
            comment_id: The UUID of the comment.
            actor_id: The UUID of the user who performed the action.
            old_state: Previous comment state.
            new_state: New comment state.
            metadata: Additional context about the action.

        Returns:
            The created AuditLog instance.
        """
        return AuditService._log(
            action=action,
            entity_type="Comment",
            entity_id=comment_id,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata,
        )
