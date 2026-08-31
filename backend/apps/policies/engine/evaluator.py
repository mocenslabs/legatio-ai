"""Condition evaluator for the Policy Engine.

This module provides deterministic evaluation of JSON-based conditions against
execution contexts. All evaluations are pure functions with no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    """Result of a safe condition evaluation.

    Attributes:
        success: Whether the evaluation completed without errors.
        result: The boolean result of the condition (only valid if success=True).
        error: Error message if evaluation failed (only valid if success=False).
    """

    success: bool
    result: bool
    error: str | None = None


def evaluate_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluate a JSON condition against a context.

    The condition must have the structure:
    {
        "field": "path.to.field",
        "operator": "==|!=|>|<|>=|<=|in|not_in|contains|exists",
        "value": <expected_value>  # optional for 'exists' operator
    }

    Args:
        condition: JSON structure defining the condition to evaluate.
        context: Dictionary containing the data to evaluate against.

    Returns:
        True if the condition is satisfied, False otherwise.

    Raises:
        ValueError: If the condition structure is invalid.
        KeyError: If the field path doesn't exist in the context.
        TypeError: If the operator is not supported.
    """
    field_path: str = condition["field"]
    operator: str = condition["operator"]
    expected_value: Any = condition.get("value")

    # Extract the actual value from context using dot notation
    actual_value = _extract_field_value(field_path, context)

    # Evaluate based on operator - wrap in bool() to satisfy mypy strict
    if operator == "==":
        return bool(actual_value == expected_value)
    if operator == "!=":
        return bool(actual_value != expected_value)
    if operator == ">":
        return bool(actual_value > expected_value)
    if operator == "<":
        return bool(actual_value < expected_value)
    if operator == ">=":
        return bool(actual_value >= expected_value)
    if operator == "<=":
        return bool(actual_value <= expected_value)
    if operator == "in":
        return bool(actual_value in expected_value)
    if operator == "not_in":
        return bool(actual_value not in expected_value)
    if operator == "contains":
        return bool(expected_value in actual_value)
    if operator == "exists":
        return bool(actual_value is not None)

    raise TypeError(f"Unsupported operator: {operator}")


def _extract_field_value(field_path: str, context: dict[str, Any]) -> Any:
    """Extract a value from context using dot notation path.

    Args:
        field_path: Dot-separated path (e.g., "user.profile.age").
        context: Dictionary to extract value from.

    Returns:
        The value at the specified path.

    Raises:
        KeyError: If any part of the path doesn't exist.
    """
    keys = field_path.split(".")
    current: Any = context

    for key in keys:
        if not isinstance(current, dict):
            raise KeyError(f"Cannot access '{key}' on non-dict value at '{field_path}'")
        if key not in current:
            raise KeyError(f"Field '{key}' not found in path '{field_path}'")
        current = current[key]

    return current


def safe_evaluate(condition: dict[str, Any], context: dict[str, Any]) -> EvaluationResult:
    """Safely evaluate a condition, catching all exceptions.

    This wrapper ensures that any error during evaluation is captured and
    returned as a structured result, preventing the policy engine from crashing.

    Args:
        condition: JSON structure defining the condition to evaluate.
        context: Dictionary containing the data to evaluate against.

    Returns:
        EvaluationResult with success=False and error message if evaluation fails.
    """
    try:
        result = evaluate_condition(condition, context)
        return EvaluationResult(success=True, result=result)
    except (KeyError, TypeError, ValueError) as e:
        return EvaluationResult(success=False, result=False, error=str(e))
    except Exception as e:  # noqa: BLE001
        # Catch-all for unexpected errors, but log them in production
        return EvaluationResult(success=False, result=False, error=f"Unexpected error: {str(e)}")
