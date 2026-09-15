"""Integration tests for constitution API endpoints."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.constitutions.models import Constitution


@pytest.fixture
def api_client() -> APIClient:
    user = User.objects.create_user(email="test@example.com", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestConstitutionAPI:
    def test_list_constitutions(self, api_client: APIClient) -> None:
        user = api_client.handler._force_user  # type: ignore
        Constitution.objects.create(user=user, name="Constitution 1")
        Constitution.objects.create(user=user, name="Constitution 2")

        # Create another user's constitution (should not appear)
        other_user = User.objects.create_user(email="other@example.com", password="pass")
        Constitution.objects.create(user=other_user, name="Other Constitution")

        url = reverse("constitutions:constitution-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_create_constitution(self, api_client: APIClient) -> None:
        url = reverse("constitutions:constitution-list")
        data = {
            "name": "New Constitution",
            "description": "A new constitution",
            "is_active": True,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Constitution"

        # Verify it was assigned to the user
        user = api_client.handler._force_user  # type: ignore
        assert Constitution.objects.filter(user=user, name="New Constitution").exists()

    def test_retrieve_constitution(self, api_client: APIClient) -> None:
        user = api_client.handler._force_user  # type: ignore
        constitution = Constitution.objects.create(user=user, name="Test Constitution")

        url = reverse("constitutions:constitution-detail", kwargs={"pk": constitution.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Constitution"

    def test_update_constitution(self, api_client: APIClient) -> None:
        user = api_client.handler._force_user  # type: ignore
        constitution = Constitution.objects.create(user=user, name="Original Name")

        url = reverse("constitutions:constitution-detail", kwargs={"pk": constitution.id})
        data = {"name": "Updated Name", "description": "Updated description"}

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete_constitution(self, api_client: APIClient) -> None:
        user = api_client.handler._force_user  # type: ignore
        constitution = Constitution.objects.create(user=user, name="To Delete")

        url = reverse("constitutions:constitution-detail", kwargs={"pk": constitution.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Constitution.objects.filter(id=constitution.id).exists()

    def test_filter_by_is_active(self, api_client: APIClient) -> None:
        user = api_client.handler._force_user  # type: ignore
        Constitution.objects.create(user=user, name="Active", is_active=True)
        Constitution.objects.create(user=user, name="Inactive", is_active=False)

        url = reverse("constitutions:constitution-list")
        response = api_client.get(url, {"is_active": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Active"
