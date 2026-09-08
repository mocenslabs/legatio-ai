"""API tests for WebhookSubscription endpoints.

Tests cover CRUD operations, filtering, and access restrictions.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.webhooks.models import WebhookEventType, WebhookSubscription


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="creator@example.com", password="testpass123")


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


@pytest.fixture
def subscription(db: None, user: User) -> WebhookSubscription:
    """Create a test webhook subscription.

    Args:
        db: The database fixture.
        user: The user fixture.

    Returns:
        A WebhookSubscription instance.
    """
    return WebhookSubscription.objects.create(
        name="Test Subscription",
        url="https://example.com/webhook",
        events=[WebhookEventType.PROPOSAL_CREATED],
        created_by=user,
        is_active=True,
    )


@pytest.mark.django_db
class TestWebhookSubscriptionAPI:
    """Tests for WebhookSubscription API endpoints."""

    def test_create_subscription(self, api_client: APIClient, user: User) -> None:
        """Verify creating a subscription returns 201 and sets created_by."""
        url = reverse("webhooksubscription-list")
        data = {
            "name": "New Subscription",
            "url": "https://example.com/new-webhook",
            "events": [WebhookEventType.AGREEMENT_ACTIVATED],
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Subscription"
        assert response.data["created_by"] == user.id
        assert "secret" in response.data
        assert len(response.data["secret"]) == 64

    def test_list_subscriptions(self, api_client: APIClient, user: User) -> None:
        """Verify listing subscriptions returns paginated results."""
        WebhookSubscription.objects.create(
            name="Sub 1", url="https://example.com/1", created_by=user
        )
        WebhookSubscription.objects.create(
            name="Sub 2", url="https://example.com/2", created_by=user
        )

        url = reverse("webhooksubscription-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_subscription(
        self, api_client: APIClient, subscription: WebhookSubscription
    ) -> None:
        """Verify retrieving a single subscription works."""
        url = reverse("webhooksubscription-detail", kwargs={"pk": subscription.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Subscription"
        assert response.data["url"] == "https://example.com/webhook"

    def test_update_subscription(
        self, api_client: APIClient, subscription: WebhookSubscription
    ) -> None:
        """Verify updating a subscription works."""
        url = reverse("webhooksubscription-detail", kwargs={"pk": subscription.id})
        data = {"name": "Updated Subscription"}

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Subscription"

    def test_delete_subscription(
        self, api_client: APIClient, subscription: WebhookSubscription
    ) -> None:
        """Verify deleting a subscription returns 204."""
        url = reverse("webhooksubscription-detail", kwargs={"pk": subscription.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not WebhookSubscription.objects.filter(id=subscription.id).exists()

    def test_filter_by_is_active(self, api_client: APIClient, user: User) -> None:
        """Verify filtering subscriptions by is_active works."""
        WebhookSubscription.objects.create(
            name="Active Sub", url="https://example.com/1", created_by=user, is_active=True
        )
        WebhookSubscription.objects.create(
            name="Inactive Sub", url="https://example.com/2", created_by=user, is_active=False
        )

        url = reverse("webhooksubscription-list")
        response = api_client.get(url, {"is_active": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["is_active"] is True

    def test_unauthenticated_returns_401(self) -> None:
        """Verify unauthenticated requests return 401."""
        client = APIClient()
        url = reverse("webhooksubscription-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
