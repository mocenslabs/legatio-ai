"""Unit tests for Notification model.

Tests cover creation, properties, and status transitions.
"""

from __future__ import annotations

import uuid

import pytest

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationStatus, NotificationType


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
class TestNotification:
    """Tests for Notification model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify notification can be created with minimal fields."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test Notification",
        )

        assert notification.notification_type == NotificationType.SYSTEM
        assert notification.recipient == user
        assert notification.title == "Test Notification"
        assert notification.status == NotificationStatus.UNREAD
        assert notification.entity_type == ""
        assert notification.entity_id is None

    def test_notify_classmethod(self, user: User) -> None:
        """Verify the notify classmethod creates a notification."""
        notification = Notification.notify(
            notification_type=NotificationType.PROPOSAL_APPROVED,
            recipient_id=user.id,
            title="Proposal approved",
            message="Your proposal was approved.",
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        assert notification.recipient_id == user.id
        assert notification.status == NotificationStatus.UNREAD
        assert Notification.objects.count() == 1

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes type and status."""
        notification = Notification.objects.create(
            notification_type=NotificationType.PROPOSAL_DENIED,
            recipient=user,
            title="Proposal denied",
        )

        assert "PROPOSAL_DENIED" in str(notification)
        assert "UNREAD" in str(notification)

    def test_default_status_is_unread(self, user: User) -> None:
        """Verify default status is UNREAD."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        assert notification.status == NotificationStatus.UNREAD

    def test_is_read_false_when_unread(self, user: User) -> None:
        """Verify is_read returns False when status is UNREAD."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        assert notification.is_read is False

    def test_is_read_true_when_read(self, user: User) -> None:
        """Verify is_read returns True when status is READ."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
            status=NotificationStatus.READ,
        )

        assert notification.is_read is True

    def test_mark_as_read(self, user: User) -> None:
        """Verify mark_as_read updates status and read_at."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        notification.mark_as_read()

        assert notification.status == NotificationStatus.READ
        assert notification.read_at is not None

    def test_mark_as_read_idempotent(self, user: User) -> None:
        """Verify mark_as_read doesn't change already-read notifications."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
            status=NotificationStatus.READ,
        )

        notification.mark_as_read()

        assert notification.status == NotificationStatus.READ

    def test_archive(self, user: User) -> None:
        """Verify archive sets status to ARCHIVED."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        notification.archive()

        assert notification.status == NotificationStatus.ARCHIVED

    def test_cascade_delete_with_recipient(self, user: User) -> None:
        """Verify notifications are deleted when recipient is deleted."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )
        notification_id = notification.id

        user.delete()

        assert not Notification.objects.filter(id=notification_id).exists()
