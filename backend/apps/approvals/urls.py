"""
URL configuration for the approvals app.

Source: 05-ROADMAP.md Section 8.5
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.approvals import views

router = DefaultRouter()
router.register(r"approvals", views.ApprovalRequestViewSet, basename="approval")

app_name = "approvals"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "approvals/<uuid:pk>/approve/",
        views.ApproveView.as_view(),
        name="approve",
    ),
    path(
        "approvals/<uuid:pk>/reject/",
        views.RejectView.as_view(),
        name="reject",
    ),
    path(
        "approvals/<uuid:pk>/modify/",
        views.ModifyView.as_view(),
        name="modify",
    ),
]
