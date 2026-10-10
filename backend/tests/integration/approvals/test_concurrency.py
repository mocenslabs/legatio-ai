"""Concurrency tests for approval decisions."""

import threading
import time

import pytest
from django.contrib.auth import get_user_model

from apps.agents.models import Agent
from apps.approvals.models import ApprovalDecision, ApprovalRequest
from apps.approvals.services import process_approval_decision
from apps.constitutions.services import activate_version, create_constitution_with_rules
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ApprovalStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)
from core.exceptions import ApprovalAlreadyDecidedError

User = get_user_model()


def _setup_approval_scenario(email: str, ref_code: str):
    """Helper to create a full approval scenario."""
    user = User.objects.create_user(email=email, password="pass")
    user_agent = Agent.objects.create(
        owner=user, agent_type=AgentType.USER_AGENT, name="User Agent"
    )
    external_agent = Agent.objects.create(
        owner=None, agent_type=AgentType.EXTERNAL_AGENT, name="Hotel Agent"
    )
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

    room = NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code=ref_code,
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
    # CRITICAL: transition proposal to PENDING_APPROVAL before creating ApprovalRequest
    # This matches the real flow where create_approval_request() does this transition
    proposal.transition_to(ProposalStatus.PENDING_APPROVAL)

    policy_decision = PolicyDecision.objects.create(
        proposal=proposal,
        constitution_version=constitution.active_version,
        outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
        risk_level=RiskLevel.LOW,
        reason="Amount exceeds auto-approve limit",
        evaluation_duration_ms=10,
        engine_version="1.0.0",
    )
    request = ApprovalRequest.objects.create(
        proposal=proposal,
        room=room,
        requested_by=user_agent,
        policy_decision=policy_decision,
        summary="Test",
    )
    return user, request


@pytest.mark.django_db(transaction=True)
class TestApprovalConcurrency:
    def test_concurrent_approve_prevented_by_lock(self) -> None:
        """Two threads try to approve simultaneously — only one succeeds."""
        user, request = _setup_approval_scenario("concurrent@example.com", "NEG-CONCURRENT-001")

        successes = []
        errors = []

        def approve(request_id, user_id, result_list, error_list):
            try:
                time.sleep(0.05)
                req = ApprovalRequest.objects.get(id=request_id)
                usr = User.objects.get(id=user_id)
                process_approval_decision(
                    request=req,
                    user=usr,
                    decision=ApprovalStatus.APPROVED,
                    comment="Concurrent test",
                )
                result_list.append("success")
            except ApprovalAlreadyDecidedError as e:
                error_list.append(f"ApprovalAlreadyDecidedError: {e}")
            except Exception as e:
                error_list.append(f"Other error: {type(e).__name__}: {e}")

        thread1 = threading.Thread(target=approve, args=(request.id, user.id, successes, errors))
        thread2 = threading.Thread(target=approve, args=(request.id, user.id, successes, errors))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        assert len(successes) == 1, f"successes={successes}, errors={errors}"
        assert len(errors) == 1
        assert "ApprovalAlreadyDecidedError" in errors[0]

        request.refresh_from_db()
        assert request.status == ApprovalStatus.APPROVED

        decisions = ApprovalDecision.objects.filter(request=request)
        assert decisions.count() == 1

    def test_concurrent_approve_and_reject(self) -> None:
        """One thread approves, another rejects — only one succeeds."""
        user, request = _setup_approval_scenario("concurrent2@example.com", "NEG-CONCURRENT-002")

        successes = []
        errors = []

        def approve(request_id, user_id, result_list, error_list):
            try:
                time.sleep(0.05)
                req = ApprovalRequest.objects.get(id=request_id)
                usr = User.objects.get(id=user_id)
                process_approval_decision(request=req, user=usr, decision=ApprovalStatus.APPROVED)
                result_list.append("approve")
            except Exception as e:
                error_list.append(f"approve: {type(e).__name__}: {e}")

        def reject(request_id, user_id, result_list, error_list):
            try:
                time.sleep(0.05)
                req = ApprovalRequest.objects.get(id=request_id)
                usr = User.objects.get(id=user_id)
                process_approval_decision(request=req, user=usr, decision=ApprovalStatus.REJECTED)
                result_list.append("reject")
            except Exception as e:
                error_list.append(f"reject: {type(e).__name__}: {e}")

        thread1 = threading.Thread(target=approve, args=(request.id, user.id, successes, errors))
        thread2 = threading.Thread(target=reject, args=(request.id, user.id, successes, errors))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        assert len(successes) == 1, f"successes={successes}, errors={errors}"
        assert len(errors) == 1

        request.refresh_from_db()
        assert request.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]
