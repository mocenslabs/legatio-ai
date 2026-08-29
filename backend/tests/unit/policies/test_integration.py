"""Integration and performance tests for the policy engine.

Tests cover real database integration and performance benchmarks.
"""

from __future__ import annotations

import time
import uuid

import pytest

from apps.constitutions.models import Constitution
from apps.policies.engine.core import assess_risk, evaluate_policy
from apps.policies.engine.types import (
    DecisionOutcome,
    ProposedAction,
    RiskLevel,
)
from apps.policies.models import PolicyRule, RuleActionType


def _rule_to_dict(rule: PolicyRule) -> dict:
    """Convert a PolicyRule model instance to a dictionary for the engine.

    Args:
        rule: PolicyRule model instance.

    Returns:
        Dictionary representation suitable for evaluate_policy.
    """
    return {
        "id": str(rule.id),
        "name": rule.name,
        "condition": rule.condition,
        "action_type": rule.action_type,
        "risk_level": rule.risk_level,
        "priority": rule.priority,
        "requires_approval_from": rule.requires_approval_from,
    }


@pytest.mark.django_db
class TestPolicyEngineIntegration:
    """Integration tests using real database models."""

    def test_evaluate_with_database_rules(self) -> None:
        """Verify policy evaluation works with rules from database."""
        # Create test data
        constitution = Constitution.objects.create(name="Test Constitution")

        # Create rules (no need to assign to variables)
        PolicyRule.objects.create(
            name="Low Amount Allow",
            condition={"field": "payload.amount", "operator": "<=", "value": 1000},
            action_type=RuleActionType.ALLOW,
            risk_level="LOW",
            priority=10,
            constitution=constitution,
        )

        PolicyRule.objects.create(
            name="High Amount Require Approval",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="MEDIUM",
            priority=20,
            requires_approval_from=["manager"],
            constitution=constitution,
        )

        # Test low amount (should ALLOW)
        action_low = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 500},
            actor_id=uuid.uuid4(),
        )

        rules = [_rule_to_dict(r) for r in PolicyRule.objects.filter(constitution=constitution)]
        decision_low = evaluate_policy(action_low, rules)

        assert decision_low.outcome == DecisionOutcome.ALLOW
        assert decision_low.risk_level == RiskLevel.LOW

        # Test high amount (should REQUIRE_APPROVAL)
        action_high = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            actor_id=uuid.uuid4(),
        )

        decision_high = evaluate_policy(action_high, rules)

        assert decision_high.outcome == DecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert decision_high.risk_level == RiskLevel.MEDIUM
        assert "manager" in decision_high.requires_approval_from

    def test_deny_rule_from_database(self) -> None:
        """Verify DENY rules work correctly from database."""
        rule = PolicyRule.objects.create(
            name="Forbidden Action",
            condition={"field": "action_type", "operator": "==", "value": "DELETE"},
            action_type=RuleActionType.DENY,
            risk_level="CRITICAL",
            priority=1,
        )

        action = ProposedAction(
            action_type="DELETE",
            target_resource="proposals",
            payload={},
            actor_id=uuid.uuid4(),
        )

        rules = [_rule_to_dict(rule)]
        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.CRITICAL
        assert "Forbidden Action" in decision.reason

    def test_assess_risk_with_database_rules(self) -> None:
        """Verify risk assessment works with database rules."""
        PolicyRule.objects.create(
            name="Medium Risk",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.ALLOW,
            risk_level="MEDIUM",
            priority=10,
        )

        PolicyRule.objects.create(
            name="High Risk",
            condition={"field": "payload.amount", "operator": ">", "value": 5000},
            action_type=RuleActionType.ALLOW,
            risk_level="HIGH",
            priority=20,
        )

        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 10000},
            actor_id=uuid.uuid4(),
        )

        rules = [_rule_to_dict(r) for r in PolicyRule.objects.all()]
        risk = assess_risk(action, rules)

        assert risk == RiskLevel.HIGH

    def test_only_active_rules_evaluated(self) -> None:
        """Verify only active rules are evaluated."""
        active_rule = PolicyRule.objects.create(
            name="Active Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
            is_active=True,
        )

        # Create inactive rule (no need to assign to variable)
        PolicyRule.objects.create(
            name="Inactive Rule",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.ALLOW,
            risk_level="LOW",
            priority=20,
            is_active=False,
        )

        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 100},
            actor_id=uuid.uuid4(),
        )

        # Only load active rules
        active_rules = [_rule_to_dict(r) for r in PolicyRule.objects.filter(is_active=True)]

        decision = evaluate_policy(action, active_rules)

        # Should be DENY because only active_rule is evaluated
        assert decision.outcome == DecisionOutcome.DENY
        assert len(decision.matched_rules) == 1
        assert uuid.UUID(str(active_rule.id)) in decision.matched_rules


class TestPolicyEnginePerformance:
    """Performance tests for the policy engine."""

    def test_evaluate_100_rules_under_50ms(self) -> None:
        """Verify evaluation of 100 rules completes in under 50ms."""
        # Generate 100 rules
        rules = []
        for i in range(100):
            rules.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Rule {i}",
                    "condition": {
                        "field": "payload.amount",
                        "operator": ">",
                        "value": i * 100,
                    },
                    "action_type": "ALLOW" if i % 2 == 0 else "DENY",
                    "risk_level": "LOW" if i < 50 else "HIGH",
                    "priority": i,
                    "requires_approval_from": [],
                }
            )

        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            actor_id=uuid.uuid4(),
        )

        # Warm up (first call might be slower due to imports)
        evaluate_policy(action, rules)

        # Measure performance
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            evaluate_policy(action, rules)

        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000

        # Assert performance requirement
        assert avg_time_ms < 50, f"Average evaluation time {avg_time_ms:.2f}ms exceeds 50ms limit"

    def test_assess_risk_performance(self) -> None:
        """Verify risk assessment is fast."""
        rules = []
        for i in range(100):
            rules.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Rule {i}",
                    "condition": {
                        "field": "payload.amount",
                        "operator": ">",
                        "value": i * 100,
                    },
                    "action_type": "ALLOW",
                    "risk_level": "LOW" if i < 50 else "HIGH",
                    "priority": i,
                    "requires_approval_from": [],
                }
            )

        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 5000},
            actor_id=uuid.uuid4(),
        )

        # Warm up
        assess_risk(action, rules)

        # Measure performance
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            assess_risk(action, rules)

        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000

        # Risk assessment should be even faster than full evaluation
        assert (
            avg_time_ms < 50
        ), f"Average risk assessment time {avg_time_ms:.2f}ms exceeds 50ms limit"

    def test_complex_conditions_performance(self) -> None:
        """Verify performance with complex nested conditions."""
        rules = []
        for i in range(50):
            rules.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Complex Rule {i}",
                    "condition": {
                        "field": f"payload.level{i}.value",
                        "operator": ">",
                        "value": i * 10,
                    },
                    "action_type": "ALLOW",
                    "risk_level": "MEDIUM",
                    "priority": i,
                    "requires_approval_from": [],
                }
            )

        # Create deeply nested payload
        payload = {}
        for i in range(50):
            payload[f"level{i}"] = {"value": i * 20}

        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload=payload,
            actor_id=uuid.uuid4(),
        )

        # Warm up
        evaluate_policy(action, rules)

        # Measure performance
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            evaluate_policy(action, rules)

        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000

        assert avg_time_ms < 50, f"Complex evaluation time {avg_time_ms:.2f}ms exceeds 50ms limit"
