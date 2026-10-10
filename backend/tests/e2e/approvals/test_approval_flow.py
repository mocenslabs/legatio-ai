"""End-to-end test for the complete approval workflow."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditEvent
from apps.constitutions.services import activate_version, create_constitution_with_rules
from core.enums import (
    AgentType,
    ApprovalStatus,
    EventType,
    ProposalStatus,
)
from services.negotiation_engine.orchestrator import NegotiationOrchestrator

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="e2e_approval@example.com", password="e2e1234")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="My Travel Agent")


@pytest.fixture
def hotel_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent")


@pytest.fixture
def madrid_constitution(user, user_agent):
    # Note: only use fields recognized by Policy Engine evaluator (amount).
    # 'phone_number' is NOT a known field and raises InvalidRuleError.
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
            "rule_number": 23,
            "name": "Large payments need approval",
            "category": "FINANCIAL",
            "field": "amount",
            "operator": "GREATER_THAN",
            "value": 200,
            "action": "REQUIRE_APPROVAL",
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
class TestApprovalWorkflowE2E:
    def test_full_approval_flow_via_api(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        """Complete flow: create -> start -> round -> approve."""
        from apps.accounts.services.auth import generate_access_token

        token = generate_access_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Use format='json' to avoid 415 Unsupported Media Type
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(user_agent.id),
                "external_agent_id": str(hotel_agent.id),
                "constitution_id": str(madrid_constitution.id),
                "title": "Hotel Madrid 5 nights",
                "user_instruction": "Find hotel in Madrid for 5 nights. Max €700.",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        room_id = response.data["id"]

        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK

        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
        round_result = response.data["round_result"]
        assert round_result["outcome"] == "REQUIRE_HUMAN_APPROVAL"

        response = client.get("/api/v1/approvals/pending/")
        assert response.status_code == status.HTTP_200_OK
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        assert len(results) >= 1
        approval_id = results[0]["id"]

        response = client.get(f"/api/v1/approvals/{approval_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == ApprovalStatus.PENDING

        response = client.post(
            f"/api/v1/approvals/{approval_id}/approve/",
            {"comment": "Approved via E2E test"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.APPROVED

        approval = ApprovalRequest.objects.get(id=approval_id)
        assert approval.status == ApprovalStatus.APPROVED
        assert approval.proposal.status == ProposalStatus.ACCEPTED

    def test_reject_flow(self, user, user_agent, hotel_agent, madrid_constitution) -> None:
        from apps.accounts.services.auth import generate_access_token

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
                "user_instruction": "Find hotel",
            },
            format="json",
        )
        room_id = response.data["id"]
        client.post(f"/api/v1/negotiations/{room_id}/start/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")

        response = client.get("/api/v1/approvals/pending/")
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        approval_id = results[0]["id"]

        response = client.post(
            f"/api/v1/approvals/{approval_id}/reject/",
            {"comment": "Too expensive"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.REJECTED

    def test_modify_flow(self, user, user_agent, hotel_agent, madrid_constitution) -> None:
        from apps.accounts.services.auth import generate_access_token

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
                "user_instruction": "Find hotel",
            },
            format="json",
        )
        room_id = response.data["id"]
        client.post(f"/api/v1/negotiations/{room_id}/start/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")

        response = client.get("/api/v1/approvals/pending/")
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        approval_id = results[0]["id"]

        response = client.post(
            f"/api/v1/approvals/{approval_id}/modify/",
            {"modifications": {"amount": 700}, "comment": "Reduce to €700"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["decision"] == ApprovalStatus.MODIFIED
        assert response.data["modifications"] == {"amount": 700}

    def test_audit_trail_completeness(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        initial_count = AuditEvent.objects.count()

        room = NegotiationOrchestrator.create_room(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=madrid_constitution,
            title="Hotel Madrid",
            user_instruction="Find hotel",
            user=user,
        )
        orchestrator = NegotiationOrchestrator(room)
        orchestrator.start_negotiation()
        orchestrator.process_round()

        approval = ApprovalRequest.objects.get(room=room)
        from apps.approvals.services import process_approval_decision

        process_approval_decision(
            request=approval, user=user, decision=ApprovalStatus.APPROVED, comment="Test"
        )

        events = AuditEvent.objects.all().order_by("created_at")
        event_types = [e.event_type for e in events]
        assert events.count() >= initial_count + 5
        assert EventType.APPROVAL_REQUESTED in event_types
        assert EventType.APPROVAL_APPROVED in event_types

    def test_multiple_decisions_not_allowed(
        self, user, user_agent, hotel_agent, madrid_constitution
    ) -> None:
        from apps.accounts.services.auth import generate_access_token

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
                "user_instruction": "Find hotel",
            },
            format="json",
        )
        room_id = response.data["id"]
        client.post(f"/api/v1/negotiations/{room_id}/start/")
        client.post(f"/api/v1/negotiations/{room_id}/process_round/")

        response = client.get("/api/v1/approvals/pending/")
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        approval_id = results[0]["id"]

        client.post(
            f"/api/v1/approvals/{approval_id}/approve/",
            {"comment": "OK"},
            format="json",
        )
        response = client.post(
            f"/api/v1/approvals/{approval_id}/reject/",
            {"comment": "Too late"},
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT
