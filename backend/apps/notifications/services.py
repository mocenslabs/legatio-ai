"""
WebSocket notification services.

Provides functions to send WebSocket events to users and negotiation rooms.
Source: 02-ARCHITECTURE.md Section 10.2
"""

import logging
from typing import Any
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger("legatio.notifications.websocket")


def send_to_user(user_id: UUID, event_type: str, payload: dict[str, Any]) -> None:
    """Send a WebSocket event to a specific user."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer not configured, skipping WebSocket send")
            return
        room_name = f"user_{user_id}"
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": event_type.replace(".", "_"),
                "payload": payload,
            },
        )
        logger.info(f"Sent {event_type} to user {user_id}")
    except Exception as exc:
        logger.error(f"Failed to send {event_type} to user {user_id}: {exc}")


def send_to_negotiation(negotiation_id: UUID, event_type: str, payload: dict[str, Any]) -> None:
    """Send a WebSocket event to all participants in a negotiation."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer not configured, skipping WebSocket send")
            return
        room_name = f"negotiation_{negotiation_id}"
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": event_type.replace(".", "_"),
                "payload": payload,
            },
        )
        logger.info(f"Sent {event_type} to negotiation {negotiation_id}")
    except Exception as exc:
        logger.error(f"Failed to send {event_type} to negotiation {negotiation_id}: {exc}")


def notify_approval_required(
    user_id: UUID,
    approval_id: UUID,
    summary: str,
    risk_level: str,
    expires_at: str,
    negotiation_id: UUID | None = None,
) -> None:
    """Notify user that approval is required."""
    payload: dict[str, Any] = {
        "approval_id": str(approval_id),
        "summary": summary,
        "risk_level": risk_level,
        "expires_at": expires_at,
    }
    if negotiation_id is not None:
        payload["negotiation_id"] = str(negotiation_id)
    send_to_user(
        user_id=user_id,
        event_type="approval.required",
        payload=payload,
    )


def notify_approval_decided(
    user_id: UUID,
    approval_id: UUID,
    decision: str,
) -> None:
    """Notify user that approval was decided."""
    event_type = "approval.approved" if decision == "APPROVED" else "approval.rejected"
    send_to_user(
        user_id=user_id,
        event_type=event_type,
        payload={
            "approval_id": str(approval_id),
            "decision": decision,
        },
    )


def notify_proposal_created(
    negotiation_id: UUID,
    proposal_id: UUID,
    amount: str | None,
    action_type: str,
) -> None:
    """Notify negotiation participants that a proposal was created."""
    send_to_negotiation(
        negotiation_id=negotiation_id,
        event_type="proposal.created",
        payload={
            "proposal_id": str(proposal_id),
            "amount": amount,
            "action_type": action_type,
        },
    )


def notify_proposal_evaluated(
    negotiation_id: UUID,
    proposal_id: UUID,
    outcome: str,
    risk_level: str | None = None,
) -> None:
    """Notify negotiation participants that a proposal was evaluated by the policy engine."""
    send_to_negotiation(
        negotiation_id=negotiation_id,
        event_type="proposal.evaluated",
        payload={
            "proposal_id": str(proposal_id),
            "outcome": outcome,
            "risk_level": risk_level,
        },
    )


def notify_counterproposal_created(
    negotiation_id: UUID,
    counterproposal_id: UUID,
    proposal_id: UUID,
    adjustments: dict[str, Any] | None = None,
) -> None:
    """Notify negotiation participants that a counter-proposal was created."""
    send_to_negotiation(
        negotiation_id=negotiation_id,
        event_type="counterproposal.created",
        payload={
            "counterproposal_id": str(counterproposal_id),
            "proposal_id": str(proposal_id),
            "adjustments": adjustments or {},
        },
    )


def notify_negotiation_started(
    user_id: UUID,
    negotiation_id: UUID,
    title: str,
) -> None:
    """Notify user that a negotiation has started."""
    send_to_user(
        user_id=user_id,
        event_type="negotiation.started",
        payload={
            "negotiation_id": str(negotiation_id),
            "title": title,
        },
    )


def notify_negotiation_completed(
    user_id: UUID,
    negotiation_id: UUID,
    outcome: str,
) -> None:
    """Notify user that a negotiation has completed."""
    send_to_user(
        user_id=user_id,
        event_type="negotiation.completed",
        payload={
            "negotiation_id": str(negotiation_id),
            "outcome": outcome,
        },
    )


def notify_agreement_created(
    user_id: UUID,
    agreement_id: UUID,
    negotiation_id: UUID,
) -> None:
    """Notify user that an agreement has been created."""
    send_to_user(
        user_id=user_id,
        event_type="agreement.created",
        payload={
            "agreement_id": str(agreement_id),
            "negotiation_id": str(negotiation_id),
        },
    )
