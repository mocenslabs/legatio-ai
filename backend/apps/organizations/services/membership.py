"""Organization membership business logic."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import transaction

from apps.organizations.models import Organization, OrganizationMembership
from core.enums import OrganizationRole, OrganizationStatus
from core.exceptions import LegatioBaseException


class OrganizationError(LegatioBaseException):
    default_code = "organization_error"
    default_message = "Organization operation failed."
    default_status = 400


class OrganizationPermissionError(OrganizationError):
    default_code = "organization_permission_denied"
    default_message = "You do not have permission for this organization action."
    default_status = 403


def create_organization(
    *,
    name: str,
    creator: Any,
    slug: str | None = None,
) -> Organization:
    """Create an organization and assign the creator as OWNER."""
    with transaction.atomic():
        org = Organization(
            name=name.strip(),
            status=OrganizationStatus.ACTIVE,
            created_by=creator,
        )
        cleaned_slug = (slug or "").strip()
        if cleaned_slug:
            org.slug = cleaned_slug
        org.save()
        OrganizationMembership.objects.create(
            organization=org,
            user=creator,
            role=OrganizationRole.OWNER,
            invited_by=None,
        )
    return org


def get_user_role(organization: Organization, user: Any) -> str | None:
    membership = (
        OrganizationMembership.objects.filter(organization=organization, user=user)
        .values_list("role", flat=True)
        .first()
    )
    return membership


def list_user_organizations(user: Any) -> list[Organization]:
    return list(Organization.objects.filter(memberships__user=user).distinct().order_by("name"))


def _require_manager(organization: Organization, actor: Any) -> OrganizationMembership:
    membership = OrganizationMembership.objects.filter(
        organization=organization, user=actor
    ).first()
    if membership is None or not membership.can_manage_members:
        raise OrganizationPermissionError("Only owners and admins can manage organization members.")
    return membership


def add_member(
    *,
    organization: Organization,
    user: Any,
    role: str = OrganizationRole.MEMBER,
    invited_by: Any,
) -> OrganizationMembership:
    if role == OrganizationRole.OWNER:
        raise OrganizationError(
            "Cannot assign OWNER via add_member; transfer ownership separately."
        )
    _require_manager(organization, invited_by)
    membership, created = OrganizationMembership.objects.get_or_create(
        organization=organization,
        user=user,
        defaults={"role": role, "invited_by": invited_by},
    )
    if not created:
        raise OrganizationError("User is already a member of this organization.")
    return membership


def update_member_role(
    *,
    organization: Organization,
    user: Any,
    new_role: str,
    actor: Any,
) -> OrganizationMembership:
    actor_membership = _require_manager(organization, actor)
    target = OrganizationMembership.objects.filter(organization=organization, user=user).first()
    if target is None:
        raise OrganizationError("User is not a member of this organization.")
    if target.role == OrganizationRole.OWNER:
        raise OrganizationError("Cannot change the role of the organization owner.")
    if new_role == OrganizationRole.OWNER and actor_membership.role != OrganizationRole.OWNER:
        raise OrganizationPermissionError("Only the owner can grant OWNER role.")
    target.role = new_role
    target.save(update_fields=["role", "updated_at"])
    return target


def remove_member(
    *,
    organization: Organization,
    user: Any,
    actor: Any,
) -> None:
    _require_manager(organization, actor)
    target = OrganizationMembership.objects.filter(organization=organization, user=user).first()
    if target is None:
        raise OrganizationError("User is not a member of this organization.")
    if target.role == OrganizationRole.OWNER:
        raise OrganizationError("Cannot remove the organization owner.")
    target.delete()


def user_in_organization(user: Any, organization_id: UUID) -> bool:
    return OrganizationMembership.objects.filter(
        organization_id=organization_id, user=user
    ).exists()
