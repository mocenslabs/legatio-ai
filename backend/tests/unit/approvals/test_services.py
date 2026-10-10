"""
Unit tests for approval services.
Source: 04-BUSINESS-FLOW.md Section 9
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.agents.models import Agent
from apps.approvals.models import ApprovalDecision
from apps.approvals.services import (
    create_approval_request,
    expire_stale_approvals,
    process_approval_decision,
)
from apps.audit.models import AuditEvent
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
from core.exceptions import (
    ApprovalAlreadyDecidedError,
    ApprovalExpiredError,
    ApprovalUnauthorizedError,
)

User = get_user_model()


@pytest.fixture
def user() -> Any:
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="Hotel Agent")


@pytest.fixture
def constitution(user: Any, user_agent: Any) -> Any:
    return Constitution.objects.create(
        agent=user_agent, name="Travel", status=ConstitutionStatus.ACTIVE
    )


@pytest.fixture
def constitution_version(user: Any, constitution: Any) -> Any:
    return ConstitutionVersion.objects.create(
        constitution=constitution, version_number=1, created_by=user
    )


@pytest.fixture
def room(user_agent: Any, external_agent: Any, constitution: Any) -> Any:
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-2026-0001",
        title="Test",
        user_instruction="Test",
    )


@pytest.fixture
def proposal(room: Any, external_agent: Any) -> Any:
    return Proposal.objects.create(
        room=room,
        sender=external_agent,
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        data_fields_requested=[],
        terms={"nights": 5, "destination": "Madrid"},
        status=ProposalStatus.EVALUATING,
        round_number=1,
    )


@pytest.fixture
def policy_decision(proposal: Any, constitution_version: Any) -> Any:
    return PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Amount €820 exceeds auto-approve limit of €200",
        matched_rules=[
            {
                "rule_id": "rule-23",
                "rule_number": 23,
                "name": "Large payments",
                "action": "REQUIRE_APPROVAL",
            }
        ],
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )


@pytest.mark.django_db
class TestCreateApprovalRequest:
    def test_create_request(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
    ) -> None:
        """ApprovalRequest can be created."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        assert request.status == ApprovalStatus.PENDING
        assert request.proposal == proposal
        assert request.room == room
        assert "Approval Required" in request.summary
        assert request.expires_at > timezone.now()

    def test_create_request_updates_proposal_status(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
    ) -> None:
        """Creating request updates proposal to PENDING_APPROVAL."""
        create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.PENDING_APPROVAL

    def test_create_request_creates_audit_event(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
    ) -> None:
        """Creating request creates audit event."""
        initial_count = AuditEvent.objects.count()
        create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        assert AuditEvent.objects.count() == initial_count + 1

    def test_create_duplicate_request_raises(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
    ) -> None:
        """Cannot create duplicate request for same proposal."""
        create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        with pytest.raises(ValueError, match="already has an active"):
            create_approval_request(
                proposal=proposal,
                policy_decision=policy_decision,
                room=room,
            )


@pytest.mark.django_db
class TestProcessApprovalDecision:
    def test_approve(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """User can approve a request."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
            comment="Looks good",
        )
        assert decision.decision == ApprovalStatus.APPROVED
        assert decision.decided_by == user
        assert decision.comment == "Looks good"
        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED
        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.ACCEPTED

    def test_reject(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """User can reject a request."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.REJECTED,
            comment="Too expensive",
        )
        assert decision.decision == ApprovalStatus.REJECTED
        request.refresh_from_db()
        assert request.status == ApprovalStatus.REJECTED
        proposal.refresh_from_db()
        assert proposal.status == ProposalStatus.REJECTED

    def test_modify(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """User can modify a request."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        decision = process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.MODIFIED,
            modifications={"amount": 700},
            comment="Reduce to €700",
        )
        assert decision.decision == ApprovalStatus.MODIFIED
        assert decision.modifications == {"amount": 700}

    def test_already_decided_raises(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """Cannot decide on an already decided request."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
        )
        with pytest.raises(ApprovalAlreadyDecidedError):
            process_approval_decision(
                request=request,
                user=user,
                decision=ApprovalStatus.REJECTED,
            )

    def test_expired_raises(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """Cannot decide on an expired request."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        # Manually expire
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()
        with pytest.raises(ApprovalExpiredError):
            process_approval_decision(
                request=request,
                user=user,
                decision=ApprovalStatus.APPROVED,
            )

    def test_unauthorized_raises(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """User cannot decide on another user's request."""
        other_user = User.objects.create_user(email="other@example.com", password="pass")
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        with pytest.raises(ApprovalUnauthorizedError):
            process_approval_decision(
                request=request,
                user=other_user,
                decision=ApprovalStatus.APPROVED,
            )


@pytest.mark.django_db
class TestExpireStaleApprovals:
    def test_expire_stale(self, proposal: Any, policy_decision: Any, room: Any) -> None:
        """Stale approvals are expired."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        # Manually expire
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        expired_count = expire_stale_approvals()
        assert expired_count == 1

        request.refresh_from_db()
        assert request.status == ApprovalStatus.EXPIRED

        # Check that a system decision was created
        decisions = ApprovalDecision.objects.filter(request=request)
        assert decisions.count() == 1
        assert decisions.first().decision == ApprovalStatus.EXPIRED
        assert decisions.first().decided_by is None

    def test_do_not_expire_active(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
    ) -> None:
        """Active approvals are not expired."""
        create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        # expires_at is in the future (24h)
        expired_count = expire_stale_approvals()
        assert expired_count == 0

    def test_do_not_expire_already_decided(
        self,
        proposal: Any,
        policy_decision: Any,
        room: Any,
        user: Any,
    ) -> None:
        """Already decided approvals are not expired."""
        request = create_approval_request(
            proposal=proposal,
            policy_decision=policy_decision,
            room=room,
        )
        process_approval_decision(
            request=request,
            user=user,
            decision=ApprovalStatus.APPROVED,
        )
        # Refresh to get the updated status (APPROVED) from DB
        request.refresh_from_db()
        # Manually set expires_at to past
        request.expires_at = timezone.now() - timedelta(hours=1)
        request.save()

        expired_count = expire_stale_approvals()
        assert expired_count == 0

        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED
