"""API tests for billing endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.services import create_organization

User = get_user_model()


@pytest.fixture
def auth_client(db):
    user = User.objects.create_user(email="bill-api@example.com", password="pass12345")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
def test_list_plans(auth_client):
    client, _ = auth_client
    response = client.get("/api/v1/billing/plans/")
    assert response.status_code == 200
    codes = {p["code"] for p in response.data}
    assert "free" in codes


@pytest.mark.django_db
def test_start_free_and_get_subscription(auth_client):
    client, user = auth_client
    org = create_organization(name="API Bill Org", creator=user)
    start = client.post(f"/api/v1/billing/organizations/{org.id}/subscription/start-free/")
    assert start.status_code == 201
    assert start.data["plan"]["code"] == "free"

    got = client.get(f"/api/v1/billing/organizations/{org.id}/subscription/")
    assert got.status_code == 200
    assert got.data["subscription"]["plan"]["code"] == "free"
