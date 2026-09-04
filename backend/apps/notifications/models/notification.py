"""Notification model definition.

This module defines the Notification model, which represents a notification
delivered to a user about relevant events in the system (approval requests,
proposal status changes, etc.).
"""

from __future__ import annotations

import logging
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class NotificationType(models.TextChoices):
    """Types of notifications."""

    APPROVAL_REQUESTED = "APPROVAL_REQUESTED", _("Approval Requested")
    PROPOSAL_APPROVED = "PROPOSAL_APPROVED", _("Proposal Approved")
    PROPOSAL_DENIED = "PROPOSAL_DENIED", _("Proposal Denied")
    PROPOSAL_EXECUTED = "PROPOSAL_EXECUTED", _("Proposal Executed")
    PROPOSAL_CANCELLED = "PROPOSAL_CANCELLED", _("Proposal Cancelled")
    AGREEMENT_ACTIVATED = "AGREEMENT_ACTIVATED", _("Agreement Activated")
    AGREEMENT_COMPLETED = "AGREEMENT_COMPLETED", _("Agreement Completed")
    AGREEMENT_TERMINATED = "AGREEMENT_TERMINATED", _("Agreement Terminated")
    NEGOTIATION_STARTED = "NEGOTIATION_STARTED", _("Negotiation Started")
    NEGOTIATION_AGREED = "NEGOTIATION_AGREED", _("Negotiation Agreed")
    OFFER_RECEIVED = "OFFER_RECEIVED", _("Offer Received")
    OFFER_ACCEPTED = "OFFER_ACCEPTED", _("Offer Accepted")
    OFFER_REJECTED = "OFFER_REJECTED", _("Offer Rejected")
    COMMENT_ADDED = "COMMENT_ADDED", _("Comment Added")
    SYSTEM = "SYSTEM", _("System")


class NotificationStatus(models.TextChoices):
    """Status lifecycle of a notification."""

    UNREAD = "UNREAD", _("Unread")
    READ = "READ", _("Read")
    ARCHIVED = "ARCHIVED", _("Archived")


class Notification(models.Model):
    """A notification delivered to a user.

    Notifications inform users about relevant events such as pending
    approval requests or changes in proposal status. When created via
    the notify() classmethod, they are also pushed in real-time via
    WebSocket if the channel layer is available.

    Attributes:
        id: UUID primary key.
        notification_type: The category of the notification.
        recipient: The user receiving the notification.
        entity_type: Optional related entity model name.
        entity_id: Optional UUID of the related entity.
        title: Short human-readable title.
        message: Detailed notification message.
        status: Current notification status.
        read_at: Timestamp when the notification was marked as read.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name=_("Notification Type"),
        help_text=_("The category of the notification."),
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Recipient"),
        help_text=_("The user receiving the notification."),
    )
    entity_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Entity Type"),
        help_text=_("Optional related entity model name."),
    )
    entity_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Entity ID"),
        help_text=_("Optional UUID of the related entity."),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Short human-readable title."),
    )
    message = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Message"),
        help_text=_("Detailed notification message."),
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.UNREAD,
        verbose_name=_("Status"),
        help_text=_("Current notification status."),
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read At"),
        help_text=_("Timestamp when the notification was marked as read."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the notification."""
        return f"{self.notification_type} for {self.recipient_id} ({self.status})"

    @property
    def is_read(self) -> bool:
        """Check if the notification has been read.

        Returns:
            True if the notification status is READ or ARCHIVED.
        """
        return bool(self.status != NotificationStatus.UNREAD)

    def mark_as_read(self) -> None:
        """Mark the notification as read.

        Sets the status to READ and records the read timestamp.
        """
        if self.status == NotificationStatus.UNREAD:
            self.status = NotificationStatus.READ
            self.read_at = timezone.now()
            self.save(update_fields=["status", "read_at", "updated_at"])

    def archive(self) -> None:
        """Archive the notification.

        Sets the status to ARCHIVED. Archived notifications are hidden
        from default views but preserved for history.
        """
        if self.status != NotificationStatus.ARCHIVED:
            self.status = NotificationStatus.ARCHIVED
            self.save(update_fields=["status", "updated_at"])

    @classmethod
    def notify(
        cls,
        notification_type: str,
        recipient_id: uuid.UUID,
        title: str,
        message: str = "",
        entity_type: str = "",
        entity_id: uuid.UUID | None = None,
    ) -> Notification:
        """Create a notification for a user and send it in real-time.

        This is the primary method for sending notifications. After
        creating the notification in the database, it sends it to the
        user's WebSocket group for instant delivery.

        Args:
            notification_type: The category of the notification.
            recipient_id: The UUID of the user receiving the notification.
            title: Short human-readable title.
            message: Detailed notification message.
            entity_type: Optional related entity model name.
            entity_id: Optional UUID of the related entity.

        Returns:
            The created Notification instance.
        """
        notification = cls.objects.create(
            notification_type=notification_type,
            recipient_id=recipient_id,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        # Send real-time notification via WebSocket (fail-safe)
        try:
            from apps.notifications.serializers import NotificationSerializer
            from apps.notifications.services.realtime import send_realtime_notification

            serialized_data = NotificationSerializer(notification).data
            send_realtime_notification(
                recipient_id=recipient_id,
                notification_data=serialized_data,
            )
        except Exception as e:
            # Fail-safe: log the error but don't break notification creation
            logger.exception(
                "Failed to send real-time notification %s: %s",
                notification.id,
                str(e),
            )

        return notification
