"""
Operator matrix tests for the Policy Engine.
Tests all 10 operators with various data types to ensure complete coverage.
Source: 03-DATA-MODEL.md Section 5.6 (RuleOperator)
"""

from decimal import Decimal

from core.enums import RuleOperator
from core.schemas.policy import RuleCondition
from services.policy_engine.evaluator import evaluate_condition
from tests.unit.policy_engine.fixtures import make_action


class TestOperatorMatrix:
    """Comprehensive tests for all 10 operators."""

    # =========================================================================
    # EQUALS
    # =========================================================================
    def test_equals_numeric(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(field_name="amount", operator=RuleOperator.EQUALS, value=100)
        assert evaluate_condition(condition, action) is True

    def test_equals_string(self) -> None:
        action = make_action(currency="EUR")
        condition = RuleCondition(field_name="currency", operator=RuleOperator.EQUALS, value="EUR")
        assert evaluate_condition(condition, action) is True

    def test_equals_boolean(self) -> None:
        action = make_action(auto_renewal=True)
        condition = RuleCondition(
            field_name="auto_renewal", operator=RuleOperator.EQUALS, value=True
        )
        assert evaluate_condition(condition, action) is True

    def test_equals_none_field_value(self) -> None:
        """When field value is None, EQUALS against a non-None target returns False."""
        action = make_action(category=None)
        condition = RuleCondition(
            field_name="category", operator=RuleOperator.EQUALS, value="electronics"
        )
        # None != "electronics" → False
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # NOT_EQUALS
    # =========================================================================
    def test_not_equals_numeric(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(field_name="amount", operator=RuleOperator.NOT_EQUALS, value=200)
        assert evaluate_condition(condition, action) is True

    def test_not_equals_string(self) -> None:
        action = make_action(currency="EUR")
        condition = RuleCondition(
            field_name="currency", operator=RuleOperator.NOT_EQUALS, value="USD"
        )
        assert evaluate_condition(condition, action) is True

    # =========================================================================
    # GREATER_THAN
    # =========================================================================
    def test_gt_numeric(self) -> None:
        action = make_action(amount=Decimal("200.00"))
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.GREATER_THAN, value=100
        )
        assert evaluate_condition(condition, action) is True

    def test_gt_equal_returns_false(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.GREATER_THAN, value=100
        )
        assert evaluate_condition(condition, action) is False

    def test_gt_none_returns_false(self) -> None:
        action = make_action(amount=None)
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.GREATER_THAN, value=100
        )
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # GREATER_THAN_OR_EQUAL
    # =========================================================================
    def test_gte_greater(self) -> None:
        action = make_action(amount=Decimal("200.00"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL,
            value=100,
        )
        assert evaluate_condition(condition, action) is True

    def test_gte_equal(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL,
            value=100,
        )
        assert evaluate_condition(condition, action) is True

    def test_gte_less_returns_false(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.GREATER_THAN_OR_EQUAL,
            value=100,
        )
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # LESS_THAN
    # =========================================================================
    def test_lt_numeric(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        condition = RuleCondition(field_name="amount", operator=RuleOperator.LESS_THAN, value=100)
        assert evaluate_condition(condition, action) is True

    def test_lt_equal_returns_false(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(field_name="amount", operator=RuleOperator.LESS_THAN, value=100)
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # LESS_THAN_OR_EQUAL
    # =========================================================================
    def test_lte_less(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.LESS_THAN_OR_EQUAL, value=100
        )
        assert evaluate_condition(condition, action) is True

    def test_lte_equal(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.LESS_THAN_OR_EQUAL, value=100
        )
        assert evaluate_condition(condition, action) is True

    def test_lte_greater_returns_false(self) -> None:
        action = make_action(amount=Decimal("200.00"))
        condition = RuleCondition(
            field_name="amount", operator=RuleOperator.LESS_THAN_OR_EQUAL, value=100
        )
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # CONTAINS
    # =========================================================================
    def test_contains_list(self) -> None:
        action = make_action(data_fields_requested=["email", "phone_number"])
        condition = RuleCondition(
            field_name="data_fields_requested",
            operator=RuleOperator.CONTAINS,
            value="phone_number",
        )
        assert evaluate_condition(condition, action) is True

    def test_contains_not_in_list(self) -> None:
        action = make_action(data_fields_requested=["email"])
        condition = RuleCondition(
            field_name="data_fields_requested",
            operator=RuleOperator.CONTAINS,
            value="phone_number",
        )
        assert evaluate_condition(condition, action) is False

    def test_contains_empty_list(self) -> None:
        action = make_action(data_fields_requested=[])
        condition = RuleCondition(
            field_name="data_fields_requested",
            operator=RuleOperator.CONTAINS,
            value="phone_number",
        )
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # NOT_CONTAINS
    # =========================================================================
    def test_not_contains_list(self) -> None:
        action = make_action(data_fields_requested=["email"])
        condition = RuleCondition(
            field_name="data_fields_requested",
            operator=RuleOperator.NOT_CONTAINS,
            value="phone_number",
        )
        assert evaluate_condition(condition, action) is True

    def test_not_contains_in_list(self) -> None:
        action = make_action(data_fields_requested=["phone_number"])
        condition = RuleCondition(
            field_name="data_fields_requested",
            operator=RuleOperator.NOT_CONTAINS,
            value="phone_number",
        )
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # IN
    # =========================================================================
    def test_in_list(self) -> None:
        action = make_action(category="books")
        condition = RuleCondition(
            field_name="category",
            operator=RuleOperator.IN,
            value=["books", "electronics"],
        )
        assert evaluate_condition(condition, action) is True

    def test_in_not_in_list(self) -> None:
        action = make_action(category="clothing")
        condition = RuleCondition(
            field_name="category",
            operator=RuleOperator.IN,
            value=["books", "electronics"],
        )
        assert evaluate_condition(condition, action) is False

    def test_in_none_returns_false(self) -> None:
        action = make_action(category=None)
        condition = RuleCondition(field_name="category", operator=RuleOperator.IN, value=["books"])
        assert evaluate_condition(condition, action) is False

    # =========================================================================
    # NOT_IN
    # =========================================================================
    def test_not_in_list(self) -> None:
        action = make_action(category="clothing")
        condition = RuleCondition(
            field_name="category",
            operator=RuleOperator.NOT_IN,
            value=["books", "electronics"],
        )
        assert evaluate_condition(condition, action) is True

    def test_not_in_in_list(self) -> None:
        action = make_action(category="books")
        condition = RuleCondition(
            field_name="category",
            operator=RuleOperator.NOT_IN,
            value=["books", "electronics"],
        )
        assert evaluate_condition(condition, action) is False
