"""
URL configuration for the audit app.

Source: 05-ROADMAP.md Section 9.5
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.audit import views

router = DefaultRouter()
router.register(r"events", views.AuditEventViewSet, basename="audit-event")

app_name = "audit"

urlpatterns = [
    # Audit event endpoints
    path("", include(router.urls)),
    # Entity audit trail
    path(
        "entities/<str:entity_type>/<uuid:entity_id>/",
        views.EntityAuditTrailView.as_view(),
        name="entity-audit-trail",
    ),
    # Verify full chain
    path(
        "verify/",
        views.VerifyAuditChainView.as_view(),
        name="verify-chain",
    ),
    # Verify entity audit trail
    path(
        "entities/<str:entity_type>/<uuid:entity_id>/verify/",
        views.VerifyEntityAuditView.as_view(),
        name="verify-entity-audit",
    ),
]
