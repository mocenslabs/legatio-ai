"""Comment model definition.

This module defines the Comment model, which provides generic discussion
capabilities for any entity in the system (proposals, agreements,
negotiations) using a polymorphic reference pattern.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class CommentEntityType(models.TextChoices):
    """Types of entities that can receive comments."""

    PROPOSAL = "Proposal", _("Proposal")
    AGREEMENT = "Agreement", _("Agreement")
    NEGOTIATION = "Negotiation", _("Negotiation")


class Comment(models.Model):
    """A comment on a proposal, agreement, or negotiation.

    Uses a polymorphic reference (entity_type + entity_id) so a single
    model supports discussion across multiple entity types. Supports
    threaded replies via the self-referential parent field.

    Attributes:
        id: UUID primary key.
        entity_type: The type of entity being commented on.
        entity_id: The UUID of the entity being commented on.
        author: The user who wrote the comment.
        content: The comment text.
        parent: Optional parent comment for threaded replies.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    entity_type = models.CharField(
        max_length=50,
        choices=CommentEntityType.choices,
        verbose_name=_("Entity Type"),
        help_text=_("The type of entity being commented on."),
    )
    entity_id = models.UUIDField(
        verbose_name=_("Entity ID"),
        help_text=_("The UUID of the entity being commented on."),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Author"),
        help_text=_("The user who wrote the comment."),
    )
    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("The comment text."),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Parent"),
        help_text=_("Optional parent comment for threaded replies."),
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
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the comment."""
        author_name = self.author.email if self.author else "Unknown"
        return f"Comment by {author_name} on {self.entity_type} ({self.id})"

    @property
    def is_reply(self) -> bool:
        """Check if this comment is a reply to another comment.

        Returns:
            True if the comment has a parent.
        """
        return bool(self.parent is not None)
