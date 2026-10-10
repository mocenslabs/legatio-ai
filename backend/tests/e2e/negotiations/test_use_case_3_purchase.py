"""
End-to-end test for Use Case 3: Purchase Approval via API.

This test reproduces the complete flow from 04-BUSINESS-FLOW.md Section 6:
"Buy the book 'Clean Architecture' if it costs less than €30."

The test verifies the full flow via REST API:
  Round 1: €25 for Clean Architecture book → REQUIRE_APPROVAL

Source: 04-BUSINESS-FLOW.md Section 6.2
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
from core.enums import AgentType, NegotiationStatus

User = get_user_model()


@pytest.fixture
def user():
    return register_user(email="purchase@example.com", password="pur1234")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="My Shopping Agent",
    )


@pytest.fixture
def vendor_agent():
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Vendor Agent",
    )


@pytest.fixture
def purchase_constitution(user, user_agent):
    """Create the purchase constitution from 04-BUSINESS-FLOW.md Section 6.1."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max transaction",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 50,
            "action": "ALLOW",
        },
        {
            "rule_number": 5,
            "name": "Auto-approve limit",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 20,
            "action": "ALLOW",
        },
        {
            "rule_number": 8,
            "name": "Allowed categories",
            "category": "CUSTOM",
            "field": "category",
            "operator": "IN",
            "value": ["books", "electronics"],
            "action": "ALLOW",
        },
        {
            "rule_number": 10,
            "name": "Prohibited categories",
            "category": "CUSTOM",
            "field": "category",
            "operator": "IN",
            "value": ["gambling"],
            "action": "DENY",
        },
        {
            "rule_number": 15,
            "name": "New vendor requires approval",
            "category": "CUSTOM",
            "field": "is_new_vendor",
            "operator": "EQUALS",
            "value": True,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="Purchase Rules",
        description="Rules for purchases",
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db
class TestUseCase3PurchaseApproval:
    """Full scenario from 04-BUSINESS-FLOW.md Section 6.2."""

    def test_full_negotiation_flow_via_api(
        self, user, user_agent, vendor_agent, purchase_constitution
    ) -> None:
        """
        Complete flow via API:
        1. Create negotiation room
        2. Start negotiation
        3. Process round 1: €25 for Clean Architecture → REQUIRE_APPROVAL
        """
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 1. Create negotiation room
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(vendor_agent.id),
                "constitution_id": str(purchase_constitution.id),
                "title": "Buy Clean Architecture",
                "user_instruction": "Buy the book 'Clean Architecture' if it costs less than €30.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        # 2. Start negotiation
        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK

        # 3. Process round 1: €25 for Clean Architecture → REQUIRE_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round1 = response.data["round_result"]
        assert round1["proposal"]["amount"] == "25.00"
        assert round1["proposal"]["terms"]["product"] == "Clean Architecture"
        assert round1["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        # Verify final state
        response = client.get(f"/api/v1/negotiations/{room_id}/")
        assert response.data["status"] == NegotiationStatus.AWAITING_APPROVAL
        assert response.data["current_round"] == 1
