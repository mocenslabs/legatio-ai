"""Comment Service layer.

This module provides a service for managing comments on proposals,
agreements, and negotiations, with audit logging and notifications.
"""

from __future__ import annotations

import uuid

from django.db import transaction

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.negotiations.models import Comment, CommentEntityType
from apps.notifications.models import NotificationType
from apps.notifications.services import NotificationService


class CommentServiceError(Exception):
    """Base exception for comment service errors."""


class CommentService:
    """Service layer for comment operations.

    Manages comment creation and deletion across proposals, agreements,
    and negotiations, recording audit events and sending notifications.
    """

    @staticmethod
    @transaction.atomic
    def add_comment(
        entity_type: str,
        entity_id: uuid.UUID,
        author_id: uuid.UUID,
        content: str,
        parent_id: uuid.UUID | None = None,
    ) -> Comment:
        """Add a comment to an entity.

        Args:
            entity_type: The type of entity (Proposal, Agreement, Negotiation).
            entity_id: The UUID of the entity being commented on.
            author_id: The UUID of the comment author.
            content: The comment text.
            parent_id: Optional UUID of the parent comment for replies.

        Returns:
            The created Comment instance.

        Raises:
            CommentServiceError: If entity_type is invalid or parent not found.
        """
        # Validate entity_type
        valid_types = {choice.value for choice in CommentEntityType}
        if entity_type not in valid_types:
            raise CommentServiceError(f"Invalid entity_type: {entity_type}")

        # Validate parent exists if provided
        parent = None
        if parent_id is not None:
            try:
                parent = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist as e:
                raise CommentServiceError(f"Parent comment {parent_id} not found") from e

        comment = Comment.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            content=content,
            parent=parent,
        )

        AuditService.log_comment_event(
            action=AuditAction.COMMENT_ADDED,
            comment_id=comment.id,
            actor_id=author_id,
            new_state={"entity_type": entity_type, "content_length": len(content)},
            metadata={
                "entity_id": str(entity_id),
                "parent_id": str(parent_id) if parent_id else None,
            },
        )

        # Notify the entity owner about the new comment (Proposal only for now)
        CommentService._notify_comment(entity_type, entity_id, comment)

        return comment

    @staticmethod
    def _notify_comment(entity_type: str, entity_id: uuid.UUID, comment: Comment) -> None:
        """Notify the entity owner about a new comment.

        Currently supports Proposal entities. Extend for other entity
        types as needed.

        Args:
            entity_type: The type of entity commented on.
            entity_id: The UUID of the entity.
            comment: The created comment.
        """
        if entity_type != CommentEntityType.PROPOSAL:
            return

        from apps.proposals.models import Proposal

        try:
            proposal = Proposal.objects.get(id=entity_id)
        except Proposal.DoesNotExist:
            return

        # Don't notify the author about their own comment
        if proposal.created_by_id == comment.author_id:
            return

        NotificationService.notify_proposal_status(
            proposal_id=proposal.id,
            recipient_id=proposal.created_by_id,
            notification_type=NotificationType.COMMENT_ADDED,
            title=f"New comment on: {proposal.title}",
            message=f"A new comment was added to your proposal '{proposal.title}'.",
        )

    @staticmethod
    @transaction.atomic
    def delete_comment(
        comment_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """Delete a comment.

        Only the comment author can delete it.

        Args:
            comment_id: The UUID of the comment to delete.
            actor_id: The UUID of the user deleting the comment.

        Raises:
            CommentServiceError: If the comment doesn't exist or actor is not the author.
        """
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist as e:
            raise CommentServiceError(f"Comment {comment_id} not found") from e

        if comment.author_id != actor_id:
            raise CommentServiceError("Only the author can delete a comment")

        entity_type = comment.entity_type
        entity_id = comment.entity_id

        comment.delete()

        AuditService.log_comment_event(
            action=AuditAction.COMMENT_DELETED,
            comment_id=comment_id,
            actor_id=actor_id,
            old_state={"entity_type": entity_type},
            metadata={"entity_id": str(entity_id)},
        )
