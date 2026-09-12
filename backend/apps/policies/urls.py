"""Policies API URLs."""
from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.policies.views import PolicyEvaluationView, PolicyRuleViewSet

router = DefaultRouter()
# Ruteo plano (Pragmático). Se filtra por ?constitution_id=X si se desea.
router.register(r"rules", PolicyRuleViewSet, basename="policyrule")

urlpatterns = [
    path("", include(router.urls)),
    # Alineado con la idea de evaluar políticas
    path("evaluate/", PolicyEvaluationView.as_view(), name="policy-evaluate"),
]
