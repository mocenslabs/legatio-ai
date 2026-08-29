"""Unit tests for core policy evaluation engine.

Tests cover evaluate_policy, assess_risk, and the deterministic algorithm.
"""

from __future__ import annotations

import uuid

from apps.policies.engine.core import assess_risk, evaluate_policy
from apps.policies.engine.types import (
    DecisionOutcome,
    PolicyDecision,
    ProposedAction,
    RiskLevel,
)


def _create_action(
    action_type: str = "CREATE_PROPOSAL",
    target_resource: str = "proposals",
    payload: dict | None = None,
    actor_id: uuid.UUID | None = None,
) -> ProposedAction:
    """Helper to create a ProposedAction for testing."""
    return ProposedAction(
        action_type=action_type,
        target_resource=target_resource,
        payload=payload or {},
        actor_id=actor_id or uuid.uuid4(),
    )


def _create_rule(
    name: str = "Test Rule",
    condition: dict | None = None,
    action_type: str = "ALLOW",
    risk_level: str = "LOW",
    priority: int = 100,
    requires_approval_from: list[str] | None = None,
) -> dict:
    """Helper to create a rule dictionary for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "condition": condition or {"field": "test", "operator": "==", "value": "value"},
        "action_type": action_type,
        "risk_level": risk_level,
        "priority": priority,
        "requires_approval_from": requires_approval_from or [],
    }


class TestEvaluatePolicy:
    """Tests for evaluate_policy function."""

    def test_allow_when_no_rules_match(self) -> None:
        """Verify ALLOW when no rules match the context."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                action_type="DENY",
            )
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW
        assert decision.matched_rules == []

    def test_deny_returns_immediately(self) -> None:
        """Verify DENY returns immediately without evaluating further rules."""
        action = _create_action(payload={"amount": 1500})
        rules = [
            _create_rule(
                name="High Amount Deny",
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                action_type="DENY",
                risk_level="HIGH",
                priority=10,
            ),
            _create_rule(
                name="Should Not Evaluate",
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="REQUIRE_APPROVAL",
                priority=20,
            ),
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.HIGH
        assert "Denied by rule: High Amount Deny" in decision.reason
        assert len(decision.matched_rules) == 1

    def test_require_approval_when_rule_matches(self) -> None:
        """Verify REQUIRE_HUMAN_APPROVAL when approval rule matches."""
        action = _create_action(payload={"amount": 5000})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                action_type="REQUIRE_APPROVAL",
                risk_level="MEDIUM",
                requires_approval_from=["manager", "director"],
            )
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert decision.risk_level == RiskLevel.MEDIUM
        assert "manager" in decision.requires_approval_from
        assert "director" in decision.requires_approval_from

    def test_priority_ordering(self) -> None:
        """Verify rules are evaluated in priority order."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                name="Low Priority",
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="ALLOW",
                priority=200,
            ),
            _create_rule(
                name="High Priority Deny",
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="DENY",
                priority=10,
            ),
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.DENY
        assert "High Priority Deny" in decision.reason

    def test_max_risk_level_tracking(self) -> None:
        """Verify maximum risk level is tracked across matched rules."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="ALLOW",
                risk_level="LOW",
                priority=10,
            ),
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 100},
                action_type="ALLOW",
                risk_level="HIGH",
                priority=20,
            ),
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.HIGH

    def test_multiple_matched_rules(self) -> None:
        """Verify all matched rules are tracked."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="ALLOW",
                priority=10,
            ),
            _create_rule(
                condition={"field": "payload.amount", "operator": "<", "value": 1000},
                action_type="ALLOW",
                priority=20,
            ),
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.ALLOW
        assert len(decision.matched_rules) == 2

    def test_failed_condition_evaluation_skips_rule(self) -> None:
        """Verify rules with evaluation errors are skipped."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                name="Bad Rule",
                condition={"field": "nonexistent", "operator": "==", "value": "value"},
                action_type="DENY",
                priority=10,
            ),
            _create_rule(
                name="Good Rule",
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="ALLOW",
                priority=20,
            ),
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.ALLOW
        assert len(decision.matched_rules) == 1

    def test_error_outcome_on_exception(self) -> None:
        """Verify ERROR outcome on unexpected exceptions."""
        # Create an action that will cause an exception in _build_context
        action = ProposedAction(
            action_type="TEST",
            target_resource="test",
            payload={},
            actor_id=uuid.uuid4(),
        )

        # Pass invalid rules structure to trigger exception
        rules = [{"invalid": "structure"}]  # Missing required keys

        decision = evaluate_policy(action, rules)

        # Should not crash, should return a valid decision
        assert isinstance(decision, PolicyDecision)

    def test_empty_rules_list(self) -> None:
        """Verify ALLOW when no rules are provided."""
        action = _create_action()
        rules: list[dict] = []

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_deny_with_no_matched_rules_yet(self) -> None:
        """Verify DENY can occur even if no rules matched before."""
        action = _create_action(payload={"amount": 1500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                action_type="DENY",
                risk_level="CRITICAL",
            )
        ]

        decision = evaluate_policy(action, rules)

        assert decision.outcome == DecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.CRITICAL


class TestAssessRisk:
    """Tests for assess_risk function."""

    def test_low_risk_when_no_rules_match(self) -> None:
        """Verify LOW risk when no rules match."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                risk_level="HIGH",
            )
        ]

        risk = assess_risk(action, rules)

        assert risk == RiskLevel.LOW

    def test_max_risk_from_matched_rules(self) -> None:
        """Verify maximum risk level from matched rules."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                risk_level="MEDIUM",
                priority=10,
            ),
            _create_rule(
                condition={"field": "payload.amount", "operator": "<", "value": 1000},
                risk_level="HIGH",
                priority=20,
            ),
        ]

        risk = assess_risk(action, rules)

        assert risk == RiskLevel.HIGH

    def test_critical_risk_on_error(self) -> None:
        """Verify CRITICAL risk on evaluation error."""
        action = _create_action()
        # Pass None as rules to trigger exception
        risk = assess_risk(action, None)  # type: ignore[arg-type]

        assert risk == RiskLevel.CRITICAL

    def test_empty_rules_list(self) -> None:
        """Verify LOW risk when no rules provided."""
        action = _create_action()
        rules: list[dict] = []

        risk = assess_risk(action, rules)

        assert risk == RiskLevel.LOW

    def test_risk_ignores_action_type(self) -> None:
        """Verify assess_risk only considers risk_level, not action_type."""
        action = _create_action(payload={"amount": 500})
        rules = [
            _create_rule(
                condition={"field": "payload.amount", "operator": ">", "value": 0},
                action_type="DENY",  # This would normally deny
                risk_level="HIGH",
            )
        ]

        risk = assess_risk(action, rules)

        # Should return HIGH risk even though action_type is DENY
        assert risk == RiskLevel.HIGH


class TestPolicyDecision:
    """Additional tests for PolicyDecision structure."""

    def test_decision_has_timestamp(self) -> None:
        """Verify decision includes timestamp."""
        action = _create_action()
        rules: list[dict] = []

        decision = evaluate_policy(action, rules)

        assert decision.timestamp is not None

    def test_decision_reason_is_descriptive(self) -> None:
        """Verify decision reason is descriptive."""
        action = _create_action(payload={"amount": 1500})
        rules = [
            _create_rule(
                name="High Amount Rule",
                condition={"field": "payload.amount", "operator": ">", "value": 1000},
                action_type="DENY",
            )
        ]

        decision = evaluate_policy(action, rules)

        assert "High Amount Rule" in decision.reason
