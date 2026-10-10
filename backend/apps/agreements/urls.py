"""
URL configuration for the agreements app.

Source: 05-ROADMAP.md Section 9.5
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.agreements import views

router = DefaultRouter()
router.register(r"agreements", views.AgreementViewSet, basename="agreement")

app_name = "agreements"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "agreements/<uuid:pk>/verify/",
        views.VerifyAgreementView.as_view(),
        name="verify-agreement",
    ),
]
