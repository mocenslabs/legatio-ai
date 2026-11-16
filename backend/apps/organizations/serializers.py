"""Serializers for organizations."""

from rest_framework import serializers

from apps.organizations.models import Organization, OrganizationMembership
from core.enums import OrganizationRole


class OrganizationSerializer(serializers.ModelSerializer[Organization]):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "status",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "status", "created_at", "updated_at", "role"]

    def get_role(self, obj: Organization) -> str | None:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None


class OrganizationCreateSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=220, required=False, allow_blank=True)


class MembershipSerializer(serializers.ModelSerializer[OrganizationMembership]):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user_id",
            "email",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "email", "created_at", "updated_at"]


class MembershipAddSerializer(serializers.Serializer[dict[str, object]]):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[
            OrganizationRole.ADMIN,
            OrganizationRole.MEMBER,
            OrganizationRole.VIEWER,
        ],
        default=OrganizationRole.MEMBER,
    )


class MembershipRoleUpdateSerializer(serializers.Serializer[dict[str, object]]):
    role = serializers.ChoiceField(
        choices=[
            OrganizationRole.ADMIN,
            OrganizationRole.MEMBER,
            OrganizationRole.VIEWER,
        ]
    )
