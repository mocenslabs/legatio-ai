"""Constitution API views."""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.constitutions.models import Constitution
from apps.constitutions.serializers import ConstitutionSerializer


class ConstitutionViewSet(viewsets.ModelViewSet):
    """ViewSet for Constitution model."""

    queryset = Constitution.objects.all()
    serializer_class = ConstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Constitution]:
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset
