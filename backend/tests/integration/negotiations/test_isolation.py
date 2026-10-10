"""
Integration tests for Negotiation API isolation.

Verifies that users cannot access negotiations of other users.

Source: 00-INDEX.md Section 2.5
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
from apps.negotiations.models import NegotiationRoom
from core.enums import AgentType, NegotiationStatus

User = get_user_model()

if TYPE_CHECKING:
    pass


@pytest.fixture
def alice() -> Any:
    """Create Alice."""
    return register_user(email="alice@example.com", password="pass1234")  # type: ignore[no-any-return]


@pytest.fixture
def bob() -> Any:
    """Create Bob."""
    return register_user(email="bob@example.com", password="pass1234")  # type: ignore[no-any-return]


@pytest.fixture
def alice_agent(alice: User) -> Agent:
    """Create Alice's agent."""
    return Agent.objects.create(
        owner=alice,
        agent_type=AgentType.USER_AGENT,
        name="Alice Agent",
    )


@pytest.fixture
def bob_agent(bob: User) -> Agent:
    """Create Bob's agent."""
    return Agent.objects.create(
        owner=bob,
        agent_type=AgentType.USER_AGENT,
        name="Bob Agent",
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
def alice_constitution(alice: User, alice_agent: Agent) -> Any:
    """Create Alice's active constitution."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max amount",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=alice_agent,
        name="Alice Rules",
        description=None,
        rules=rules,
        user=alice,
    )
    activate_version(version=version, user=alice)
    return constitution


@pytest.fixture
def bob_constitution(bob: User, bob_agent: Agent) -> Any:
    """Create Bob's active constitution."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max amount",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 500,
            "action": "ALLOW",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=bob_agent,
        name="Bob Rules",
        description=None,
        rules=rules,
        user=bob,
    )
    activate_version(version=version, user=bob)
    return constitution


@pytest.mark.django_db
class TestNegotiationIsolation:
    def test_alice_cannot_see_bob_negotiations(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot list Bob's negotiations."""
        # Bob creates a negotiation
        NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-001",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        # Alice tries to list
        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get("/api/v1/negotiations/")
        assert response.status_code == status.HTTP_200_OK
        # Alice should see 0 negotiations
        # DRF pagination returns dict with 'results' key
        results = response.data.get("results", response.data)
        if isinstance(results, list):
            assert len(results) == 0
        else:
            assert len(response.data) == 0

    def test_alice_cannot_retrieve_bob_negotiation(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot retrieve Bob's negotiation."""
        bob_room = NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-002",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/negotiations/{bob_room.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_start_bob_negotiation(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot start Bob's negotiation."""
        bob_room = NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-003",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/negotiations/{bob_room.id}/start/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_cancel_bob_negotiation(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot cancel Bob's negotiation."""
        bob_room = NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-004",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(f"/api/v1/negotiations/{bob_room.id}/cancel/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        bob_room.refresh_from_db()
        assert bob_room.status != NegotiationStatus.CANCELLED

    def test_alice_cannot_see_bob_messages(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot see messages in Bob's negotiation."""
        bob_room = NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-005",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/negotiations/{bob_room.id}/messages/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_see_bob_proposals(
        self,
        alice: User,
        bob: User,
        alice_agent: Agent,
        bob_agent: Agent,
        hotel_agent: Agent,
        bob_constitution: Constitution,
    ) -> None:
        """Alice cannot see proposals in Bob's negotiation."""
        bob_room = NegotiationRoom.objects.create(
            user_agent=bob_agent,
            external_agent=hotel_agent,
            constitution=bob_constitution,
            reference_code="NEG-BOB-006",
            title="Bob's Negotiation",
            user_instruction="Test",
        )

        token = generate_access_token(alice)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get(f"/api/v1/negotiations/{bob_room.id}/proposals/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
