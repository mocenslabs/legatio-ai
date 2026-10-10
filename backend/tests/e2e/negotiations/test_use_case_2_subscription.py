"""
End-to-end test for Use Case 2: Subscription Negotiation via API.

This test reproduces the complete flow from 04-BUSINESS-FLOW.md Section 5:
"Negotiate my internet bill. I want to pay less than €100/month
and I don't want auto-renewal."

The test verifies the full flow via REST API:
  Round 1: €60/month, 24 months, auto-renewal → DENY (contract > 12)
  Round 2: €70/month, 12 months, no auto-renewal → REQUIRE_APPROVAL

Source: 04-BUSINESS-FLOW.md Section 5.2
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
from core.enums import AgentType, NegotiationStatus, PolicyDecisionOutcome

User = get_user_model()


@pytest.fixture
def user():
    return register_user(email="subscription@example.com", password="sub1234")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="My Subscription Agent",
    )


@pytest.fixture
def isp_agent():
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="ISP Agent",
    )


@pytest.fixture
def subscription_constitution(user, user_agent):
    """Create the subscription constitution from 04-BUSINESS-FLOW.md Section 5.1."""
    rules = [
        {
            "rule_number": 1,
            "name": "Max monthly spend",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 100,
            "action": "ALLOW",
        },
        {
            "rule_number": 5,
            "name": "Auto-approve limit",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "LESS_THAN_OR_EQUAL",
            "value": 50,
            "action": "ALLOW",
        },
        {
            "rule_number": 12,
            "name": "Max contract length",
            "category": "NEGOTIATION",
            "field": "contract_length_months",
            "operator": "GREATER_THAN",
            "value": 12,
            "action": "DENY",
        },
        {
            "rule_number": 15,
            "name": "Auto-renewal requires approval",
            "category": "NEGOTIATION",
            "field": "auto_renewal",
            "operator": "EQUALS",
            "value": True,
            "action": "REQUIRE_APPROVAL",
        },
        {
            "rule_number": 18,
            "name": "High monthly cost requires approval",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 65,
            "action": "REQUIRE_APPROVAL",
        },
        {
            "rule_number": 20,
            "name": "Price increase requires approval",
            "category": "FINANCIAL",
            "field": "price_increase_pct",
            "operator": "GREATER_THAN",
            "value": 10,
            "action": "REQUIRE_APPROVAL",
        },
    ]
    constitution, version = create_constitution_with_rules(
        agent=user_agent,
        name="ISP Subscription Rules",
        description="Rules for internet subscription negotiation",
        rules=rules,
        user=user,
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.mark.django_db
class TestUseCase2SubscriptionNegotiation:
    """Full scenario from 04-BUSINESS-FLOW.md Section 5.2."""

    def test_full_negotiation_flow_via_api(
        self, user, user_agent, isp_agent, subscription_constitution
    ) -> None:
        """
        Complete flow via API:
        1. Create negotiation room
        2. Start negotiation
        3. Process round 1: €60, 24 months, auto-renewal → DENY (contract > 12)
        4. Process round 2: €70, 12 months, no auto-renewal → REQUIRE_APPROVAL
        """
        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 1. Create negotiation room
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(isp_agent.id),
                "constitution_id": str(subscription_constitution.id),
                "title": "ISP Subscription",
                "user_instruction": "Negotiate my internet bill. Max €100/month, no auto-renewal.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        # 2. Start negotiation
        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == NegotiationStatus.IN_PROGRESS

        # 3. Process round 1: €60, 24 months, auto-renewal → DENY
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round1 = response.data["round_result"]
        assert round1["proposal"]["amount"] == "60.00"
        assert round1["proposal"]["contract_length_months"] == 24
        assert round1["proposal"]["auto_renewal"] is True
        assert round1["outcome"] == "DENY"
        assert round1["policy_decision"]["outcome"] == PolicyDecisionOutcome.DENY

        # 4. Process round 2: €70, 12 months, no auto-renewal → REQUIRE_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round2 = response.data["round_result"]
        assert round2["proposal"]["amount"] == "70.00"
        assert round2["proposal"]["contract_length_months"] == 12
        assert round2["proposal"]["auto_renewal"] is False
        assert round2["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        # Verify final state
        response = client.get(f"/api/v1/negotiations/{room_id}/")
        assert response.data["status"] == NegotiationStatus.AWAITING_APPROVAL
