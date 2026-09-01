"""API tests for Notification endpoints.

Tests cover list, retrieve, filtering, actions, and access restrictions.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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


@pytest.fixture
def api_client(user: User) -> APIClient:
    """Create an authenticated API client.

    Args:
        user: The user fixture.

    Returns:
        Authenticated APIClient instance.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestNotificationList:
    """Tests for listing and retrieving notifications."""

    def test_list_notifications(self, api_client: APIClient, user: User) -> None:
        """Verify listing notifications returns paginated results."""
        Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Notification 1",
        )
        Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Notification 2",
        )

        url = reverse("notification-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_notification(self, api_client: APIClient, user: User) -> None:
        """Verify retrieving a single notification works."""
        notification = Notification.objects.create(
            notification_type=NotificationType.PROPOSAL_APPROVED,
            recipient=user,
            title="Proposal approved",
        )

        url = reverse("notification-detail", kwargs={"pk": notification.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Proposal approved"
        assert response.data["status"] == "UNREAD"
        assert response.data["is_read"] is False

    def test_filter_by_status(self, api_client: APIClient, user: User) -> None:
        """Verify filtering notifications by status works."""
        Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Unread",
        )
        Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Read",
            status=NotificationStatus.READ,
        )

        url = reverse("notification-list")
        response = api_client.get(url, {"status": "UNREAD"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Unread"

    def test_filter_by_notification_type(self, api_client: APIClient, user: User) -> None:
        """Verify filtering notifications by notification_type works."""
        Notification.objects.create(
            notification_type=NotificationType.PROPOSAL_APPROVED,
            recipient=user,
            title="Approved",
        )
        Notification.objects.create(
            notification_type=NotificationType.PROPOSAL_DENIED,
            recipient=user,
            title="Denied",
        )

        url = reverse("notification-list")
        response = api_client.get(url, {"notification_type": NotificationType.PROPOSAL_DENIED})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Denied"


@pytest.mark.django_db
class TestNotificationActions:
    """Tests for notification actions (mark_as_read, archive)."""

    def test_mark_as_read(self, api_client: APIClient, user: User) -> None:
        """Verify marking a notification as read updates its status."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        url = reverse("notification-mark-as-read", kwargs={"pk": notification.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "READ"
        assert response.data["is_read"] is True
        assert response.data["read_at"] is not None

    def test_archive(self, api_client: APIClient, user: User) -> None:
        """Verify archiving a notification updates its status."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        url = reverse("notification-archive", kwargs={"pk": notification.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ARCHIVED"


@pytest.mark.django_db
class TestNotificationRestrictions:
    """Tests for access restrictions on notifications."""

    def test_create_not_allowed(self, api_client: APIClient, user: User) -> None:
        """Verify creating notifications via API returns 405."""
        url = reverse("notification-list")
        data = {
            "notification_type": NotificationType.SYSTEM,
            "recipient": str(user.id),
            "title": "Test",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, api_client: APIClient, user: User) -> None:
        """Verify deleting notifications via API returns 405."""
        notification = Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        url = reverse("notification-detail", kwargs={"pk": notification.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_unauthenticated_returns_401(self, user: User) -> None:
        """Verify unauthenticated requests return 401."""
        Notification.objects.create(
            notification_type=NotificationType.SYSTEM,
            recipient=user,
            title="Test",
        )

        client = APIClient()
        url = reverse("notification-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
