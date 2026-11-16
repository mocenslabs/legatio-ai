"""API tests for organizations."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.services import create_organization
from core.enums import OrganizationRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="api-owner@example.com", password="pass12345")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_create_and_list_organizations(auth_client, user):
    response = auth_client.post(
        "/api/v1/organizations/",
        {"name": "Nova Org"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "Nova Org"
    assert response.data["role"] == OrganizationRole.OWNER

    listed = auth_client.get("/api/v1/organizations/")
    assert listed.status_code == 200
    assert any(item["name"] == "Nova Org" for item in listed.data)


@pytest.mark.django_db
def test_members_endpoint(auth_client, user, db):
    org = create_organization(name="Members Org", creator=user)
    other = User.objects.create_user(email="invitee@example.com", password="pass12345")
    response = auth_client.post(
        f"/api/v1/organizations/{org.id}/members/",
        {"email": other.email, "role": OrganizationRole.MEMBER},
        format="json",
    )
    assert response.status_code == 201
    members = auth_client.get(f"/api/v1/organizations/{org.id}/members/")
    assert members.status_code == 200
    emails = {m["email"] for m in members.data}
    assert user.email in emails
    assert other.email in emails
