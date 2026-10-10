"""
Integration tests for Negotiation API endpoints.

Source: 05-ROADMAP.md Section 7.3
"""

from typing import TYPE_CHECKING, Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token, register_user
from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from core.enums import AgentType, NegotiationStatus

User = get_user_model()

if TYPE_CHECKING:
    pass


@pytest.fixture
def user() -> Any:
    """Create a test user."""
    return register_user(email="user@example.com", password="pass1234")  # type: ignore[no-any-return]


@pytest.fixture
def user_agent(user: User) -> Agent:
    """Create a user agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="User Agent",
    )


@pytest.fixture
def hotel_agent() -> Agent:
    """Create a simulated hotel agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Hotel Agent",
    )


@pytest.fixture
def active_constitution(user: User, user_agent: Agent) -> Any:
    """Create an active constitution with rules."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
        {
            "rule_number": 17,
            "name": "Never share phone",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "phone_number",
            "action": "DENY",
        },
        {
            "rule_number": 23,
            "name": "Large payments",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Travel Rules",
        description=None,
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db
class TestNegotiationListAPI:
    def test_list_negotiations(
        self, user: User, user_agent: Agent, active_constitution: Constitution
    ) -> None:
        """User can list their negotiations."""
        from apps.negotiations.models import NegotiationRoom

        NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=Agent.objects.create(
                owner=None, agent_type=AgentType.SIMULATED, name="Hotel"
            ),
            constitution=active_constitution,
            reference_code="NEG-TEST-001",
            title="Test",
            user_instruction="Test",
        )

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get("/api/v1/negotiations/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_negotiations_unauthenticated(self) -> None:
        """Unauthenticated users cannot list negotiations."""
        client = APIClient()
        response = client.get("/api/v1/negotiations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestNegotiationCreateAPI:
    def test_create_negotiation(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can create a negotiation."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(hotel_agent.id),
                "constitution_id": str(active_constitution.id),
                "title": "Hotel Madrid",
                "user_instruction": "Find hotel in Madrid",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == NegotiationStatus.PENDING
        assert "NEG-" in response.data["reference_code"]

    def test_create_negotiation_with_same_agents_denied(
        self, user: User, user_agent: Agent, active_constitution: Constitution
    ) -> None:
        """Cannot create negotiation with same user_agent and external_agent."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(user_agent.id),  # Same agent
                "constitution_id": str(active_constitution.id),
                "title": "Test",
                "user_instruction": "Test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestNegotiationStartAPI:
    def test_start_negotiation(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can start a negotiation."""
        from apps.negotiations.models import NegotiationRoom

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=active_constitution,
            reference_code="NEG-TEST-002",
            title="Test",
            user_instruction="Test",
        )

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/negotiations/{room.id}/start/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == NegotiationStatus.IN_PROGRESS


@pytest.mark.django_db
class TestNegotiationProcessRoundAPI:
    def test_process_round(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can process a round of negotiation."""
        from apps.negotiations.models import NegotiationRoom
        from services.negotiation_engine.orchestrator import NegotiationOrchestrator

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=active_constitution,
            reference_code="NEG-TEST-003",
            title="Test",
            user_instruction="Test",
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/negotiations/{room.id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        assert "round_result" in response.data
        assert "proposal" in response.data["round_result"]
        assert "policy_decision" in response.data["round_result"]


@pytest.mark.django_db
class TestNegotiationMessagesAPI:
    def test_list_messages(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can list messages in a negotiation."""
        from apps.negotiations.models import NegotiationRoom
        from services.negotiation_engine.orchestrator import NegotiationOrchestrator

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=active_constitution,
            reference_code="NEG-TEST-004",
            title="Test",
            user_instruction="Test",
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/negotiations/{room.id}/messages/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestNegotiationProposalsAPI:
    def test_list_proposals(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can list proposals in a negotiation."""
        from apps.negotiations.models import NegotiationRoom
        from services.negotiation_engine.orchestrator import NegotiationOrchestrator

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=active_constitution,
            reference_code="NEG-TEST-005",
            title="Test",
            user_instruction="Test",
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/negotiations/{room.id}/proposals/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestNegotiationCancelAPI:
    def test_cancel_negotiation(self, user, user_agent, hotel_agent, active_constitution) -> None:
        """User can cancel a negotiation."""
        from apps.negotiations.models import NegotiationRoom

        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=active_constitution,
            reference_code="NEG-TEST-006",
            title="Test",
            user_instruction="Test",
        )

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/negotiations/{room.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == NegotiationStatus.CANCELLED
