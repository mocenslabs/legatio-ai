"""Unit tests for WebhookSubscription model.

Tests cover creation, properties, and string representation.
"""

from __future__ import annotations

import pytest

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


@pytest.mark.django_db
class TestWebhookSubscription:
    """Tests for WebhookSubscription model."""

    def test_create_minimal(self, user: User) -> None:
        """Verify subscription can be created with minimal fields."""
        subscription = WebhookSubscription.objects.create(
            name="Test Subscription",
            url="https://example.com/webhook",
            created_by=user,
        )

        assert subscription.name == "Test Subscription"
        assert subscription.url == "https://example.com/webhook"
        assert subscription.is_active is True
        assert subscription.events == []
        assert len(subscription.secret) == 64  # 32 bytes hex encoded

    def test_create_with_events(self, user: User) -> None:
        """Verify subscription can be created with event types."""
        subscription = WebhookSubscription.objects.create(
            name="Multi-Event Subscription",
            url="https://example.com/webhook",
            events=[
                WebhookEventType.PROPOSAL_CREATED,
                WebhookEventType.AGREEMENT_ACTIVATED,
            ],
            created_by=user,
        )

        assert len(subscription.events) == 2
        assert WebhookEventType.PROPOSAL_CREATED in subscription.events
        assert WebhookEventType.AGREEMENT_ACTIVATED in subscription.events

    def test_str_representation(self, user: User) -> None:
        """Verify string representation includes name and URL."""
        subscription = WebhookSubscription.objects.create(
            name="My Subscription",
            url="https://example.com/webhook",
            created_by=user,
        )

        assert str(subscription) == "My Subscription (https://example.com/webhook)"

    def test_active_events_filters_empty(self, user: User) -> None:
        """Verify active_events returns empty list when no events configured."""
        subscription = WebhookSubscription.objects.create(
            name="Empty Events",
            url="https://example.com/webhook",
            created_by=user,
        )

        assert subscription.active_events == []

    def test_active_events_filters_configured(self, user: User) -> None:
        """Verify active_events returns configured events."""
        subscription = WebhookSubscription.objects.create(
            name="Configured Events",
            url="https://example.com/webhook",
            events=[WebhookEventType.PROPOSAL_CREATED],
            created_by=user,
        )

        assert subscription.active_events == [WebhookEventType.PROPOSAL_CREATED]

    def test_secret_auto_generated(self, user: User) -> None:
        """Verify secret is auto-generated when not provided."""
        subscription = WebhookSubscription.objects.create(
            name="Auto Secret",
            url="https://example.com/webhook",
            created_by=user,
        )

        assert subscription.secret is not None
        assert len(subscription.secret) > 0

    def test_secret_custom(self, user: User) -> None:
        """Verify custom secret can be provided."""
        custom_secret = "my-custom-secret-key"
        subscription = WebhookSubscription.objects.create(
            name="Custom Secret",
            url="https://example.com/webhook",
            secret=custom_secret,
            created_by=user,
        )

        assert subscription.secret == custom_secret

    def test_ordering_by_created_at_desc(self, user: User) -> None:
        """Verify subscriptions are ordered by created_at descending."""
        sub1 = WebhookSubscription.objects.create(
            name="First",
            url="https://example.com/1",
            created_by=user,
        )
        sub2 = WebhookSubscription.objects.create(
            name="Second",
            url="https://example.com/2",
            created_by=user,
        )

        subscriptions = list(WebhookSubscription.objects.all())

        assert subscriptions[0].id == sub2.id
        assert subscriptions[1].id == sub1.id
