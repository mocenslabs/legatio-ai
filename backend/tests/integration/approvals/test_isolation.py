"""
Isolation tests for Approval API.

Ensures users cannot access or decide on other users' approvals.
Source: 00-INDEX.md Section 2.5
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services.auth import generate_access_token
from apps.agents.models import Agent
from apps.approvals.models import ApprovalRequest
from apps.approvals.services import create_approval_request
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ApprovalStatus,
    ConstitutionStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)

User = get_user_model()


def _make_approval_for(owner: Any, ref_code: str) -> ApprovalRequest:
    """Helper to create a full approval chain owned by ``owner``."""
    agent = Agent.objects.create(
        owner=owner,
        agent_type=AgentType.USER_AGENT,
        name=f"Agent-{ref_code}",
    )
    external = Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name=f"External-{ref_code}",
    )
    constitution = Constitution.objects.create(
        agent=agent,
        name=f"Const-{ref_code}",
        status=ConstitutionStatus.ACTIVE,
    )
    version = ConstitutionVersion.objects.create(
        constitution=constitution,
        version_number=1,
        created_by=owner,
    )
    room = NegotiationRoom.objects.create(
        user_agent=agent,
        external_agent=external,
        constitution=constitution,
        reference_code=ref_code,
        title="Isolation Test",
        user_instruction="Test",
    )
    proposal = Proposal.objects.create(
        room=room,
        sender=external,
        action_type="purchase",
        amount=Decimal("500.00"),
        currency="EUR",
        data_fields_requested=[],
        terms={},
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )
    policy_decision = PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.MEDIUM,
        reason="Isolation test",
        evaluation_duration_ms=5,
        engine_version="1.0.0",
    )
    return create_approval_request(
        proposal=proposal,
        policy_decision=policy_decision,
        room=room,
    )


@pytest.fixture
def alice() -> Any:
    return User.objects.create_user(email="alice@example.com", password="pass1234")


@pytest.fixture
def bob() -> Any:
    return User.objects.create_user(email="bob@example.com", password="pass1234")


@pytest.fixture
def bob_approval(bob: Any) -> ApprovalRequest:
    return _make_approval_for(bob, "NEG-BOB-ISO-001")


@pytest.fixture
def alice_client(alice: Any) -> APIClient:
    client = APIClient()
    token = generate_access_token(alice)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestApprovalIsolation:
    def test_alice_cannot_list_bobs_approvals(
        self, alice_client: APIClient, bob_approval: ApprovalRequest
    ) -> None:
        response = alice_client.get("/api/v1/approvals/")
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        data = response.data
        results = data.get("results", data) if isinstance(data, dict) else data
        ids = [str(item["id"]) for item in results]
        assert str(bob_approval.id) not in ids

    def test_alice_cannot_retrieve_bobs_approval(
        self, alice_client: APIClient, bob_approval: ApprovalRequest
    ) -> None:
        response = alice_client.get(f"/api/v1/approvals/{bob_approval.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_alice_cannot_approve_bobs_approval(
        self, alice_client: APIClient, bob_approval: ApprovalRequest
    ) -> None:
        response = alice_client.post(
            f"/api/v1/approvals/{bob_approval.id}/approve/",
            {"comment": "Hacked"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        bob_approval.refresh_from_db()
        assert bob_approval.status == ApprovalStatus.PENDING

    def test_alice_cannot_reject_bobs_approval(
        self, alice_client: APIClient, bob_approval: ApprovalRequest
    ) -> None:
        response = alice_client.post(
            f"/api/v1/approvals/{bob_approval.id}/reject/",
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        bob_approval.refresh_from_db()
        assert bob_approval.status == ApprovalStatus.PENDING

    def test_alice_cannot_modify_bobs_approval(
        self, alice_client: APIClient, bob_approval: ApprovalRequest
    ) -> None:
        response = alice_client.post(
            f"/api/v1/approvals/{bob_approval.id}/modify/",
            {"modifications": {"amount": "1"}, "comment": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        bob_approval.refresh_from_db()
        assert bob_approval.status == ApprovalStatus.PENDING
