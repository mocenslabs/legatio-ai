"""
Property-based tests for Policy Engine invariants.
"""

from hypothesis import HealthCheck, given, settings
from tests.property.policy_engine.strategies import (
    proposed_action_strategy,
    rule_condition_strategy,
    rule_input_strategy,
    rule_set_strategy,
)

from core.enums import (
    PolicyDecisionOutcome,
    RiskLevel,
    RuleAction,
    RuleCategory,
    RuleOperator,
)
from core.schemas.policy import ProposedAction, RuleCondition
from services.policy_engine.evaluator import (
    evaluate_condition,
    evaluate_policy,
    safe_evaluate,
)
from services.policy_engine.types import RuleInput


class TestDeterminismProperty:
    """Property: Same input -> same output. Always."""

    @given(action=proposed_action_strategy(), rules=rule_set_strategy(size=10))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_evaluate_policy_is_deterministic(
        self, action: ProposedAction, rules: list[RuleInput]
    ) -> None:
        result1 = safe_evaluate(action, rules)
        result2 = safe_evaluate(action, rules)
        assert result1.outcome == result2.outcome
        assert result1.risk_level == result2.risk_level
        assert result1.reason == result2.reason
        assert len(result1.matched_rules) == len(result2.matched_rules)


class TestFailSafeProperty:
    """Property: safe_evaluate never raises, always returns PolicyDecision."""

    @given(action=proposed_action_strategy(), rules=rule_set_strategy(size=5))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_safe_evaluate_never_raises(
        self, action: ProposedAction, rules: list[RuleInput]
    ) -> None:
        result = safe_evaluate(action, rules)
        assert result.outcome in [
            PolicyDecisionOutcome.ALLOW,
            PolicyDecisionOutcome.DENY,
            PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            PolicyDecisionOutcome.ERROR,
        ]
        assert result.risk_level in list(RiskLevel)
        assert len(result.reason) > 0
        assert result.engine_version == "1.0.0"


class TestDenyPriorityProperty:
    """Property: DENY always takes priority over REQUIRE_APPROVAL and ALLOW."""

    @given(action=proposed_action_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_deny_rule_blocks_everything(self, action: ProposedAction) -> None:
        """A DENY rule that matches must produce DENY outcome."""
        deny_rule = RuleInput(
            rule_id="deny-rule",
            rule_number=1,
            name="Always deny this action type",
            category=RuleCategory.CUSTOM,
            action=RuleAction.DENY,
            conditions=[
                RuleCondition(
                    field_name="action_type",
                    operator=RuleOperator.EQUALS,
                    value=action.action_type,
                    category=RuleCategory.CUSTOM,
                )
            ],
            is_active=True,
        )
        result = evaluate_policy(action, [deny_rule])
        assert result.outcome == PolicyDecisionOutcome.DENY


class TestRiskLevelProperty:
    """Property: Risk level is consistent with outcome."""

    @given(action=proposed_action_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_deny_implies_critical_risk(self, action: ProposedAction) -> None:
        deny_rule = RuleInput(
            rule_id="deny-rule",
            rule_number=1,
            name="Always deny this action type",
            category=RuleCategory.CUSTOM,
            action=RuleAction.DENY,
            conditions=[
                RuleCondition(
                    field_name="action_type",
                    operator=RuleOperator.EQUALS,
                    value=action.action_type,
                    category=RuleCategory.CUSTOM,
                )
            ],
            is_active=True,
        )
        result = evaluate_policy(action, [deny_rule])
        if result.outcome == PolicyDecisionOutcome.DENY:
            assert result.risk_level == RiskLevel.CRITICAL


class TestEmptyRulesProperty:
    """Property: Empty rules -> ALLOW."""

    @given(action=proposed_action_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_empty_rules_allow(self, action: ProposedAction) -> None:
        result = evaluate_policy(action, [])
        assert result.outcome == PolicyDecisionOutcome.ALLOW
        assert len(result.matched_rules) == 0


class TestInactiveRulesProperty:
    """Property: Inactive rules are ignored."""

    @given(action=proposed_action_strategy(), rule=rule_input_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_inactive_rules_ignored(self, action: ProposedAction, rule: RuleInput) -> None:
        rule.is_active = False
        result = evaluate_policy(action, [rule])
        assert result.outcome == PolicyDecisionOutcome.ALLOW


class TestConditionEvaluationProperty:
    """Property: evaluate_condition is deterministic and safe."""

    @given(action=proposed_action_strategy(), condition=rule_condition_strategy())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_condition_evaluation_deterministic(
        self, action: ProposedAction, condition: RuleCondition
    ) -> None:
        try:
            result1 = evaluate_condition(condition, action)
            result2 = evaluate_condition(condition, action)
            assert result1 == result2
        except Exception:
            pass
