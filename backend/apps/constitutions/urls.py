"""
URL configuration for the constitutions app.

Source: 05-ROADMAP.md Section 6.5
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.constitutions import views

router = DefaultRouter()
router.register(r"constitutions", views.ConstitutionViewSet, basename="constitution")

# Separate router for rules (since they have nested URLs)
rule_router = DefaultRouter()
rule_router.register(r"rules", views.PolicyRuleViewSet, basename="rule")

app_name = "constitutions"

urlpatterns = [
    # Constitution endpoints
    path("", include(router.urls)),
    # Nested: constitution rules
    path(
        "constitutions/<uuid:constitution_id>/rules/",
        views.PolicyRuleViewSet.as_view({"post": "create"}),
        name="constitution-rules-create",
    ),
    # Standalone rule endpoints
    path("", include(rule_router.urls)),
]
