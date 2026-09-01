"""Unit tests for NotificationService.

Tests cover the typed convenience methods for creating notifications.
"""

from __future__ import annotations

import uuid

import pytest

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationType
from apps.notifications.services import NotificationService


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="recipient@example.com", password="testpass123")


@pytest.mark.django_db
class TestNotificationService:
    """Tests for NotificationService class."""

    def test_notify_proposal_status(self, user: User) -> None:
        """Verify proposal status notifications are created."""
        proposal_id = uuid.uuid4()

        NotificationService.notify_proposal_status(
            proposal_id=proposal_id,
            recipient_id=user.id,
            notification_type=NotificationType.PROPOSAL_APPROVED,
            title="Approved",
            message="Your proposal was approved.",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_APPROVED
        assert notification.entity_type == "Proposal"
        assert notification.entity_id == proposal_id

    def test_notify_approval_requested(self, user: User) -> None:
        """Verify approval request notifications are created."""
        approval_id = uuid.uuid4()
        proposal_id = uuid.uuid4()

        NotificationService.notify_approval_requested(
            approval_id=approval_id,
            proposal_id=proposal_id,
            recipient_id=user.id,
            required_role="manager",
            proposal_title="Test Proposal",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.APPROVAL_REQUESTED
        assert notification.entity_type == "ApprovalRequest"
        assert "manager" in notification.message

    def test_notify_proposal_approved(self, user: User) -> None:
        """Verify proposal approved notifications are created."""
        proposal_id = uuid.uuid4()

        NotificationService.notify_proposal_approved(
            proposal_id=proposal_id,
            recipient_id=user.id,
            proposal_title="Test Proposal",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_APPROVED
        assert "approved" in notification.title.lower()

    def test_notify_proposal_denied(self, user: User) -> None:
        """Verify proposal denied notifications include reason."""
        proposal_id = uuid.uuid4()

        NotificationService.notify_proposal_denied(
            proposal_id=proposal_id,
            recipient_id=user.id,
            proposal_title="Test Proposal",
            reason="Policy violation",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_DENIED
        assert "Policy violation" in notification.message

    def test_notify_proposal_executed(self, user: User) -> None:
        """Verify proposal executed notifications are created."""
        proposal_id = uuid.uuid4()

        NotificationService.notify_proposal_executed(
            proposal_id=proposal_id,
            recipient_id=user.id,
            proposal_title="Test Proposal",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_EXECUTED

    def test_notify_proposal_cancelled(self, user: User) -> None:
        """Verify proposal cancelled notifications are created."""
        proposal_id = uuid.uuid4()

        NotificationService.notify_proposal_cancelled(
            proposal_id=proposal_id,
            recipient_id=user.id,
            proposal_title="Test Proposal",
        )

        notification = Notification.objects.get(recipient=user)
        assert notification.notification_type == NotificationType.PROPOSAL_CANCELLED
