"""Notification Service layer.

This module provides a service for creating and managing user notifications
throughout the system, wrapping the Notification model with convenient methods.
"""

from __future__ import annotations

import uuid

from apps.notifications.models import Notification, NotificationType


class NotificationService:
    """Service layer for notification operations.

    Provides convenient methods for creating notifications related to
    proposal lifecycle events and approval requests.
    """

    @staticmethod
    def notify_proposal_status(
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str = "",
    ) -> Notification:
        """Create a notification about a proposal status change.

        Args:
            proposal_id: The UUID of the proposal.
            recipient_id: The UUID of the user to notify.
            notification_type: The type of notification.
            title: Short human-readable title.
            message: Detailed notification message.

        Returns:
            The created Notification instance.
        """
        return Notification.notify(
            notification_type=notification_type,
            recipient_id=recipient_id,
            title=title,
            message=message,
            entity_type="Proposal",
            entity_id=proposal_id,
        )

    @staticmethod
    def notify_approval_requested(
        approval_id: uuid.UUID,
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        required_role: str,
        proposal_title: str,
    ) -> Notification:
        """Create a notification for a new approval request.

        Args:
            approval_id: The UUID of the approval request.
            proposal_id: The UUID of the related proposal.
            recipient_id: The UUID of the user to notify.
            required_role: The role required to approve.
            proposal_title: The title of the proposal.

        Returns:
            The created Notification instance.
        """
        title = f"Approval required: {proposal_title}"
        message = (
            f"Approval is required from role '{required_role}' " f"for proposal '{proposal_title}'."
        )
        return Notification.notify(
            notification_type=NotificationType.APPROVAL_REQUESTED,
            recipient_id=recipient_id,
            title=title,
            message=message,
            entity_type="ApprovalRequest",
            entity_id=approval_id,
        )

    @staticmethod
    def notify_proposal_approved(
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        proposal_title: str,
    ) -> Notification:
        """Notify a user that their proposal was approved.

        Args:
            proposal_id: The UUID of the proposal.
            recipient_id: The UUID of the user to notify.
            proposal_title: The title of the proposal.

        Returns:
            The created Notification instance.
        """
        return NotificationService.notify_proposal_status(
            proposal_id=proposal_id,
            recipient_id=recipient_id,
            notification_type=NotificationType.PROPOSAL_APPROVED,
            title=f"Proposal approved: {proposal_title}",
            message=f"Your proposal '{proposal_title}' has been approved.",
        )

    @staticmethod
    def notify_proposal_denied(
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        proposal_title: str,
        reason: str = "",
    ) -> Notification:
        """Notify a user that their proposal was denied.

        Args:
            proposal_id: The UUID of the proposal.
            recipient_id: The UUID of the user to notify.
            proposal_title: The title of the proposal.
            reason: Optional reason for the denial.

        Returns:
            The created Notification instance.
        """
        message = f"Your proposal '{proposal_title}' has been denied."
        if reason:
            message = f"{message} Reason: {reason}"
        return NotificationService.notify_proposal_status(
            proposal_id=proposal_id,
            recipient_id=recipient_id,
            notification_type=NotificationType.PROPOSAL_DENIED,
            title=f"Proposal denied: {proposal_title}",
            message=message,
        )

    @staticmethod
    def notify_proposal_executed(
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        proposal_title: str,
    ) -> Notification:
        """Notify a user that their proposal was executed.

        Args:
            proposal_id: The UUID of the proposal.
            recipient_id: The UUID of the user to notify.
            proposal_title: The title of the proposal.

        Returns:
            The created Notification instance.
        """
        return NotificationService.notify_proposal_status(
            proposal_id=proposal_id,
            recipient_id=recipient_id,
            notification_type=NotificationType.PROPOSAL_EXECUTED,
            title=f"Proposal executed: {proposal_title}",
            message=f"Your proposal '{proposal_title}' has been executed.",
        )

    @staticmethod
    def notify_proposal_cancelled(
        proposal_id: uuid.UUID,
        recipient_id: uuid.UUID,
        proposal_title: str,
    ) -> Notification:
        """Notify a user that their proposal was cancelled.

        Args:
            proposal_id: The UUID of the proposal.
            recipient_id: The UUID of the user to notify.
            proposal_title: The title of the proposal.

        Returns:
            The created Notification instance.
        """
        return NotificationService.notify_proposal_status(
            proposal_id=proposal_id,
            recipient_id=recipient_id,
            notification_type=NotificationType.PROPOSAL_CANCELLED,
            title=f"Proposal cancelled: {proposal_title}",
            message=f"Your proposal '{proposal_title}' has been cancelled.",
        )
