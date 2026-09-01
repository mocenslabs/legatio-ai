"""AuditLog API views.

This module provides DRF ViewSets for AuditLog model operations.
Audit logs are read-only via API (append-only by design).
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog model (read-only).

    Provides list and retrieve operations. Audit logs are append-only
    and managed exclusively by the service layer.

    Permissions:
        - IsAuthenticated: All operations require authentication.

    Filters:
        - entity_type: Filter by entity type (query param: ?entity_type=Proposal)
        - entity_id: Filter by entity ID (query param: ?entity_id=<uuid>)
        - action: Filter by action (query param: ?action=PROPOSAL_APPROVED)
        - actor: Filter by actor ID (query param: ?actor=<uuid>)
    """

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[AuditLog]:
        """Filter queryset based on query parameters.

        Returns:
            Filtered queryset of AuditLog objects.
        """
        queryset = super().get_queryset()

        # Filter by entity_type
        entity_type = self.request.query_params.get("entity_type")
        if entity_type is not None:
            queryset = queryset.filter(entity_type=entity_type)

        # Filter by entity_id
        entity_id = self.request.query_params.get("entity_id")
        if entity_id is not None:
            queryset = queryset.filter(entity_id=entity_id)

        # Filter by action
        action = self.request.query_params.get("action")
        if action is not None:
            queryset = queryset.filter(action=action)

        # Filter by actor
        actor = self.request.query_params.get("actor")
        if actor is not None:
            queryset = queryset.filter(actor_id=actor)

        return queryset
