"""Unit tests for PolicyEngineService.

Tests cover service layer integration with Django models and the policy engine.
"""

from __future__ import annotations

import uuid

import pytest

from apps.constitutions.models import Constitution
from apps.policies.engine.types import DecisionOutcome, RiskLevel
from apps.policies.models import PolicyRule, RuleActionType
from apps.policies.services import PolicyEngineService


@pytest.mark.django_db
class TestPolicyEngineService:
    """Tests for PolicyEngineService class."""

    def test_evaluate_action_with_no_rules(self) -> None:
        """Verify evaluation returns ALLOW when no active rules exist."""
        decision = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
        )

        assert decision.outcome == DecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_evaluate_action_with_deny_rule(self) -> None:
        """Verify evaluation returns DENY when deny rule matches."""
        PolicyRule.objects.create(
            name="Deny High Amount",
            condition={"field": "payload.amount", "operator": ">", "value": 5000},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
        )

        decision = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 10000},
            actor_id=uuid.uuid4(),
        )

        assert decision.outcome == DecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.HIGH

    def test_evaluate_action_with_approval_rule(self) -> None:
        """Verify evaluation returns REQUIRE_HUMAN_APPROVAL when approval rule matches."""
        PolicyRule.objects.create(
            name="Require Approval for High Amount",
            condition={"field": "payload.amount", "operator": ">", "value": 5000},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="MEDIUM",
            priority=10,
            requires_approval_from=["manager", "director"],
        )

        decision = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 10000},
            actor_id=uuid.uuid4(),
        )

        assert decision.outcome == DecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert decision.risk_level == RiskLevel.MEDIUM
        assert "manager" in decision.requires_approval_from
        assert "director" in decision.requires_approval_from

    def test_evaluate_action_with_constitution_scope(self) -> None:
        """Verify evaluation only considers rules from specified constitution."""
        constitution1 = Constitution.objects.create(name="Constitution 1")
        constitution2 = Constitution.objects.create(name="Constitution 2")

        PolicyRule.objects.create(
            name="Rule for Constitution 1",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
            constitution=constitution1,
        )

        PolicyRule.objects.create(
            name="Rule for Constitution 2",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.ALLOW,
            risk_level="LOW",
            priority=10,
            constitution=constitution2,
        )

        # Evaluate with constitution1 - should DENY
        decision1 = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
            constitution_id=constitution1.id,
        )

        assert decision1.outcome == DecisionOutcome.DENY

        # Evaluate with constitution2 - should ALLOW
        decision2 = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
            constitution_id=constitution2.id,
        )

        assert decision2.outcome == DecisionOutcome.ALLOW

    def test_evaluate_action_ignores_inactive_rules(self) -> None:
        """Verify evaluation only considers active rules."""
        PolicyRule.objects.create(
            name="Inactive Deny Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
            is_active=False,
        )

        decision = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
        )

        assert decision.outcome == DecisionOutcome.ALLOW

    def test_assess_action_risk(self) -> None:
        """Verify risk assessment returns maximum risk level."""
        PolicyRule.objects.create(
            name="Medium Risk Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.ALLOW,
            risk_level="MEDIUM",
            priority=10,
        )

        PolicyRule.objects.create(
            name="High Risk Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 500},
            action_type=RuleActionType.ALLOW,
            risk_level="HIGH",
            priority=20,
        )

        risk = PolicyEngineService.assess_action_risk(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
        )

        assert risk == RiskLevel.HIGH

    def test_get_decision_summary(self) -> None:
        """Verify decision summary serialization."""
        PolicyRule.objects.create(
            name="Test Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
        )

        decision = PolicyEngineService.evaluate_action(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 1000},
            actor_id=uuid.uuid4(),
        )

        summary = PolicyEngineService.get_decision_summary(decision)

        assert summary["outcome"] == "DENY"
        assert summary["risk_level"] == "HIGH"
        assert "reason" in summary
        assert "matched_rules" in summary
        assert "requires_approval_from" in summary
        assert "timestamp" in summary
        assert isinstance(summary["matched_rules"], list)
        assert isinstance(summary["requires_approval_from"], list)
