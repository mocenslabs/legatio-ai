"""
Edge case tests for the Policy Engine.
Tests boundary conditions, unusual inputs, and error scenarios.
"""

from decimal import Decimal

import pytest

from core.enums import PolicyDecisionOutcome, RuleAction, RuleOperator
from core.exceptions import InvalidRuleError
from core.schemas.policy import RuleCondition
from services.policy_engine.evaluator import evaluate_condition, evaluate_policy
from tests.unit.policy_engine.fixtures import make_action, make_rule


class TestBoundaryConditions:
    """Tests for boundary values and edge cases."""

    def test_amount_zero(self) -> None:
        """Amount = 0 should be valid."""
        action = make_action(amount=Decimal("0.00"))
        rule = make_rule(
            rule_number=1,
            action=RuleAction.ALLOW,
            conditions=[RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=0)],
        )
        decision = evaluate_policy(action, [rule])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_amount_very_large(self) -> None:
        """Very large amount should be handled."""
        action = make_action(amount=Decimal("999999999.99"))
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_empty_data_fields_list(self) -> None:
        """Empty data_fields_requested should be valid."""
        action = make_action(data_fields_requested=[])
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_many_data_fields(self) -> None:
        """Many data fields should be handled."""
        action = make_action(data_fields_requested=["email"] * 100)
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_unicode_in_metadata(self) -> None:
        """Unicode characters in metadata should be handled."""
        action = make_action(metadata={"destination": "Madrid 🇪🇸"})
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_special_characters_in_category(self) -> None:
        """Special characters in category should be handled."""
        action = make_action(category="books & more")
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW


class TestRuleOrdering:
    """Tests for rule ordering and priority."""

    def test_rules_evaluated_in_number_order(self) -> None:
        """Rules must be evaluated in rule_number order."""
        action = make_action(amount=Decimal("100.00"))
        rule_3 = make_rule(
            rule_id="rule-3",
            rule_number=3,
            action=RuleAction.DENY,
            conditions=[
                RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=100)
            ],
        )
        rule_1 = make_rule(
            rule_id="rule-1",
            rule_number=1,
            action=RuleAction.ALLOW,
            conditions=[
                RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=100)
            ],
        )
        decision = evaluate_policy(action, [rule_3, rule_1])
        assert decision.outcome == PolicyDecisionOutcome.DENY

    def test_many_rules_performance(self) -> None:
        """Many rules should not significantly impact performance."""
        action = make_action(amount=Decimal("500.00"))
        rules = [
            make_rule(
                rule_id=f"rule-{i}",
                rule_number=i,
                action=RuleAction.ALLOW,
                conditions=[
                    RuleCondition(
                        field_name="amount",
                        operator=RuleOperator.EQUALS,
                        value=999999,
                    )
                ],
            )
            for i in range(1, 1001)  # Start at 1 (rule_number >= 1)
        ]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.evaluation_duration_ms < 100


class TestMultipleConditions:
    """Tests for rules with multiple conditions (AND logic)."""

    def test_all_conditions_must_match(self) -> None:
        """All conditions in a rule must match (AND logic)."""
        action = make_action(amount=Decimal("100.00"), currency="EUR")
        rule = make_rule(
            rule_number=1,
            action=RuleAction.ALLOW,
            conditions=[
                RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=100),
                RuleCondition(field_name="currency", operator=RuleOperator.EQUALS, value="EUR"),
            ],
        )
        decision = evaluate_policy(action, [rule])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_one_condition_fails_rule_does_not_match(self) -> None:
        """If one condition fails, the rule does not match."""
        action = make_action(amount=Decimal("100.00"), currency="USD")
        rule = make_rule(
            rule_number=1,
            action=RuleAction.ALLOW,
            conditions=[
                RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=100),
                RuleCondition(field_name="currency", operator=RuleOperator.EQUALS, value="EUR"),
            ],
        )
        decision = evaluate_policy(action, [rule])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert len(decision.matched_rules) == 0


class TestMetadataFallback:
    """Tests for metadata field access."""

    def test_custom_field_in_metadata(self) -> None:
        """Custom fields should be accessible via metadata."""
        action = make_action(metadata={"destination": "Madrid"})
        condition = RuleCondition(
            field_name="destination", operator=RuleOperator.EQUALS, value="Madrid"
        )
        assert evaluate_condition(condition, action) is True

    def test_unknown_field_raises_error(self) -> None:
        """Unknown fields not in action or metadata should raise error."""
        action = make_action()
        condition = RuleCondition(
            field_name="nonexistent_field", operator=RuleOperator.EQUALS, value="value"
        )
        with pytest.raises(InvalidRuleError):
            evaluate_condition(condition, action)


class TestDecimalPrecision:
    """Tests for Decimal precision in comparisons."""

    def test_decimal_equality(self) -> None:
        """Decimal comparisons should be precise."""
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.EQUALS,
            value=Decimal("100.00"),
        )
        assert evaluate_condition(condition, action) is True

    def test_decimal_inequality(self) -> None:
        """Decimal inequality should work correctly."""
        action = make_action(amount=Decimal("100.01"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.EQUALS,
            value=Decimal("100.00"),
        )
        assert evaluate_condition(condition, action) is False

    def test_decimal_greater_than(self) -> None:
        """Decimal greater than should work correctly."""
        action = make_action(amount=Decimal("100.01"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.GREATER_THAN,
            value=Decimal("100.00"),
        )
        assert evaluate_condition(condition, action) is True
