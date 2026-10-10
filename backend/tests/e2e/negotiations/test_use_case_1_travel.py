"""
End-to-end test for Use Case 1: AI Travel Negotiation via API.

This test reproduces the complete flow from 04-BUSINESS-FLOW.md Section 4:
"Find me a hotel in Madrid for 5 nights. Don't spend more than €700
and never share my phone number."

The test verifies the full flow via REST API:
  Round 1: €820, no phone → REQUIRE_APPROVAL
  Round 2: €680, with phone → DENY (Rule #17)
  Round 3: €700, no phone → REQUIRE_APPROVAL

Source: 05-ROADMAP.md Section 7.3 (Deliverable 3.13)
Source: 04-BUSINESS-FLOW.md Section 4.2
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token, register_user
from apps.agents.models import Agent
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision
from core.enums import (
    AgentType,
    NegotiationStatus,
    PolicyDecisionOutcome,
)

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return register_user(email="travel@example.com", password="travel1234")


@pytest.fixture
def user_agent(user):
    """Create the user's travel agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="My Travel Agent",
    )


@pytest.fixture
def hotel_agent():
    """Create the simulated hotel agent."""
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Hotel Agent",
    )


@pytest.fixture
def madrid_constitution(user, user_agent):
    """Create the Madrid travel constitution from 04-BUSINESS-FLOW.md Section 4.1."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction amount",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 700,
            "action": "ALLOW",
        },
        {
            "rule_number": 17,
            "name": "Never share phone number",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "phone_number",
            "action": "DENY",
        },
        {
            "rule_number": 23,
            "name": "Large payments need approval",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
        },
        {
            "rule_number": 31,
            "name": "Email sharing allowed",
            "category": "PRIVACY",
            "field": "data_fields_requested",
            "operator": "CONTAINS",
            "value": "email",
            "action": "ALLOW",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Madrid Travel Rules",
        description="Rules for hotel booking in Madrid",
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db
class TestUseCase1TravelNegotiationViaAPI:
    """
    Full scenario from 04-BUSINESS-FLOW.md Section 4.2, executed via REST API.
    """

    def test_full_negotiation_flow_via_api(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        """
        Complete flow via API:
        1. Create negotiation room
        2. Start negotiation
        3. Process round 1: €820, no phone → REQUIRE_APPROVAL
        4. Process round 2: €680, with phone → DENY
        5. Process round 3: €700, no phone → REQUIRE_APPROVAL
        6. Verify final state
        """
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 1. Create negotiation room
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(hotel_agent.id),
                "constitution_id": str(madrid_constitution.id),
                "title": "Hotel Madrid 5 nights",
                "user_instruction": "Find hotel in Madrid for 5 nights. Max €700. Never share phone.",
                "max_rounds": 10,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]
        assert response.data["status"] == NegotiationStatus.PENDING

        # 2. Start negotiation
        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == NegotiationStatus.IN_PROGRESS

        # 3. Process round 1: €820, no phone → REQUIRE_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round1 = response.data["round_result"]
        assert round1["proposal"]["amount"] == "820.00"
        assert round1["proposal"]["data_fields_requested"] == []
        assert round1["outcome"] == "REQUIRE_HUMAN_APPROVAL"
        assert round1["policy_decision"]["outcome"] == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

        # 4. Process round 2: €680, with phone → DENY
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round2 = response.data["round_result"]
        assert round2["proposal"]["amount"] == "680.00"
        assert "phone_number" in round2["proposal"]["data_fields_requested"]
        assert round2["outcome"] == "DENY"
        assert round2["policy_decision"]["outcome"] == PolicyDecisionOutcome.DENY
        assert round2["policy_decision"]["risk_level"] == "CRITICAL"
        assert round2["counter_offer"] is not None

        # 5. Process round 3: €700, no phone → REQUIRE_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round3 = response.data["round_result"]
        assert round3["proposal"]["amount"] == "700.00"
        assert round3["proposal"]["data_fields_requested"] == []
        assert round3["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        # 6. Verify final state
        response = client.get(f"/api/v1/negotiations/{room_id}/")
        assert response.status_code == status.HTTP_200_OK
        # Room stays IN_PROGRESS per DEL-024 R-102 (approval flow deferred to DEL-027)
        assert response.data["current_round"] == 3

        # Verify proposals
        response = client.get(f"/api/v1/negotiations/{room_id}/proposals/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        amounts = [p["amount"] for p in response.data]
        assert "820.00" in amounts
        assert "680.00" in amounts
        assert "700.00" in amounts

        # Verify messages
        response = client.get(f"/api/v1/negotiations/{room_id}/messages/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3

    def test_audit_trail_completeness(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        """Verify that the audit trail contains all expected events."""
        from apps.audit.models import AuditEvent

        initial_count = AuditEvent.objects.count()

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create and run negotiation
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(hotel_agent.id),
                "constitution_id": str(madrid_constitution.id),
                "title": "Hotel Madrid",
                "user_instruction": "Find hotel in Madrid",
            },
            format="json",
        )
        room_id = response.data["id"]

        client.post(f"/api/v1/negotiations/{room_id}/start/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")

        # Verify audit events
        events = AuditEvent.objects.all().order_by("created_at")
        event_types = [e.event_type for e in events]

        # Should have at least:
        # - negotiation.started (1)
        # - proposal.received (3)
        # - proposal.evaluated (3)
        # - proposal.denied (1, for round 2)
        # - counterproposal.created (1, for round 2)
        assert events.count() >= initial_count + 9

        from core.enums import EventType

        assert EventType.NEGOTIATION_STARTED in event_types
        assert EventType.PROPOSAL_RECEIVED in event_types
        assert EventType.PROPOSAL_EVALUATED in event_types
        assert EventType.PROPOSAL_DENIED in event_types
        assert EventType.COUNTERPROPOSAL_CREATED in event_types

    def test_policy_decisions_created(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        """Verify that PolicyDecision records are created for each proposal."""
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(hotel_agent.id),
                "constitution_id": str(madrid_constitution.id),
                "title": "Hotel Madrid",
                "user_instruction": "Find hotel in Madrid",
            },
            format="json",
        )
        room_id = response.data["id"]

        client.post(f"/api/v1/negotiations/{room_id}/start/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")

        # Verify PolicyDecision records
        room = NegotiationRoom.objects.get(id=room_id)
        decisions = PolicyDecision.objects.filter(proposal__room=room)
        assert decisions.count() == 3

        # Verify outcomes
        outcomes = [d.outcome for d in decisions]
        assert PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL in outcomes
        assert PolicyDecisionOutcome.DENY in outcomes
