"""API tests for AuditLog endpoints.

Tests cover list, retrieve, filtering, and access restrictions.
Audit logs are read-only via API.
"""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditAction, AuditLog


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="viewer@example.com", password="testpass123")


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
class TestAuditLogAPI:
    """Tests for AuditLog API endpoints."""

    def test_list_audit_logs(self, api_client: APIClient) -> None:
        """Verify listing audit logs returns paginated results."""
        entity_id = uuid.uuid4()
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=entity_id,
        )
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_SUBMITTED,
            entity_type="Proposal",
            entity_id=entity_id,
        )

        url = reverse("auditlog-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_audit_log(self, api_client: APIClient) -> None:
        """Verify retrieving a single audit log works."""
        audit_log = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        url = reverse("auditlog-detail", kwargs={"pk": audit_log.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["action"] == AuditAction.PROPOSAL_CREATED
        assert response.data["entity_type"] == "Proposal"

    def test_filter_by_entity_type(self, api_client: APIClient) -> None:
        """Verify filtering audit logs by entity_type works."""
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )
        AuditLog.objects.create(
            action=AuditAction.APPROVAL_REQUESTED,
            entity_type="ApprovalRequest",
            entity_id=uuid.uuid4(),
        )

        url = reverse("auditlog-list")
        response = api_client.get(url, {"entity_type": "Proposal"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["entity_type"] == "Proposal"

    def test_filter_by_action(self, api_client: APIClient) -> None:
        """Verify filtering audit logs by action works."""
        entity_id = uuid.uuid4()
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=entity_id,
        )
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_APPROVED,
            entity_type="Proposal",
            entity_id=entity_id,
        )

        url = reverse("auditlog-list")
        response = api_client.get(url, {"action": AuditAction.PROPOSAL_APPROVED})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["action"] == AuditAction.PROPOSAL_APPROVED

    def test_filter_by_actor(self, api_client: APIClient, user: User) -> None:
        """Verify filtering audit logs by actor works."""
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
            actor=user,
        )
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_SUBMITTED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        url = reverse("auditlog-list")
        response = api_client.get(url, {"actor": str(user.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["actor"] == user.id

    def test_create_not_allowed(self, api_client: APIClient) -> None:
        """Verify creating audit logs via API returns 405."""
        url = reverse("auditlog-list")
        data = {
            "action": AuditAction.PROPOSAL_CREATED,
            "entity_type": "Proposal",
            "entity_id": str(uuid.uuid4()),
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, api_client: APIClient) -> None:
        """Verify deleting audit logs via API returns 405."""
        audit_log = AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        url = reverse("auditlog-detail", kwargs={"pk": audit_log.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_unauthenticated_returns_401(self) -> None:
        """Verify unauthenticated requests return 401."""
        AuditLog.objects.create(
            action=AuditAction.PROPOSAL_CREATED,
            entity_type="Proposal",
            entity_id=uuid.uuid4(),
        )

        client = APIClient()
        url = reverse("auditlog-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
