"""
Unit tests for evaluate_condition.

Source: 04-BUSINESS-FLOW.md Section 7.2
"""

from decimal import Decimal

import pytest

from core.enums import RuleOperator
from core.exceptions import InvalidRuleError
from services.policy_engine.evaluator import evaluate_condition
from tests.unit.policy_engine.fixtures import make_action, make_condition


class TestEqualsOperator:
    def test_equals_match(self) -> None:
        action = make_action(amount=Decimal("700.00"))
        cond = make_condition("amount", RuleOperator.EQUALS, 700)
        assert evaluate_condition(cond, action) is True

    def test_equals_no_match(self) -> None:
        action = make_action(amount=Decimal("800.00"))
        cond = make_condition("amount", RuleOperator.EQUALS, 700)
        assert evaluate_condition(cond, action) is False

    def test_equals_boolean(self) -> None:
        action = make_action(auto_renewal=True)
        cond = make_condition("auto_renewal", RuleOperator.EQUALS, True)
        assert evaluate_condition(cond, action) is True

    def test_equals_none_field(self) -> None:
        action = make_action(category=None)
        cond = make_condition("category", RuleOperator.EQUALS, "electronics")
        assert evaluate_condition(cond, action) is False


class TestNotEqualsOperator:
    def test_not_equals_match(self) -> None:
        action = make_action(currency="EUR")
        cond = make_condition("currency", RuleOperator.NOT_EQUALS, "USD")
        assert evaluate_condition(cond, action) is True

    def test_not_equals_no_match(self) -> None:
        action = make_action(currency="EUR")
        cond = make_condition("currency", RuleOperator.NOT_EQUALS, "EUR")
        assert evaluate_condition(cond, action) is False


class TestGreaterThanOperator:
    def test_gt_match(self) -> None:
        action = make_action(amount=Decimal("820.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN, 700)
        assert evaluate_condition(cond, action) is True

    def test_gt_no_match_equal(self) -> None:
        action = make_action(amount=Decimal("700.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN, 700)
        assert evaluate_condition(cond, action) is False

    def test_gt_no_match_less(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN, 700)
        assert evaluate_condition(cond, action) is False

    def test_gt_none_field_returns_false(self) -> None:
        action = make_action(amount=None)
        cond = make_condition("amount", RuleOperator.GREATER_THAN, 700)
        assert evaluate_condition(cond, action) is False


class TestGreaterThanOrEqualOperator:
    def test_gte_match_greater(self) -> None:
        action = make_action(amount=Decimal("800.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is True

    def test_gte_match_equal(self) -> None:
        action = make_action(amount=Decimal("700.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is True

    def test_gte_no_match(self) -> None:
        action = make_action(amount=Decimal("699.00"))
        cond = make_condition("amount", RuleOperator.GREATER_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is False


class TestLessThanOperator:
    def test_lt_match(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        cond = make_condition("amount", RuleOperator.LESS_THAN, 700)
        assert evaluate_condition(cond, action) is True

    def test_lt_no_match_equal(self) -> None:
        action = make_action(amount=Decimal("700.00"))
        cond = make_condition("amount", RuleOperator.LESS_THAN, 700)
        assert evaluate_condition(cond, action) is False

    def test_lt_none_field_returns_false(self) -> None:
        action = make_action(amount=None)
        cond = make_condition("amount", RuleOperator.LESS_THAN, 700)
        assert evaluate_condition(cond, action) is False


class TestLessThanOrEqualOperator:
    def test_lte_match_less(self) -> None:
        action = make_action(amount=Decimal("699.00"))
        cond = make_condition("amount", RuleOperator.LESS_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is True

    def test_lte_match_equal(self) -> None:
        action = make_action(amount=Decimal("700.00"))
        cond = make_condition("amount", RuleOperator.LESS_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is True

    def test_lte_no_match(self) -> None:
        action = make_action(amount=Decimal("701.00"))
        cond = make_condition("amount", RuleOperator.LESS_THAN_OR_EQUAL, 700)
        assert evaluate_condition(cond, action) is False


class TestContainsOperator:
    def test_contains_match(self) -> None:
        action = make_action(data_fields_requested=["phone_number", "email"])
        cond = make_condition("data_fields_requested", RuleOperator.CONTAINS, "phone_number")
        assert evaluate_condition(cond, action) is True

    def test_contains_no_match(self) -> None:
        action = make_action(data_fields_requested=["email"])
        cond = make_condition("data_fields_requested", RuleOperator.CONTAINS, "phone_number")
        assert evaluate_condition(cond, action) is False

    def test_contains_empty_list(self) -> None:
        action = make_action(data_fields_requested=[])
        cond = make_condition("data_fields_requested", RuleOperator.CONTAINS, "phone_number")
        assert evaluate_condition(cond, action) is False

    def test_contains_none_field_treated_as_empty(self) -> None:
        action = make_action(category=None)
        cond = make_condition("category", RuleOperator.CONTAINS, "electronics")
        assert evaluate_condition(cond, action) is False


class TestNotContainsOperator:
    def test_not_contains_match(self) -> None:
        action = make_action(data_fields_requested=["email"])
        cond = make_condition("data_fields_requested", RuleOperator.NOT_CONTAINS, "phone_number")
        assert evaluate_condition(cond, action) is True

    def test_not_contains_no_match(self) -> None:
        action = make_action(data_fields_requested=["phone_number"])
        cond = make_condition("data_fields_requested", RuleOperator.NOT_CONTAINS, "phone_number")
        assert evaluate_condition(cond, action) is False


class TestInOperator:
    def test_in_match(self) -> None:
        action = make_action(category="electronics")
        cond = make_condition("category", RuleOperator.IN, ["books", "electronics"])
        assert evaluate_condition(cond, action) is True

    def test_in_no_match(self) -> None:
        action = make_action(category="gambling")
        cond = make_condition("category", RuleOperator.IN, ["books", "electronics"])
        assert evaluate_condition(cond, action) is False

    def test_in_none_field_returns_false(self) -> None:
        action = make_action(category=None)
        cond = make_condition("category", RuleOperator.IN, ["books"])
        assert evaluate_condition(cond, action) is False


class TestNotInOperator:
    def test_not_in_match(self) -> None:
        action = make_action(category="electronics")
        cond = make_condition("category", RuleOperator.NOT_IN, ["gambling", "alcohol"])
        assert evaluate_condition(cond, action) is True

    def test_not_in_no_match(self) -> None:
        action = make_action(category="gambling")
        cond = make_condition("category", RuleOperator.NOT_IN, ["gambling", "alcohol"])
        assert evaluate_condition(cond, action) is False


class TestMetadataFallback:
    def test_metadata_field_access(self) -> None:
        action = make_action(metadata={"destination": "Madrid"})
        cond = make_condition("destination", RuleOperator.EQUALS, "Madrid")
        assert evaluate_condition(cond, action) is True

    def test_unknown_field_raises(self) -> None:
        action = make_action()
        cond = make_condition("nonexistent_field", RuleOperator.EQUALS, "value")
        with pytest.raises(InvalidRuleError):
            evaluate_condition(cond, action)
