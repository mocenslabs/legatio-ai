"""
Integration tests for audit API endpoints.

Source: 05-ROADMAP.md Section 9.5
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token
from apps.audit.services import create_audit_event
from core.enums import ActorType, EventType

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(email="audit_api@example.com", password="pass1234")


def _extract_results(response):
    """Handle both paginated and non-paginated responses."""
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data


@pytest.mark.django_db
class TestAuditEventListAPI:
    def test_list_events(self, user) -> None:
        """User can list their audit events."""
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get("/api/v1/audit/events/")
        assert response.status_code == status.HTTP_200_OK
        results = _extract_results(response)
        assert len(results) >= 3

    def test_list_events_unauthenticated(self) -> None:
        """Unauthenticated users cannot list events."""
        client = APIClient()
        response = client.get("/api/v1/audit/events/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAuditEventRetrieveAPI:
    def test_retrieve_event(self, user) -> None:
        """User can retrieve a specific audit event."""
        event = create_audit_event(
            event_type=EventType.USER_REGISTERED,
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="User",
            entity_id=user.id,
        )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/audit/events/{event.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(event.id)


@pytest.mark.django_db
class TestEntityAuditTrailAPI:
    def test_get_entity_trail(self, user) -> None:
        """User can get audit trail for an entity."""
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/audit/entities/User/{user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3


@pytest.mark.django_db
class TestVerifyAuditChainAPI:
    def test_verify_full_chain(self, user) -> None:
        """User can verify the full audit chain."""
        for _ in range(5):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post("/api/v1/audit/verify/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["chain_is_valid"] is True
        assert response.data["total_events"] >= 5

    def test_verify_chain_range(self, user) -> None:
        """User can verify a specific range."""
        for _ in range(10):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(
            "/api/v1/audit/verify/",
            {"start_sequence": 1, "end_sequence": 5},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_verify_invalid_range_params(self, user) -> None:
        """Providing only start_sequence without end_sequence fails."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(
            "/api/v1/audit/verify/",
            {"start_sequence": 1},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVerifyEntityAuditAPI:
    def test_verify_entity_audit(self, user) -> None:
        """User can verify audit trail for an entity."""
        for _ in range(3):
            create_audit_event(
                event_type=EventType.USER_REGISTERED,
                actor_type=ActorType.USER,
                actor_id=user.id,
                entity_type="User",
                entity_id=user.id,
            )
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/audit/entities/User/{user.id}/verify/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["chain_is_valid"] is True
