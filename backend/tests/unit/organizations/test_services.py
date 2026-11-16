"""Unit tests for organization services."""

import pytest
from django.contrib.auth import get_user_model

from apps.organizations.services import (
    add_member,
    create_organization,
    get_user_role,
    list_user_organizations,
    remove_member,
    update_member_role,
)
from apps.organizations.services.membership import (
    OrganizationError,
    OrganizationPermissionError,
)
from core.enums import OrganizationRole

User = get_user_model()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(email="owner@example.com", password="pass12345")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(email="member@example.com", password="pass12345")


@pytest.mark.django_db
def test_create_organization_assigns_owner(user_a):
    org = create_organization(name="Acme Corp", creator=user_a)
    assert org.slug.startswith("acme")
    assert get_user_role(org, user_a) == OrganizationRole.OWNER
    assert org in list_user_organizations(user_a)


@pytest.mark.django_db
def test_add_member_and_permissions(user_a, user_b):
    org = create_organization(name="Beta Inc", creator=user_a)
    membership = add_member(
        organization=org,
        user=user_b,
        role=OrganizationRole.MEMBER,
        invited_by=user_a,
    )
    assert membership.role == OrganizationRole.MEMBER
    with pytest.raises(OrganizationPermissionError):
        add_member(
            organization=org,
            user=user_a,
            role=OrganizationRole.VIEWER,
            invited_by=user_b,
        )


@pytest.mark.django_db
def test_cannot_remove_owner(user_a, user_b):
    org = create_organization(name="Gamma LLC", creator=user_a)
    add_member(
        organization=org,
        user=user_b,
        role=OrganizationRole.ADMIN,
        invited_by=user_a,
    )
    with pytest.raises(OrganizationError):
        remove_member(organization=org, user=user_a, actor=user_b)


@pytest.mark.django_db
def test_update_member_role(user_a, user_b):
    org = create_organization(name="Delta SA", creator=user_a)
    add_member(
        organization=org,
        user=user_b,
        role=OrganizationRole.MEMBER,
        invited_by=user_a,
    )
    m = update_member_role(
        organization=org,
        user=user_b,
        new_role=OrganizationRole.ADMIN,
        actor=user_a,
    )
    assert m.role == OrganizationRole.ADMIN
