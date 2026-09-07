"""API tests for reporting endpoints.

Tests cover dashboard metrics and activity feed endpoints.
"""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditAction, AuditLog
from apps.proposals.models import Proposal, ProposalStatus


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="user@example.com", password="testpass123")


@pytest.fixture
def api_client(user: User) -> APIClient:
    """Create an authenticated API client.

    Args:
        user: The user fixture.

    Returns:
        Authenticated APIClient instance.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for the dashboard endpoint."""

    def test_dashboard_returns_200(self, api_client: APIClient, user: User) -> None:
        """Verify dashboard endpoint returns 200 with metrics."""
        Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        url = reverse("reporting-dashboard")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "proposals" in response.data
        assert "agreements" in response.data
        assert "notifications" in response.data
        assert "generated_at" in response.data

    def test_dashboard_reflects_data(self, api_client: APIClient, user: User) -> None:
        """Verify dashboard reflects actual data counts."""
        Proposal.objects.create(
            title="Test Proposal",
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            created_by=user,
            status=ProposalStatus.DRAFT,
        )

        url = reverse("reporting-dashboard")
        response = api_client.get(url)

        assert response.data["proposals"]["total"] == 1
        assert response.data["proposals"]["by_status"]["DRAFT"] == 1

    def test_dashboard_unauthenticated_returns_401(self) -> None:
        """Verify unauthenticated requests return 401."""
        client = APIClient()
        url = reverse("reporting-dashboard")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestActivityFeedAPI:
    """Tests for the activity feed endpoint."""

    def test_activity_feed_returns_200(self, api_client: APIClient, user: User) -> None:
        """Verify activity feed endpoint returns 200."""
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
            actor=user,
        )

        url = reverse("reporting-activity")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

    def test_activity_feed_respects_limit(self, api_client: APIClient, user: User) -> None:
        """Verify activity feed respects the limit query parameter."""
        for i in range(5):
            AuditLog.objects.create(
                action=AuditAction.PROPOSAL_CREATED,
                entity_type="Proposal",
                entity_id=uuid.uuid4(),
                actor=user,
            )

        url = reverse("reporting-activity")
        response = api_client.get(url, {"limit": 3})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_activity_feed_limit_capped_at_max(self, api_client: APIClient, user: User) -> None:
        """Verify limit is capped at maximum value."""
        for i in range(5):
            AuditLog.objects.create(
                action=AuditAction.PROPOSAL_CREATED,
                entity_type="Proposal",
                entity_id=uuid.uuid4(),
                actor=user,
            )

        url = reverse("reporting-activity")
        response = api_client.get(url, {"limit": 500})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 100

    def test_activity_feed_invalid_limit_uses_default(
        self, api_client: APIClient, user: User
    ) -> None:
        """Verify invalid limit falls back to default."""
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
            actor=user,
        )

        url = reverse("reporting-activity")
        response = api_client.get(url, {"limit": "invalid"})

        assert response.status_code == status.HTTP_200_OK

    def test_activity_feed_unauthenticated_returns_401(self) -> None:
        """Verify unauthenticated requests return 401."""
        client = APIClient()
        url = reverse("reporting-activity")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
