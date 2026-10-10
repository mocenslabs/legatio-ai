"""
Unit tests for WebSocket notification services.
Source: 02-ARCHITECTURE.md Section 10.2
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.notifications.services import (
    notify_approval_decided,
    notify_approval_required,
    notify_negotiation_started,
    notify_proposal_created,
    send_to_negotiation,
    send_to_user,
)


@pytest.mark.django_db(transaction=True)
class TestWebSocketServices:
    def test_send_to_user(self) -> None:
        """send_to_user calls channel layer correctly."""
        user_id = uuid4()
        with (
            patch("apps.notifications.services.get_channel_layer") as mock_get_layer,
            patch("apps.notifications.services.async_to_sync") as mock_async_to_sync,
        ):
            mock_layer = MagicMock()
            mock_get_layer.return_value = mock_layer
            mock_group_send = mock_async_to_sync.return_value
            send_to_user(
                user_id=user_id,
                event_type="approval.required",
                payload={"test": "data"},
            )
            mock_async_to_sync.assert_called_once_with(mock_layer.group_send)
            mock_group_send.assert_called_once()
            call_args = mock_group_send.call_args
            assert call_args[0][0] == f"user_{user_id}"
            assert call_args[0][1]["type"] == "approval_required"

    def test_send_to_user_no_channel_layer(self) -> None:
        """send_to_user handles missing channel layer gracefully."""
        with patch("apps.notifications.services.get_channel_layer", return_value=None):
            # Should not raise
            send_to_user(
                user_id=uuid4(),
                event_type="approval.required",
                payload={"test": "data"},
            )

    def test_send_to_negotiation(self) -> None:
        """send_to_negotiation calls channel layer correctly."""
        negotiation_id = uuid4()
        with (
            patch("apps.notifications.services.get_channel_layer") as mock_get_layer,
            patch("apps.notifications.services.async_to_sync") as mock_async_to_sync,
        ):
            mock_layer = MagicMock()
            mock_get_layer.return_value = mock_layer
            mock_group_send = mock_async_to_sync.return_value
            send_to_negotiation(
                negotiation_id=negotiation_id,
                event_type="proposal.created",
                payload={"test": "data"},
            )
            mock_async_to_sync.assert_called_once_with(mock_layer.group_send)
            mock_group_send.assert_called_once()
            call_args = mock_group_send.call_args
            assert call_args[0][0] == f"negotiation_{negotiation_id}"
            assert call_args[0][1]["type"] == "proposal_created"

    def test_notify_approval_required(self) -> None:
        """notify_approval_required sends correct event."""
        user_id = uuid4()
        approval_id = uuid4()
        with patch("apps.notifications.services.send_to_user") as mock_send:
            notify_approval_required(
                user_id=user_id,
                approval_id=approval_id,
                negotiation_id=uuid4(),
                summary="Test summary",
                risk_level="LOW",
                expires_at="2026-10-02T00:00:00Z",
            )
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["event_type"] == "approval.required"
            assert call_args[1]["payload"]["approval_id"] == str(approval_id)

    def test_notify_approval_decided_approved(self) -> None:
        """notify_approval_decided sends approval.approved for APPROVED."""
        user_id = uuid4()
        with patch("apps.notifications.services.send_to_user") as mock_send:
            notify_approval_decided(
                user_id=user_id,
                approval_id=uuid4(),
                decision="APPROVED",
            )
            call_args = mock_send.call_args
            assert call_args[1]["event_type"] == "approval.approved"

    def test_notify_approval_decided_rejected(self) -> None:
        """notify_approval_decided sends approval.rejected for REJECTED."""
        user_id = uuid4()
        with patch("apps.notifications.services.send_to_user") as mock_send:
            notify_approval_decided(
                user_id=user_id,
                approval_id=uuid4(),
                decision="REJECTED",
            )
            call_args = mock_send.call_args
            assert call_args[1]["event_type"] == "approval.rejected"

    def test_notify_proposal_created(self) -> None:
        """notify_proposal_created sends correct event."""
        negotiation_id = uuid4()
        proposal_id = uuid4()
        with patch("apps.notifications.services.send_to_negotiation") as mock_send:
            notify_proposal_created(
                negotiation_id=negotiation_id,
                proposal_id=proposal_id,
                amount="700.00",
                action_type="purchase",
            )
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["event_type"] == "proposal.created"
            assert call_args[1]["payload"]["proposal_id"] == str(proposal_id)

    def test_notify_negotiation_started(self) -> None:
        """notify_negotiation_started sends correct event."""
        user_id = uuid4()
        negotiation_id = uuid4()
        with patch("apps.notifications.services.send_to_user") as mock_send:
            notify_negotiation_started(
                user_id=user_id,
                negotiation_id=negotiation_id,
                title="Test Negotiation",
            )
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["event_type"] == "negotiation.started"
            assert call_args[1]["payload"]["title"] == "Test Negotiation"
