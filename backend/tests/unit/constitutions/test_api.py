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
        Constitution.objects.create(name="Constitution 1")
        Constitution.objects.create(name="Constitution 2")
        url = reverse("constitution-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_create_constitution(self, api_client: APIClient) -> None:
        url = reverse("constitution-list")
        data = {"name": "New Constitution", "description": "A new constitution", "is_active": True}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Constitution"

    def test_retrieve_constitution(self, api_client: APIClient) -> None:
        constitution = Constitution.objects.create(name="Test Constitution")
        url = reverse("constitution-detail", kwargs={"pk": constitution.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Constitution"

    def test_update_constitution(self, api_client: APIClient) -> None:
        constitution = Constitution.objects.create(name="Original Name")
        url = reverse("constitution-detail", kwargs={"pk": constitution.id})
        data = {"name": "Updated Name", "description": "Updated description"}
        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete_constitution(self, api_client: APIClient) -> None:
        constitution = Constitution.objects.create(name="To Delete")
        url = reverse("constitution-detail", kwargs={"pk": constitution.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Constitution.objects.filter(id=constitution.id).exists()

    def test_filter_by_is_active(self, api_client: APIClient) -> None:
        Constitution.objects.create(name="Active", is_active=True)
        Constitution.objects.create(name="Inactive", is_active=False)
        url = reverse("constitution-list")
        response = api_client.get(url, {"is_active": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Active"
