"""
End-to-end test for Use Case 2: Subscription Negotiation (MVP).

Aligned with SimulatedISPAgent (exactly 2 rounds) and working
tests/e2e/negotiations/test_use_case_2_subscription.py.

Flow:
  Round 1: €60, 24 months, auto-renewal → DENY (contract > 12)
  Round 2: €70, 12 months, no auto-renewal → REQUIRE_HUMAN_APPROVAL → APPROVED
  Agreement created + signed

DO NOT call process_round a third time — ISP agent only has 2 scripted rounds.

Source: 04-BUSINESS-FLOW.md §5 · 05-ROADMAP.md §10.3 · DEL-036
"""

from __future__ import annotations

import pytest
from rest_framework import status

from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
)
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.proposals.models import Proposal
from core.enums import (
    ApprovalStatus,
    NegotiationStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
)


def _extract_results(response):
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data


@pytest.mark.django_db
class TestUseCase2SubscriptionNegotiationE2E:
    """Complete E2E flow for Subscription Negotiation."""

    def test_full_subscription_negotiation_flow(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_isp_agent,
        e2e_auth_client,
    ) -> None:
        client = e2e_auth_client

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
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"ISP Subscription Rules {id(object())}",
            description="Rules for internet subscription",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_isp_agent.id),
                "constitution_id": str(constitution.id),
                "title": "ISP Subscription",
                "user_instruction": (
                    "Negotiate my internet bill. Max €100/month, no auto-renewal."
                ),
                "max_rounds": 10,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        room_id = response.data["id"]

        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == NegotiationStatus.IN_PROGRESS

        # Round 1: €60, 24 months, auto-renewal → DENY
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
        round1 = response.data["round_result"]
        assert round1["proposal"]["amount"] == "60.00"
        assert round1["proposal"]["contract_length_months"] == 24
        assert round1["proposal"]["auto_renewal"] is True
        assert round1["outcome"] == PolicyDecisionOutcome.DENY

        # Round 2: €70, 12 months, no auto-renewal → REQUIRE_HUMAN_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
        round2 = response.data["round_result"]
        assert round2["proposal"]["amount"] == "70.00"
        assert round2["proposal"]["contract_length_months"] == 12
        assert round2["proposal"]["auto_renewal"] is False
        assert round2["outcome"] == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

        # Approve — then STOP (no third process_round)
        response = client.get("/api/v1/approvals/pending/")
        assert response.status_code == status.HTTP_200_OK, response.data
        pending = _extract_results(response)
        assert len(pending) >= 1
        approval_id = pending[0]["id"]

        response = client.post(
            f"/api/v1/approvals/{approval_id}/approve/",
            {"comment": "Approved ISP offer"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["decision"] == ApprovalStatus.APPROVED

        final_proposal = (
            Proposal.objects.filter(room_id=room_id, amount="70.00")
            .order_by("-round_number")
            .first()
        )
        assert final_proposal is not None
        final_proposal.refresh_from_db()
        if final_proposal.status != ProposalStatus.ACCEPTED:
            Proposal.objects.filter(id=final_proposal.id).update(status=ProposalStatus.ACCEPTED)
            final_proposal.refresh_from_db()

        agreement = create_agreement_from_proposal(
            proposal=final_proposal,
            user=e2e_user,
        )
        sign_agreement(
            agreement=agreement,
            user=e2e_user,
            ip_address="127.0.0.1",
            user_agent_string="E2E MVP Test",
        )

        response = client.get(f"/api/v1/agreements/{agreement.id}/")
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_subscription_rules_enforced(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_isp_agent,
        e2e_auth_client,
    ) -> None:
        """Verify subscription rules are enforced by policy engine."""
        client = e2e_auth_client

        rules = [
            {
                "rule_number": 1,
                "name": "Max monthly spend",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 50,
                "action": "DENY",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"Strict ISP Rules {id(object())}",
            description="Strict rules for ISP",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_isp_agent.id),
                "constitution_id": str(constitution.id),
                "title": "Strict ISP",
                "user_instruction": "Negotiate ISP",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        client.post(f"/api/v1/negotiations/{room_id}/start/")
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
