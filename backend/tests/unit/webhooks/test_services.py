"""Unit tests for WebhookService.

Tests cover event triggering and subscription dispatching.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.accounts.models import User
from apps.webhooks.models import WebhookEventType, WebhookSubscription
from apps.webhooks.services import WebhookService


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
class TestWebhookServiceTriggerEvent:
    """Tests for WebhookService.trigger_event."""

    def test_dispatches_to_matching_subscriptions(self, user: User) -> None:
        """Verify event is dispatched to subscriptions listening to it."""
        WebhookSubscription.objects.create(
            name="Matching Subscription",
            url="https://example.com/webhook",
            events=[WebhookEventType.PROPOSAL_CREATED],
            created_by=user,
            is_active=True,
        )

        with patch(
            "apps.webhooks.services.webhook_service.deliver_webhook_task.delay"
        ) as mock_delay:
            dispatched = WebhookService.trigger_event(
                WebhookEventType.PROPOSAL_CREATED,
                {"proposal_id": "test-id"},
            )

        assert dispatched == 1
        mock_delay.assert_called_once()

    def test_skips_subscriptions_not_listening(self, user: User) -> None:
        """Verify event is not dispatched to subscriptions not listening."""
        WebhookSubscription.objects.create(
            name="Non-Matching Subscription",
            url="https://example.com/webhook",
            events=[WebhookEventType.AGREEMENT_ACTIVATED],
            created_by=user,
            is_active=True,
        )

        with patch(
            "apps.webhooks.services.webhook_service.deliver_webhook_task.delay"
        ) as mock_delay:
            dispatched = WebhookService.trigger_event(
                WebhookEventType.PROPOSAL_CREATED,
                {"proposal_id": "test-id"},
            )

        assert dispatched == 0
        mock_delay.assert_not_called()

    def test_skips_inactive_subscriptions(self, user: User) -> None:
        """Verify event is not dispatched to inactive subscriptions."""
        WebhookSubscription.objects.create(
            name="Inactive Subscription",
            url="https://example.com/webhook",
            events=[WebhookEventType.PROPOSAL_CREATED],
            created_by=user,
            is_active=False,
        )

        with patch(
            "apps.webhooks.services.webhook_service.deliver_webhook_task.delay"
        ) as mock_delay:
            dispatched = WebhookService.trigger_event(
                WebhookEventType.PROPOSAL_CREATED,
                {"proposal_id": "test-id"},
            )

        assert dispatched == 0
        mock_delay.assert_not_called()

    def test_dispatches_to_multiple_subscriptions(self, user: User) -> None:
        """Verify event is dispatched to all matching subscriptions."""
        WebhookSubscription.objects.create(
            name="Subscription 1",
            url="https://example.com/1",
            events=[WebhookEventType.PROPOSAL_CREATED],
            created_by=user,
            is_active=True,
        )
        WebhookSubscription.objects.create(
            name="Subscription 2",
            url="https://example.com/2",
            events=[WebhookEventType.PROPOSAL_CREATED],
            created_by=user,
            is_active=True,
        )

        with patch(
            "apps.webhooks.services.webhook_service.deliver_webhook_task.delay"
        ) as mock_delay:
            dispatched = WebhookService.trigger_event(
                WebhookEventType.PROPOSAL_CREATED,
                {"proposal_id": "test-id"},
            )

        assert dispatched == 2
        assert mock_delay.call_count == 2

    def test_returns_zero_when_no_subscriptions(self, user: User) -> None:
        """Verify returns 0 when no subscriptions match."""
        with patch(
            "apps.webhooks.services.webhook_service.deliver_webhook_task.delay"
        ) as mock_delay:
            dispatched = WebhookService.trigger_event(
                WebhookEventType.PROPOSAL_CREATED,
                {"proposal_id": "test-id"},
            )

        assert dispatched == 0
        mock_delay.assert_not_called()
