"""Comment serializers.

This module provides DRF serializers for the Comment model.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.negotiations.models import Comment, CommentEntityType


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model (standard representation).

    The author field is read-only as it is set from the authenticated user.
    """

    is_reply = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "author",
            "content",
            "parent",
            "is_reply",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "is_reply",
            "created_at",
            "updated_at",
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments.

    Validates input for comment creation. The author is set from the
    authenticated user via the service layer.
    """

    class Meta:
        model = Comment
        fields = [
            "entity_type",
            "entity_id",
            "content",
            "parent",
        ]

    def validate_entity_type(self, value: str) -> str:
        """Validate entity_type is a valid choice.

        Args:
            value: The entity_type value to validate.

        Returns:
            The validated entity_type.

        Raises:
            serializers.ValidationError: If entity_type is invalid.
        """
        valid_types = {choice.value for choice in CommentEntityType}
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid entity_type: {value}")
        return value

    def validate_content(self, value: str) -> str:
        """Validate content is not empty.

        Args:
            value: The content value to validate.

        Returns:
            The validated content.

        Raises:
            serializers.ValidationError: If content is empty.
        """
        if not value.strip():
            raise serializers.ValidationError("content cannot be empty.")
        return value
