"""Tests for automatic approval expiration."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.agents.models import Agent
from apps.approvals.models import ApprovalDecision, ApprovalRequest
from apps.approvals.services import create_approval_request, expire_stale_approvals
from apps.audit.models import AuditEvent
from apps.constitutions.services import activate_version, create_constitution_with_rules
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ApprovalStatus,
    EventType,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="expire@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent")


@pytest.fixture
def constitution_with_rules(user, user_agent):
    rules = [
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
        agent=user_agent, name="Rules", description=None, rules=rules, user=user
    )
    activate_version(version=version, user=user)
    return constitution


@pytest.fixture
def room(user_agent, external_agent, constitution_with_rules):
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution_with_rules,
        reference_code="NEG-EXPIRE-001",
        title="Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room, external_agent):
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=820.00,
        currency="EUR",
        round_number=1,
        status=ProposalStatus.EVALUATING,
    )


@pytest.fixture
def policy_decision(proposal, constitution_with_rules):
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_with_rules.active_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Amount exceeds auto-approve limit",
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.mark.django_db
class TestApprovalExpiration:
    def test_expire_stale_approval(self, proposal, policy_decision, room) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        expired_count = expire_stale_approvals()
        assert expired_count == 1

        request.refresh_from_db()
        assert request.status == ApprovalStatus.EXPIRED

    def test_expire_creates_system_decision(self, proposal, policy_decision, room) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        expire_stale_approvals()

        decisions = ApprovalDecision.objects.filter(request=request)
        assert decisions.count() == 1
        decision = decisions.first()
        assert decision.decision == ApprovalStatus.EXPIRED
        assert decision.decided_by is None
        assert decision.comment == "Expired due to timeout"

    def test_expire_updates_proposal_status(self, proposal, policy_decision, room) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        expire_stale_approvals()

        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.REJECTED

    def test_expire_creates_audit_event(self, proposal, policy_decision, room) -> None:
        """Expiration creates exactly one new audit event."""
        # Create the approval first, then measure the delta for expiration only
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        # Snapshot AFTER create_approval_request, so we count only expiration events
        count_after_create = AuditEvent.objects.count()

        expire_stale_approvals()

        assert AuditEvent.objects.count() == count_after_create + 1
        event = AuditEvent.objects.order_by("-created_at").first()
        assert event.event_type == EventType.APPROVAL_EXPIRED.value

    def test_do_not_expire_active_approval(self, proposal, policy_decision, room) -> None:
        create_approval_request(proposal=proposal, policy_decision=policy_decision, room=room)

        expired_count = expire_stale_approvals()
        assert expired_count == 0

    def test_do_not_expire_already_decided(self, proposal, policy_decision, room, user) -> None:
        """Already-decided approvals must NOT be expired."""
        from apps.approvals.services import process_approval_decision

        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        process_approval_decision(request=request, user=user, decision=ApprovalStatus.APPROVED)

        # Refresh from DB so we have the APPROVED status in memory
        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED

        # Use QuerySet.update() to bypass state machine for testing only
        ApprovalRequest.objects.filter(id=request.id).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )

        expired_count = expire_stale_approvals()
        assert expired_count == 0

        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED

    def test_expire_multiple_stale(
        self, user, user_agent, external_agent, constitution_with_rules
    ) -> None:
        for i in range(3):
            room = NegotiationRoom.objects.create(
                user_agent=user_agent,
                external_agent=external_agent,
                constitution=constitution_with_rules,
                reference_code=f"NEG-EXPIRE-{i:03d}",
                title="Test",
                user_instruction="Test",
            )
            proposal = Proposal.objects.create(
                room=room,
                sender=external_agent,
                action_type="purchase",
                amount=820.00,
                currency="EUR",
                round_number=1,
                status=ProposalStatus.EVALUATING,
            )
            policy_decision = PolicyDecision.objects.create(
                proposal=proposal,
                constitution_version=constitution_with_rules.active_version,
                outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
                risk_level=RiskLevel.LOW,
                reason="Test",
                evaluation_duration_ms=10,
                engine_version="1.0.0",
            )
            request = create_approval_request(
                proposal=proposal, policy_decision=policy_decision, room=room
            )
            request.expires_at = timezone.now() - timedelta(hours=1)
            request.save()

        expired_count = expire_stale_approvals()
        assert expired_count == 3

        for room in NegotiationRoom.objects.filter(reference_code__startswith="NEG-EXPIRE-"):
            approval = ApprovalRequest.objects.get(room=room)
            assert approval.status == ApprovalStatus.EXPIRED

    def test_celery_task_runs(self) -> None:
        from apps.approvals.tasks import expire_stale_approvals_task

        result = expire_stale_approvals_task()
        assert isinstance(result, dict)
        assert "expired_count" in result
        assert isinstance(result["expired_count"], int)
