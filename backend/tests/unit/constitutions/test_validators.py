"""
Unit tests for Constitution validators.
"""

import pytest
from pydantic import ValidationError

from apps.constitutions.validators import RuleSetValidator, RuleValidator
from core.enums import RuleAction, RuleCategory, RuleOperator


class TestRuleValidator:
    def test_valid_rule(self) -> None:
        """Valid rule passes validation."""
        rule = RuleValidator(
            rule_number=1,
            name="Max amount",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
            action=RuleAction.ALLOW,
        )
        assert rule.rule_number == 1
        assert rule.name == "Max amount"

    def test_invalid_field_name(self) -> None:
        """Invalid field name raises error."""
        with pytest.raises(ValidationError):
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="invalid field!",  # Invalid character
                operator=RuleOperator.EQUALS,
                value="test",
            )

    def test_in_operator_requires_list(self) -> None:
        """IN operator requires list value."""
        with pytest.raises(ValidationError):
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="category",
                operator=RuleOperator.IN,
                value="not_a_list",  # Should be list
            )

    def test_numeric_operator_requires_number(self) -> None:
        """Numeric operators require numeric value."""
        with pytest.raises(ValidationError):
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.FINANCIAL,
                field="amount",
                operator=RuleOperator.GREATER_THAN,
                value="not_a_number",  # Should be number
            )

    def test_default_action_is_deny(self) -> None:
        """Default action is DENY."""
        rule = RuleValidator(
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
        )
        assert rule.action == RuleAction.DENY


class TestRuleSetValidator:
    def test_valid_rule_set(self) -> None:
        """Valid rule set passes validation."""
        rules = RuleSetValidator(
            rules=[
                RuleValidator(
                    rule_number=1,
                    name="Rule 1",
                    category=RuleCategory.FINANCIAL,
                    field="amount",
                    operator=RuleOperator.LESS_THAN_OR_EQUAL,
                    value=700,
                ),
                RuleValidator(
                    rule_number=2,
                    name="Rule 2",
                    category=RuleCategory.PRIVACY,
                    field="phone_number",
                    operator=RuleOperator.EQUALS,
                    value=True,
                ),
            ]
        )
        assert len(rules.rules) == 2

    def test_duplicate_rule_numbers_raises(self) -> None:
        """Duplicate rule numbers raise error."""
        with pytest.raises(ValidationError):
            RuleSetValidator(
                rules=[
                    RuleValidator(
                        rule_number=1,
                        name="Rule 1",
                        category=RuleCategory.FINANCIAL,
                        field="amount",
                        operator=RuleOperator.EQUALS,
                        value=100,
                    ),
                    RuleValidator(
                        rule_number=1,  # Duplicate
                        name="Rule 2",
                        category=RuleCategory.FINANCIAL,
                        field="amount",
                        operator=RuleOperator.EQUALS,
                        value=200,
                    ),
                ]
            )
