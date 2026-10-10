"""
Integration tests for Approval API endpoints.

Source: 05-ROADMAP.md Section 8.5
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


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="api-user@example.com", password="pass1234")


@pytest.fixture
def other_user() -> Any:
    return User.objects.create_user(email="other@example.com", password="pass1234")


@pytest.fixture
def user_agent(user: Any) -> Agent:
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="User Agent",
    )


@pytest.fixture
def external_agent() -> Agent:
    return Agent.objects.create(
        owner=None,
        agent_type=AgentType.SIMULATED,
        name="Hotel Agent",
    )


@pytest.fixture
def constitution(user_agent: Agent) -> Constitution:
    return Constitution.objects.create(
        agent=user_agent,
        name="Travel Rules",
        status=ConstitutionStatus.ACTIVE,
    )


@pytest.fixture
def constitution_version(user: Any, constitution: Constitution) -> ConstitutionVersion:
    return ConstitutionVersion.objects.create(
        constitution=constitution,
        version_number=1,
        created_by=user,
    )


@pytest.fixture
def room(
    user_agent: Agent,
    external_agent: Agent,
    constitution: Constitution,
) -> NegotiationRoom:
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-API-001",
        title="API Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room: NegotiationRoom, external_agent: Agent) -> Proposal:
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        data_fields_requested=[],
        terms={"nights": 5},
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )


@pytest.fixture
def policy_decision(
    proposal: Proposal,
    constitution_version: ConstitutionVersion,
) -> PolicyDecision:
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Amount exceeds auto-approve limit",
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.fixture
def approval_request(
    proposal: Proposal,
    policy_decision: PolicyDecision,
    room: NegotiationRoom,
) -> ApprovalRequest:
    return create_approval_request(
        proposal=proposal,
        policy_decision=policy_decision,
        room=room,
    )


@pytest.fixture
def api_client(user: Any) -> APIClient:
    client = APIClient()
    token = generate_access_token(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestApprovalListAPI:
    def test_list_approvals(self, api_client: APIClient, approval_request: ApprovalRequest) -> None:
        response = api_client.get("/api/v1/approvals/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        # Handle both paginated and non-paginated responses
        data = response.data
        results = data.get("results", data) if isinstance(data, dict) else data
        approval_ids = [str(item["id"]) for item in results]
        assert str(approval_request.id) in approval_ids

    def test_list_pending(self, api_client: APIClient, approval_request: ApprovalRequest) -> None:
        response = api_client.get("/api/v1/approvals/pending/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert all(item["status"] == ApprovalStatus.PENDING for item in response.data)

    def test_list_requires_auth(self) -> None:
        client = APIClient()
        response = client.get("/api/v1/approvals/")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


@pytest.mark.django_db
class TestApprovalRetrieveAPI:
    def test_retrieve_approval(
        self, api_client: APIClient, approval_request: ApprovalRequest
    ) -> None:
        response = api_client.get(f"/api/v1/approvals/{approval_request.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(approval_request.id)
        assert "proposal_details" in response.data
        assert "policy_decision_details" in response.data
        assert "summary" in response.data

    def test_retrieve_not_found(self, api_client: APIClient) -> None:
        import uuid

        response = api_client.get(f"/api/v1/approvals/{uuid.uuid4()}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestApprovalDecisionAPI:
    def test_approve(self, api_client: APIClient, approval_request: ApprovalRequest) -> None:
        response = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/approve/",
            {"comment": "Looks good"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.APPROVED

        approval_request.refresh_from_db()
        assert approval_request.status == ApprovalStatus.APPROVED

    def test_reject(self, api_client: APIClient, approval_request: ApprovalRequest) -> None:
        response = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/reject/",
            {"comment": "Too expensive"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.REJECTED

        approval_request.refresh_from_db()
        assert approval_request.status == ApprovalStatus.REJECTED

    def test_modify(self, api_client: APIClient, approval_request: ApprovalRequest) -> None:
        response = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/modify/",
            {
                "modifications": {"amount": "700.00"},
                "comment": "Lower the price",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.MODIFIED
        assert response.data["modifications"] == {"amount": "700.00"}

        approval_request.refresh_from_db()
        assert approval_request.status == ApprovalStatus.MODIFIED

    def test_modify_requires_modifications(
        self, api_client: APIClient, approval_request: ApprovalRequest
    ) -> None:
        response = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/modify/",
            {"comment": "Missing mods"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_approve_twice_returns_409(
        self, api_client: APIClient, approval_request: ApprovalRequest
    ) -> None:
        first = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/approve/",
            {},
            format="json",
        )
        assert first.status_code == status.HTTP_201_CREATED

        second = api_client.post(
            f"/api/v1/approvals/{approval_request.id}/approve/",
            {},
            format="json",
        )
        assert second.status_code == status.HTTP_409_CONFLICT
