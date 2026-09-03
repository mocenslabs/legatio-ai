"""Comment API views.

This module provides DRF ViewSets for Comment model operations.
Comments are created and deleted via the service layer.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.negotiations.models import Comment
from apps.negotiations.serializers import CommentCreateSerializer, CommentSerializer
from apps.negotiations.services import CommentService, CommentServiceError


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment model.

    Provides list, retrieve, create, and delete operations. Updates are
    not supported; comments are immutable once created.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - entity_type: Filter by entity type (query param: ?entity_type=Proposal)
        - entity_id: Filter by entity ID (query param: ?entity_id=<uuid>)
        - author: Filter by author ID (query param: ?author=<uuid>)
    """

    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Return the appropriate serializer based on action.

        Returns:
            The serializer class for the current action.
        """
        if self.action == "create":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self) -> QuerySet[Comment]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of Comment objects.
        """
        queryset = super().get_queryset()

        entity_type = self.request.query_params.get("entity_type")
        if entity_type is not None:
            queryset = queryset.filter(entity_type=entity_type)

        entity_id = self.request.query_params.get("entity_id")
        if entity_id is not None:
            queryset = queryset.filter(entity_id=entity_id)

        author = self.request.query_params.get("author")
        if author is not None:
            queryset = queryset.filter(author_id=author)

        return queryset

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new comment via the service layer.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with the created comment.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        parent = validated.get("parent")
        parent_id = parent.id if parent is not None else None

        try:
            comment = CommentService.add_comment(
                entity_type=validated["entity_type"],
                entity_id=validated["entity_id"],
                author_id=cast(uuid.UUID, request.user.id),
                content=validated["content"],
                parent_id=parent_id,
            )
        except CommentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = CommentSerializer(comment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a comment via the service layer.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with 204 on success or 400 on error.
        """
        comment = self.get_object()
        try:
            CommentService.delete_comment(
                comment_id=comment.id,
                actor_id=cast(uuid.UUID, request.user.id),
            )
        except CommentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
