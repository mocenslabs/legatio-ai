"""Billing API — catalog + organization subscription (no payments yet)."""

from typing import Any, cast
from uuid import UUID

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.billing.models import OrganizationSubscription, Plan
from apps.billing.serializers import PlanSerializer, SubscriptionSerializer
from apps.billing.services import ensure_default_plans, start_free_subscription
from apps.organizations.models import Organization, OrganizationMembership


class PlanListView(APIView):
    """GET /api/v1/billing/plans/ — public catalog (auth required for consistency)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        ensure_default_plans()
        qs = Plan.objects.filter(is_active=True, is_public=True).order_by("sort_order")
        return Response(PlanSerializer(qs, many=True).data)


class OrganizationSubscriptionView(APIView):
    """GET /api/v1/billing/organizations/{org_id}/subscription/"""

    permission_classes = [IsAuthenticated]

    def _get_org_for_user(self, org_id: UUID, user: Any) -> Organization | None:
        org = Organization.objects.filter(id=org_id).first()
        if org is None:
            return None
        if getattr(user, "is_staff", False):
            return cast(Organization, org)
        if not OrganizationMembership.objects.filter(
            organization=org, user=cast(User, user)
        ).exists():
            return None
        return cast(Organization, org)

    def get(self, request: Request, org_id: UUID) -> Response:
        org = self._get_org_for_user(org_id, request.user)
        if org is None:
            return Response(
                {"error": {"code": "not_found", "message": "Organization not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        sub = (
            OrganizationSubscription.objects.filter(organization=org).select_related("plan").first()
        )
        if sub is None:
            return Response(
                {
                    "subscription": None,
                    "billing_enabled": bool(getattr(settings, "BILLING_ENABLED", False)),
                }
            )
        return Response(
            {
                "subscription": SubscriptionSerializer(sub).data,
                "billing_enabled": bool(getattr(settings, "BILLING_ENABLED", False)),
            }
        )


class StartFreeSubscriptionView(APIView):
    """POST — attach free/trial plan if the org has no subscription yet."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, org_id: UUID) -> Response:
        org = Organization.objects.filter(id=org_id).first()
        if org is None:
            return Response(
                {"error": {"code": "not_found", "message": "Organization not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        membership = OrganizationMembership.objects.filter(
            organization=org, user=cast(User, request.user)
        ).first()
        if membership is None and not request.user.is_staff:
            return Response(
                {"error": {"code": "forbidden", "message": "Not a member"}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if membership and membership.role not in ("owner", "admin") and not request.user.is_staff:
            return Response(
                {
                    "error": {
                        "code": "forbidden",
                        "message": "Only owner/admin can start subscription",
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        sub = start_free_subscription(org)
        return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)
