"""Unit tests for webhook Celery tasks.

Tests cover HMAC signature generation and webhook delivery.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from apps.accounts.models import User
from apps.webhooks.models import WebhookEventType, WebhookSubscription
from apps.webhooks.tasks import _generate_signature, deliver_webhook_task


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
        secret="test-secret-key",
        events=[WebhookEventType.PROPOSAL_CREATED],
        created_by=user,
        is_active=True,
    )


class TestGenerateSignature:
    """Tests for the _generate_signature helper function."""

    def test_signature_format(self) -> None:
        """Verify signature has correct format."""
        payload = {"key": "value"}
        signature = _generate_signature("secret", payload)

        assert signature.startswith("sha256=")
        assert len(signature) == 7 + 64  # "sha256=" + 64 hex chars

    def test_signature_is_deterministic(self) -> None:
        """Verify same payload and secret produce same signature."""
        payload = {"key": "value"}
        sig1 = _generate_signature("secret", payload)
        sig2 = _generate_signature("secret", payload)

        assert sig1 == sig2

    def test_signature_changes_with_different_secret(self) -> None:
        """Verify different secrets produce different signatures."""
        payload = {"key": "value"}
        sig1 = _generate_signature("secret1", payload)
        sig2 = _generate_signature("secret2", payload)

        assert sig1 != sig2

    def test_signature_changes_with_different_payload(self) -> None:
        """Verify different payloads produce different signatures."""
        sig1 = _generate_signature("secret", {"key": "value1"})
        sig2 = _generate_signature("secret", {"key": "value2"})

        assert sig1 != sig2

    def test_signature_ignores_key_order(self) -> None:
        """Verify signature is the same regardless of key order."""
        payload1 = {"a": 1, "b": 2}
        payload2 = {"b": 2, "a": 1}
        sig1 = _generate_signature("secret", payload1)
        sig2 = _generate_signature("secret", payload2)

        assert sig1 == sig2

    def test_signature_matches_manual_hmac(self) -> None:
        """Verify signature matches manually computed HMAC."""
        payload = {"key": "value"}
        secret = "my-secret"

        signature = _generate_signature(secret, payload)

        # Manually compute expected signature
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        secret_bytes = secret.encode("utf-8")
        expected = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()

        assert signature == f"sha256={expected}"


@pytest.mark.django_db
class TestDeliverWebhookTask:
    """Tests for the deliver_webhook_task Celery task."""

    def test_delivers_successfully(self, subscription: WebhookSubscription) -> None:
        """Verify webhook is delivered with correct headers."""
        payload = {"proposal_id": "test-id"}

        with patch("apps.webhooks.tasks.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            deliver_webhook_task.run(
                subscription_id=str(subscription.id),
                payload=payload,
                event_type=WebhookEventType.PROPOSAL_CREATED,
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["json"] == payload
        assert call_args.kwargs["headers"]["Content-Type"] == "application/json"
        assert call_args.kwargs["headers"]["X-Legatio-Event"] == WebhookEventType.PROPOSAL_CREATED
        assert "X-Legatio-Signature" in call_args.kwargs["headers"]

    def test_skips_inactive_subscription(self, subscription: WebhookSubscription) -> None:
        """Verify task skips inactive subscriptions."""
        subscription.is_active = False
        subscription.save()

        with patch("apps.webhooks.tasks.requests.post") as mock_post:
            deliver_webhook_task.run(
                subscription_id=str(subscription.id),
                payload={},
                event_type=WebhookEventType.PROPOSAL_CREATED,
            )

        mock_post.assert_not_called()

    def test_skips_nonexistent_subscription(self) -> None:
        """Verify task skips nonexistent subscriptions."""
        with patch("apps.webhooks.tasks.requests.post") as mock_post:
            deliver_webhook_task.run(
                subscription_id="00000000-0000-0000-0000-000000000000",
                payload={},
                event_type=WebhookEventType.PROPOSAL_CREATED,
            )

        mock_post.assert_not_called()

    def test_retries_on_failure(self, subscription: WebhookSubscription) -> None:
        """Verify task retries on HTTP failure."""
        with patch("apps.webhooks.tasks.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Connection error")

            with patch.object(deliver_webhook_task, "retry", side_effect=Exception("Retry called")):
                with pytest.raises(Exception, match="Retry called"):
                    deliver_webhook_task.run(
                        subscription_id=str(subscription.id),
                        payload={},
                        event_type=WebhookEventType.PROPOSAL_CREATED,
                    )

        mock_post.assert_called_once()
