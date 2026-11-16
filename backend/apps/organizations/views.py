"""Organization API views."""

from typing import Any, cast
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.serializers import (
    MembershipAddSerializer,
    MembershipRoleUpdateSerializer,
    MembershipSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)
from apps.organizations.services import (
    add_member,
    create_organization,
    remove_member,
    update_member_role,
)
from apps.organizations.services.membership import OrganizationError, OrganizationPermissionError


class OrganizationViewSet(ModelViewSet):  # type: ignore[type-arg]
    """
    Organizations the current user belongs to.

        GET    /api/v1/organizations/
        POST   /api/v1/organizations/
        GET    /api/v1/organizations/{id}/
        PATCH  /api/v1/organizations/{id}/
        DELETE /api/v1/organizations/{id}/  (soft delete, owner only)
        GET    /api/v1/organizations/{id}/members/
        POST   /api/v1/organizations/{id}/members/
        PATCH  /api/v1/organizations/{id}/members/{user_id}/
        DELETE /api/v1/organizations/{id}/members/{user_id}/
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "pk"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self) -> Any:
        user = self.request.user
        if not user.is_authenticated:
            return Organization.objects.none()
        if user.is_staff:
            return Organization.objects.all()
        return Organization.objects.filter(memberships__user=user).distinct()

    def get_serializer_class(self) -> type:
        if self.action == "create":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = self.get_queryset()
        serializer = OrganizationSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        org = self.get_object()
        return Response(OrganizationSerializer(org, context={"request": request}).data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        ser = OrganizationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        org = create_organization(
            name=ser.validated_data["name"],
            slug=ser.validated_data.get("slug") or None,
            creator=request.user,
        )
        return Response(
            OrganizationSerializer(org, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        org = self.get_object()
        membership = OrganizationMembership.objects.filter(
            organization=org, user=cast(User, request.user)
        ).first()
        if membership is None or membership.role not in ("owner", "admin"):
            return Response(
                {"error": {"code": "organization_permission_denied", "message": "Forbidden"}},
                status=status.HTTP_403_FORBIDDEN,
            )
        name = request.data.get("name")
        if name:
            org.name = str(name).strip()
            org.save(update_fields=["name", "updated_at"])
        return Response(OrganizationSerializer(org, context={"request": request}).data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        org = self.get_object()
        membership = OrganizationMembership.objects.filter(
            organization=org, user=cast(User, request.user)
        ).first()
        if membership is None or membership.role != "owner":
            return Response(
                {
                    "error": {
                        "code": "organization_permission_denied",
                        "message": "Only owner can archive",
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        org.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request: Request, pk: UUID | None = None) -> Response:
        org = self.get_object()
        if request.method == "GET":
            qs = OrganizationMembership.objects.filter(organization=org).select_related("user")
            return Response(MembershipSerializer(qs, many=True).data)

        ser = MembershipAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email__iexact=ser.validated_data["email"])
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "No user with that email"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            membership = add_member(
                organization=org,
                user=user,
                role=ser.validated_data["role"],
                invited_by=request.user,
            )
        except (OrganizationError, OrganizationPermissionError) as exc:
            return Response(
                {"error": {"code": exc.code, "message": exc.message}},
                status=exc.default_status,
            )
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"members/(?P<user_id>[0-9a-f-]+)",
    )
    def member_detail(
        self, request: Request, pk: UUID | None = None, user_id: str | None = None
    ) -> Response:
        org = self.get_object()
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "User not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "DELETE":
            try:
                remove_member(organization=org, user=target_user, actor=request.user)
            except (OrganizationError, OrganizationPermissionError) as exc:
                return Response(
                    {"error": {"code": exc.code, "message": exc.message}},
                    status=exc.default_status,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        ser = MembershipRoleUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            membership = update_member_role(
                organization=org,
                user=target_user,
                new_role=ser.validated_data["role"],
                actor=request.user,
            )
        except (OrganizationError, OrganizationPermissionError) as exc:
            return Response(
                {"error": {"code": exc.code, "message": exc.message}},
                status=exc.default_status,
            )
        return Response(MembershipSerializer(membership).data)
