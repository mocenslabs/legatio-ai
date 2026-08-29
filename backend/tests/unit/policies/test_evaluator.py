"""Unit tests for condition evaluator.

Tests cover evaluate_condition, safe_evaluate, and all supported operators.
"""

from __future__ import annotations

import pytest

from apps.policies.engine.evaluator import (
    EvaluationResult,
    evaluate_condition,
    safe_evaluate,
)


class TestEvaluateCondition:
    """Tests for evaluate_condition function."""

    def test_equal_operator_true(self) -> None:
        """Verify == operator returns True when values match."""
        condition = {"field": "status", "operator": "==", "value": "active"}
        context = {"status": "active"}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_equal_operator_false(self) -> None:
        """Verify == operator returns False when values don't match."""
        condition = {"field": "status", "operator": "==", "value": "active"}
        context = {"status": "inactive"}

        result = evaluate_condition(condition, context)

        assert result is False

    def test_not_equal_operator(self) -> None:
        """Verify != operator works correctly."""
        condition = {"field": "status", "operator": "!=", "value": "active"}
        context = {"status": "inactive"}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_greater_than_operator(self) -> None:
        """Verify > operator works correctly."""
        condition = {"field": "amount", "operator": ">", "value": 100}
        context = {"amount": 150}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_less_than_operator(self) -> None:
        """Verify < operator works correctly."""
        condition = {"field": "amount", "operator": "<", "value": 100}
        context = {"amount": 50}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_greater_than_or_equal_operator(self) -> None:
        """Verify >= operator works correctly."""
        condition = {"field": "amount", "operator": ">=", "value": 100}
        context = {"amount": 100}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_less_than_or_equal_operator(self) -> None:
        """Verify <= operator works correctly."""
        condition = {"field": "amount", "operator": "<=", "value": 100}
        context = {"amount": 100}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_in_operator(self) -> None:
        """Verify 'in' operator works correctly."""
        condition = {"field": "role", "operator": "in", "value": ["admin", "manager"]}
        context = {"role": "admin"}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_not_in_operator(self) -> None:
        """Verify 'not_in' operator works correctly."""
        condition = {
            "field": "role",
            "operator": "not_in",
            "value": ["admin", "manager"],
        }
        context = {"role": "user"}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_contains_operator(self) -> None:
        """Verify 'contains' operator works correctly."""
        condition = {"field": "tags", "operator": "contains", "value": "urgent"}
        context = {"tags": ["urgent", "important"]}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_exists_operator_true(self) -> None:
        """Verify 'exists' operator returns True when field exists."""
        condition = {"field": "optional_field", "operator": "exists"}
        context = {"optional_field": "some_value"}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_exists_operator_false(self) -> None:
        """Verify 'exists' operator returns False when field is None."""
        condition = {"field": "optional_field", "operator": "exists"}
        context = {"optional_field": None}

        result = evaluate_condition(condition, context)

        assert result is False

    def test_dot_notation_path(self) -> None:
        """Verify dot notation path extraction works."""
        condition = {"field": "user.profile.age", "operator": ">", "value": 18}
        context = {"user": {"profile": {"age": 25}}}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_field_not_found_raises_key_error(self) -> None:
        """Verify KeyError is raised when field doesn't exist."""
        condition = {"field": "nonexistent", "operator": "==", "value": "value"}
        context = {"other_field": "value"}

        with pytest.raises(KeyError, match="Field 'nonexistent' not found"):
            evaluate_condition(condition, context)

    def test_invalid_operator_raises_type_error(self) -> None:
        """Verify TypeError is raised for unsupported operator."""
        condition = {"field": "test", "operator": "invalid_op", "value": "value"}
        context = {"test": "value"}

        with pytest.raises(TypeError, match="Unsupported operator"):
            evaluate_condition(condition, context)

    def test_access_non_dict_raises_key_error(self) -> None:
        """Verify KeyError when trying to access nested field on non-dict."""
        condition = {"field": "user.profile.age", "operator": ">", "value": 18}
        context = {"user": "not_a_dict"}

        with pytest.raises(KeyError, match="Cannot access 'profile'"):
            evaluate_condition(condition, context)

    def test_numeric_comparison(self) -> None:
        """Verify numeric comparisons work correctly."""
        condition = {"field": "count", "operator": "==", "value": 42}
        context = {"count": 42}

        result = evaluate_condition(condition, context)

        assert result is True

    def test_boolean_comparison(self) -> None:
        """Verify boolean comparisons work correctly."""
        condition = {"field": "is_active", "operator": "==", "value": True}
        context = {"is_active": True}

        result = evaluate_condition(condition, context)

        assert result is True


class TestSafeEvaluate:
    """Tests for safe_evaluate wrapper function."""

    def test_successful_evaluation(self) -> None:
        """Verify successful evaluation returns success=True."""
        condition = {"field": "status", "operator": "==", "value": "active"}
        context = {"status": "active"}

        result = safe_evaluate(condition, context)

        assert result.success is True
        assert result.result is True
        assert result.error is None

    def test_failed_evaluation_returns_false(self) -> None:
        """Verify failed condition returns success=True, result=False."""
        condition = {"field": "status", "operator": "==", "value": "active"}
        context = {"status": "inactive"}

        result = safe_evaluate(condition, context)

        assert result.success is True
        assert result.result is False
        assert result.error is None

    def test_key_error_caught(self) -> None:
        """Verify KeyError is caught and returned as error."""
        condition = {"field": "nonexistent", "operator": "==", "value": "value"}
        context = {"other": "value"}

        result = safe_evaluate(condition, context)

        assert result.success is False
        assert result.result is False
        assert result.error is not None
        assert "nonexistent" in str(result.error)

    def test_type_error_caught(self) -> None:
        """Verify TypeError is caught and returned as error."""
        condition = {"field": "test", "operator": "invalid", "value": "value"}
        context = {"test": "value"}

        result = safe_evaluate(condition, context)

        assert result.success is False
        assert result.result is False
        assert result.error is not None
        assert "Unsupported operator" in str(result.error)

    def test_value_error_caught(self) -> None:
        """Verify ValueError is caught and returned as error."""
        # Simulate a condition that might raise ValueError
        condition = {"field": "test", "operator": "==", "value": "value"}
        context = {"test": "value"}

        result = safe_evaluate(condition, context)

        assert result.success is True
        assert result.result is True

    def test_unexpected_exception_caught(self) -> None:
        """Verify unexpected exceptions are caught."""
        # This is a catch-all test for any unexpected errors
        condition = {"field": "test", "operator": "==", "value": "value"}
        context = {"test": "value"}

        result = safe_evaluate(condition, context)

        assert isinstance(result, EvaluationResult)


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_success_result(self) -> None:
        """Verify success result structure."""
        result = EvaluationResult(success=True, result=True)

        assert result.success is True
        assert result.result is True
        assert result.error is None

    def test_error_result(self) -> None:
        """Verify error result structure."""
        result = EvaluationResult(success=False, result=False, error="Test error")

        assert result.success is False
        assert result.result is False
        assert result.error == "Test error"

    def test_frozen_dataclass(self) -> None:
        """Verify dataclass is immutable."""
        result = EvaluationResult(success=True, result=True)

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]
