"""
WebSocket consumers for real-time notifications.

Handles WebSocket connections for user notifications and negotiation updates.
Source: 02-ARCHITECTURE.md Section 10.1
Source: 04-BUSINESS-FLOW.md Section 14.1
"""

import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

logger = logging.getLogger("legatio.notifications.websocket")


class NotificationConsumer(AsyncWebsocketConsumer):  # type: ignore[misc]
    """
    WebSocket consumer for user notifications.

    Handles:
    - Approval requests (approval.required)
    - Approval decisions (approval.approved, approval.rejected)
    - Negotiation updates (negotiation.*)
    - Agreement events (agreement.*)
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.user = self.scope.get("user", AnonymousUser())
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection rejected")
            await self.close()
            return

        self.user_room = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_room, self.channel_name)

        negotiation_ids = await self.get_active_negotiations()
        self.negotiation_rooms = []
        for neg_id in negotiation_ids:
            room_name = f"negotiation_{neg_id}"
            await self.channel_layer.group_add(room_name, self.channel_name)
            self.negotiation_rooms.append(room_name)

        await self.accept()

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection.established",
                    "payload": {
                        "user_id": str(self.user.id),
                        "negotiation_rooms": self.negotiation_rooms,
                    },
                    "timestamp": self.get_timestamp(),
                }
            )
        )
        logger.info(f"WebSocket connected for user {self.user.id}")

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        if hasattr(self, "user_room"):
            await self.channel_layer.group_discard(self.user_room, self.channel_name)

        for room_name in getattr(self, "negotiation_rooms", []):
            await self.channel_layer.group_discard(room_name, self.channel_name)

        logger.info(f"WebSocket disconnected for user " f"{self.scope.get('user', 'unknown')}")

    async def receive(self, text_data: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            if message_type == "subscribe":
                negotiation_ids = data.get("payload", {}).get("negotiation_ids", [])
                for neg_id in negotiation_ids:
                    room_name = f"negotiation_{neg_id}"
                    if room_name not in self.negotiation_rooms:
                        await self.channel_layer.group_add(room_name, self.channel_name)
                        self.negotiation_rooms.append(room_name)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "subscription.confirmed",
                            "payload": {"negotiation_rooms": self.negotiation_rooms},
                            "timestamp": self.get_timestamp(),
                        }
                    )
                )
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "payload": {"message": "Invalid JSON"},
                        "timestamp": self.get_timestamp(),
                    }
                )
            )

    # ---- Event handlers for group messages ----
    async def approval_required(self, event: dict[str, Any]) -> None:
        """Handle approval.required event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "approval.required",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def approval_approved(self, event: dict[str, Any]) -> None:
        """Handle approval.approved event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "approval.approved",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def approval_rejected(self, event: dict[str, Any]) -> None:
        """Handle approval.rejected event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "approval.rejected",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def proposal_created(self, event: dict[str, Any]) -> None:
        """Handle proposal.created event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "proposal.created",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def proposal_evaluated(self, event: dict[str, Any]) -> None:
        """Handle proposal.evaluated event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "proposal.evaluated",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def counterproposal_created(self, event: dict[str, Any]) -> None:
        """Handle counterproposal.created event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "counterproposal.created",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def negotiation_started(self, event: dict[str, Any]) -> None:
        """Handle negotiation.started event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "negotiation.started",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def negotiation_completed(self, event: dict[str, Any]) -> None:
        """Handle negotiation.completed event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "negotiation.completed",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def agreement_created(self, event: dict[str, Any]) -> None:
        """Handle agreement.created event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "agreement.created",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    async def agreement_signed(self, event: dict[str, Any]) -> None:
        """Handle agreement.signed event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "agreement.signed",
                    "payload": event["payload"],
                    "timestamp": self.get_timestamp(),
                }
            )
        )

    @database_sync_to_async  # type: ignore[misc]
    def get_active_negotiations(self) -> list[str]:
        """Get list of active negotiation IDs for the user."""
        from apps.negotiations.models import NegotiationRoom
        from core.enums import NegotiationStatus

        rooms = NegotiationRoom.objects.filter(
            user_agent__owner=self.user,
            status__in=[
                NegotiationStatus.PENDING,
                NegotiationStatus.IN_PROGRESS,
                NegotiationStatus.AWAITING_APPROVAL,
            ],
        ).values_list("id", flat=True)
        return [str(room_id) for room_id in rooms]

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return timezone.now().isoformat()
