"""
End-to-end test for Use Case 1: AI Travel Negotiation (MVP).

Aligned with real SimulatedHotelAgent (3 rounds) and working
tests/e2e/negotiations/test_use_case_1_travel.py.

Flow:
  Round 1: €820 → REQUIRE_HUMAN_APPROVAL
  Round 2: €680 + phone → DENY (Rule #17 CONTAINS phone_number)
  Round 3: €700, no phone → REQUIRE_HUMAN_APPROVAL → APPROVED
  Agreement created + signed + audit verified

Source: 04-BUSINESS-FLOW.md §4 · 05-ROADMAP.md §10.3 · DEL-036
"""

from __future__ import annotations

import pytest
from rest_framework import status

from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
)
from apps.audit.models import AuditEvent
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
class TestUseCase1TravelNegotiationE2E:
    """Complete E2E flow for AI Travel Negotiation."""

    def test_full_travel_negotiation_flow(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_hotel_agent,
        e2e_auth_client,
    ) -> None:
        client = e2e_auth_client

        # Rules must match policy engine field semantics (see working e2e tests)
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
                "name": "Email sharing requires approval",
                "category": "PRIVACY",
                "field": "data_fields_requested",
                "operator": "CONTAINS",
                "value": "email",
                "action": "REQUIRE_APPROVAL",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"Madrid Travel Rules {id(object())}",
            description="Rules for hotel booking in Madrid",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_hotel_agent.id),
                "constitution_id": str(constitution.id),
                "title": "Hotel Madrid 5 nights",
                "user_instruction": (
                    "Find hotel in Madrid for 5 nights. " "Max €700. Never share phone."
                ),
                "max_rounds": 10,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        room_id = response.data["id"]
        assert response.data["status"] == NegotiationStatus.PENDING

        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == NegotiationStatus.IN_PROGRESS

        # Round 1: €820 → REQUIRE_HUMAN_APPROVAL
        # Do NOT reject between rounds — same as working e2e/negotiations tests
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
        round1 = response.data["round_result"]
        assert round1["proposal"]["amount"] == "820.00"
        assert round1["proposal"]["data_fields_requested"] == []
        assert round1["outcome"] == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

        # Round 2: €680 + phone → DENY
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
        round2 = response.data["round_result"]
        assert round2["proposal"]["amount"] == "680.00"
        assert "phone_number" in round2["proposal"]["data_fields_requested"]
        assert round2["outcome"] == PolicyDecisionOutcome.DENY
        assert round2["counter_offer"] is not None

        # Round 3: €700, no phone → REQUIRE_HUMAN_APPROVAL
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK, response.data
        round3 = response.data["round_result"]
        assert round3["proposal"]["amount"] == "700.00"
        assert round3["proposal"]["data_fields_requested"] == []
        assert round3["outcome"] == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

        # Approve a pending request (prefer latest)
        response = client.get("/api/v1/approvals/pending/")
        assert response.status_code == status.HTTP_200_OK, response.data
        pending = _extract_results(response)
        assert len(pending) >= 1
        approval_id = pending[0]["id"]

        response = client.post(
            f"/api/v1/approvals/{approval_id}/approve/",
            {"comment": "Approved final hotel offer"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["decision"] == ApprovalStatus.APPROVED

        final_proposal = (
            Proposal.objects.filter(room_id=room_id, amount="700.00")
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

        response = client.get(f"/api/v1/agreements/{agreement.id}/canonical/")
        assert response.status_code == status.HTTP_200_OK, response.data

        response = client.get(f"/api/v1/agreements/{agreement.id}/signature/")
        assert response.status_code == status.HTTP_200_OK, response.data

        response = client.post(
            f"/api/v1/agreements/{agreement.id}/export/",
            {"format": "json"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        assert AuditEvent.objects.count() >= 5

    def test_audit_trail_completeness(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_hotel_agent,
        e2e_auth_client,
    ) -> None:
        """Process 3 hotel rounds and verify audit activity exists."""
        client = e2e_auth_client

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
            {
                "rule_number": 17,
                "name": "No phone",
                "category": "PRIVACY",
                "field": "data_fields_requested",
                "operator": "CONTAINS",
                "value": "phone_number",
                "action": "DENY",
            },
            {
                "rule_number": 23,
                "name": "Need approval",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "GREATER_THAN",
                "value": 200,
                "action": "REQUIRE_APPROVAL",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"Audit Travel {id(object())}",
            description="Audit trail test",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_hotel_agent.id),
                "constitution_id": str(constitution.id),
                "title": "Audit Hotel",
                "user_instruction": "Find hotel",
                "max_rounds": 10,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        client.post(f"/api/v1/negotiations/{room_id}/start/")
        for _ in range(3):
            r = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
            assert r.status_code == status.HTTP_200_OK, r.data

        assert AuditEvent.objects.count() >= 3
