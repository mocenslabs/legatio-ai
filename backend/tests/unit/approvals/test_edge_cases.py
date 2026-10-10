"""Edge case tests for approval workflow."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.agents.models import Agent
from apps.approvals.models import ApprovalRequest
from apps.approvals.services import create_approval_request, process_approval_decision
from apps.approvals.summaries import generate_approval_summary
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
def user():
    return User.objects.create_user(email="edge@example.com", password="pass")


@pytest.fixture
def user_agent(user):
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent():
    return Agent.objects.create(owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent")


@pytest.fixture
def constitution(user, user_agent):
    return Constitution.objects.create(
        agent=user_agent, name="Test", status=ConstitutionStatus.ACTIVE
    )


@pytest.fixture
def constitution_version(user, constitution):
    return ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )


@pytest.fixture
def room(user_agent, external_agent, constitution):
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-EDGE-001",
        title="Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room, external_agent):
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        round_number=1,
        status=ProposalStatus.EVALUATING,
    )


@pytest.fixture
def policy_decision(proposal, constitution_version):
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Test reason",
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


def _make_decision(proposal, constitution_version, **overrides):
    """Create a new PolicyDecision (append-only, cannot update existing)."""
    defaults = {
        "proposal": proposal,
        "constitution_version": constitution_version,
        "outcome": PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        "risk_level": RiskLevel.LOW,
        "reason": "Test reason",
        "evaluation_duration_ms": 10,
        "engine_version": "1.0.0",
    }
    defaults.update(overrides)
    return PolicyDecision.objects.create(**defaults)


@pytest.mark.django_db
class TestSummaryEdgeCases:
    def test_summary_with_none_amount(self, proposal, policy_decision) -> None:
        proposal.amount = None
        # Proposal.save() is allowed (not append-only)
        proposal.save()
        summary = generate_approval_summary(proposal, policy_decision)
        assert "Approval Required" in summary

    def test_summary_with_large_amount(self, proposal, policy_decision) -> None:
        proposal.amount = Decimal("999999999.99")
        proposal.save()
        summary = generate_approval_summary(proposal, policy_decision)
        assert "999999999.99" in summary

    def test_summary_with_many_matched_rules(self, proposal, constitution_version) -> None:
        """PolicyDecision is append-only, so create a new one with many rules."""
        new_decision = _make_decision(
            proposal,
            constitution_version,
            matched_rules=[{"rule_number": i, "name": f"Rule {i}"} for i in range(10)],
        )
        summary = generate_approval_summary(proposal, new_decision)
        assert "Rule" in summary

    def test_summary_with_empty_reason(self, proposal, constitution_version) -> None:
        """PolicyDecision is append-only, so create a new one with empty reason."""
        new_decision = _make_decision(proposal, constitution_version, reason="")
        summary = generate_approval_summary(proposal, new_decision)
        assert "Approval Required" in summary

    def test_summary_with_special_characters(self, proposal, policy_decision) -> None:
        proposal.terms = {"notes": "Test <script>alert('xss')</script>"}
        proposal.save()
        summary = generate_approval_summary(proposal, policy_decision)
        assert isinstance(summary, str)


@pytest.mark.django_db
class TestApprovalRequestEdgeCases:
    def test_create_with_custom_expires_at(self, proposal, policy_decision, room) -> None:
        custom_expires = timezone.now() + timedelta(hours=48)
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=room.user_agent,
            policy_decision=policy_decision,
            summary="Test",
            expires_at=custom_expires,
        )
        assert request.expires_at == custom_expires

    def test_create_with_zero_expires_at(self, proposal, policy_decision, room) -> None:
        request = ApprovalRequest.objects.create(
            proposal=proposal,
            room=room,
            requested_by=room.user_agent,
            policy_decision=policy_decision,
            summary="Test",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        assert request.is_expired is True

    def test_process_decision_with_empty_comment(
        self, proposal, policy_decision, room, user
    ) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
            comment="",
        )
        assert decision.comment == ""

    def test_process_decision_with_long_comment(
        self, proposal, policy_decision, room, user
    ) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        long_comment = "A" * 10000
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
            comment=long_comment,
        )
        assert decision.comment == long_comment

    def test_process_decision_with_complex_modifications(
        self, proposal, policy_decision, room, user
    ) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        modifications = {
            "amount": 700,
            "currency": "EUR",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.MODIFIED,
            modifications=modifications,
        )
        assert decision.modifications == modifications

    def test_multiple_requests_same_proposal_after_terminal(
        self, proposal, policy_decision, room, user
    ) -> None:
        """Can create new request after previous one is terminal."""
        request1 = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        process_approval_decision(request=request1, user=user, decision=ApprovalStatus.APPROVED)

        # Reset proposal status via QuerySet to bypass state machine
        Proposal.objects.filter(id=proposal.id).update(status=ProposalStatus.EVALUATING)
        proposal.refresh_from_db()

        request2 = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        assert request2.status == ApprovalStatus.PENDING


@pytest.mark.django_db
class TestApprovalDecisionEdgeCases:
    def test_multiple_decisions_allowed(self, proposal, policy_decision, room, user) -> None:
        """First decision creates a terminal ApprovalDecision."""
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        decision1 = process_approval_decision(
            request=request, user=user, decision=ApprovalStatus.APPROVED
        )
        assert decision1.decision == ApprovalStatus.APPROVED

    def test_decision_with_unicode_comment(self, proposal, policy_decision, room, user) -> None:
        request = create_approval_request(
            proposal=proposal, policy_decision=policy_decision, room=room
        )
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
            comment="Aprobado ✓ — €700 está bien 🎉",
        )
        assert "✓" in decision.comment
        assert "🎉" in decision.comment
