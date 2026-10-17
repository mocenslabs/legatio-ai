"""
Policy Engine Evaluator — The Heart of Legatio AI.
Deterministic policy evaluation. No LLM. No randomness.
Same input → same output. Always.
Source: 04-BUSINESS-FLOW.md Section 7
"""

import logging
import time
from decimal import Decimal, InvalidOperation
from typing import Any

from core.constants import (
    ENGINE_VERSION,
    RISK_CRITICAL_AMOUNT_THRESHOLD,
    RISK_HIGH_AMOUNT_THRESHOLD,
)
from core.enums import PolicyDecisionOutcome, RiskLevel, RuleAction, RuleOperator
from core.exceptions import InvalidActionError, InvalidRuleError
from core.schemas.policy import MatchedRule, PolicyDecision, ProposedAction, RuleCondition
from services.policy_engine.types import RuleInput

logger = logging.getLogger("legatio.policy_engine")


# =============================================================================
# Public API
# =============================================================================


def safe_evaluate(action: ProposedAction, rules: list[RuleInput]) -> PolicyDecision:
    """
    Fail-safe wrapper around evaluate_policy.
    Never raises exceptions. On any error, returns a PolicyDecision
    with outcome=ERROR and risk_level=CRITICAL.
    Source: 04-BUSINESS-FLOW.md Section 7.4 and 11.1
    """
    try:
        return evaluate_policy(action, rules)
    except Exception as exc:
        logger.exception("Policy evaluation failed unexpectedly")
        return PolicyDecision(
            outcome=PolicyDecisionOutcome.ERROR,
            risk_level=RiskLevel.CRITICAL,
            reason=f"Policy evaluation failed: {exc}",
            matched_rules=[],
            evaluation_duration_ms=0,
            engine_version=ENGINE_VERSION,
        )


def evaluate_policy(action: ProposedAction, rules: list[RuleInput]) -> PolicyDecision:
    """
    Deterministic policy evaluation.
    Evaluates a ProposedAction against a list of rules and returns
    a PolicyDecision. DENY has immediate priority.
    Source: 04-BUSINESS-FLOW.md Section 7.1
    """
    start_time = time.monotonic()

    if not isinstance(action, ProposedAction):
        raise InvalidActionError("action must be a ProposedAction instance")

    active_rules = sorted(
        [r for r in rules if r.is_active],
        key=lambda r: r.rule_number,
    )

    matched_rules: list[MatchedRule] = []
    has_require_approval = False

    for rule in active_rules:
        if _rule_matches(rule, action):
            matched_rules.append(
                MatchedRule(
                    rule_id=rule.rule_id,
                    rule_number=rule.rule_number,
                    name=rule.name,
                    action=rule.action,
                    triggered_by=_build_trigger_explanation(rule, action),
                )
            )

            if rule.action == RuleAction.DENY:
                duration_ms = _elapsed_ms(start_time)
                return PolicyDecision(
                    outcome=PolicyDecisionOutcome.DENY,
                    risk_level=assess_risk(action, matched_rules),
                    reason=f"Blocked by Rule #{rule.rule_number}: {rule.name}",
                    matched_rules=matched_rules,
                    evaluation_duration_ms=duration_ms,
                    engine_version=ENGINE_VERSION,
                )

            if rule.action == RuleAction.REQUIRE_APPROVAL:
                has_require_approval = True

    duration_ms = _elapsed_ms(start_time)
    risk_level = assess_risk(action, matched_rules)

    if has_require_approval:
        return PolicyDecision(
            outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=risk_level,
            reason=_build_approval_reason(matched_rules, action),
            matched_rules=matched_rules,
            evaluation_duration_ms=duration_ms,
            engine_version=ENGINE_VERSION,
        )

    return PolicyDecision(
        outcome=PolicyDecisionOutcome.ALLOW,
        risk_level=risk_level,
        reason="All policy checks passed",
        matched_rules=matched_rules,
        evaluation_duration_ms=duration_ms,
        engine_version=ENGINE_VERSION,
    )


def evaluate_condition(condition: RuleCondition, action: ProposedAction) -> bool:
    """
    Evaluate a single rule condition against a proposed action.
    Source: 04-BUSINESS-FLOW.md Section 7.2
    """
    field_value = _get_field_value(condition.field_name, action)
    operator = condition.operator
    target_value = condition.value

    try:
        if operator == RuleOperator.EQUALS:
            return _compare_equals(field_value, target_value)
        if operator == RuleOperator.NOT_EQUALS:
            return not _compare_equals(field_value, target_value)
        if operator == RuleOperator.GREATER_THAN:
            return _compare_numeric(field_value, target_value, lambda a, b: a > b)
        if operator == RuleOperator.GREATER_THAN_OR_EQUAL:
            return _compare_numeric(field_value, target_value, lambda a, b: a >= b)
        if operator == RuleOperator.LESS_THAN:
            return _compare_numeric(field_value, target_value, lambda a, b: a < b)
        if operator == RuleOperator.LESS_THAN_OR_EQUAL:
            return _compare_numeric(field_value, target_value, lambda a, b: a <= b)
        if operator == RuleOperator.CONTAINS:
            return _compare_contains(field_value, target_value)
        if operator == RuleOperator.NOT_CONTAINS:
            return not _compare_contains(field_value, target_value)
        if operator == RuleOperator.IN:
            return _compare_in(field_value, target_value)
        if operator == RuleOperator.NOT_IN:
            return not _compare_in(field_value, target_value)
        raise InvalidRuleError(f"Unknown operator: {operator}")
    except (TypeError, InvalidOperation) as exc:
        raise InvalidRuleError(
            f"Cannot evaluate condition '{condition.field_name} {operator} {target_value}': {exc}"
        ) from exc


def assess_risk(action: ProposedAction, matched_rules: list[MatchedRule]) -> RiskLevel:
    """
    Assess the risk level of a proposed action based on matched rules.
    Source: 04-BUSINESS-FLOW.md Section 7.3
    """
    if any(r.action == RuleAction.DENY for r in matched_rules):
        return RiskLevel.CRITICAL

    if action.amount is not None:
        if action.amount >= RISK_CRITICAL_AMOUNT_THRESHOLD:
            return RiskLevel.CRITICAL
        if action.amount >= RISK_HIGH_AMOUNT_THRESHOLD:
            return RiskLevel.HIGH

    if any(r.action == RuleAction.REQUIRE_APPROVAL for r in matched_rules):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


# =============================================================================
# Internal helpers
# =============================================================================


def _rule_matches(rule: RuleInput, action: ProposedAction) -> bool:
    """Check if all conditions of a rule match (AND logic).

    Rules that reference unknown ProposedAction fields are skipped
    (treated as non-matching) so a single bad rule does not abort
    the whole negotiation round.
    """
    try:
        return all(evaluate_condition(condition, action) for condition in rule.conditions)
    except InvalidRuleError:
        return False


def _get_field_value(field_name: str, action: ProposedAction) -> Any:
    """
    Extract a field value from ProposedAction by name.
    Falls back to metadata for unknown field names.
    """
    known_fields = {
        "action_type",
        "amount",
        "currency",
        "data_fields_requested",
        "contract_length_months",
        "auto_renewal",
        "category",
        "is_new_vendor",
        "price_increase_pct",
    }

    if field_name in known_fields:
        return getattr(action, field_name)

    if field_name in action.metadata:
        return action.metadata[field_name]

    raise InvalidRuleError(f"Unknown field: '{field_name}'")


def _to_decimal(value: Any) -> Decimal:
    """Convert a value to Decimal for numeric comparison."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _compare_equals(field_value: Any, target_value: Any) -> bool:
    """Compare two values for equality with Decimal support."""
    if field_value is None and target_value is None:
        return True
    if field_value is None or target_value is None:
        return False

    try:
        return _to_decimal(field_value) == _to_decimal(target_value)
    except (InvalidOperation, ValueError):
        pass

    return str(field_value) == str(target_value)


def _compare_numeric(
    field_value: Any,
    target_value: Any,
    comparator: Any,
) -> bool:
    """Compare two values numerically. Returns False if field_value is None or types incompatible."""
    if field_value is None:
        return False
    try:
        return bool(comparator(_to_decimal(field_value), _to_decimal(target_value)))
    except (InvalidOperation, ValueError, TypeError):
        return False


def _compare_contains(field_value: Any, target_value: Any) -> bool:
    """Check if target_value is contained in field_value."""
    if field_value is None:
        return False
    if isinstance(field_value, list):
        target_str = str(target_value)
        return bool(any(target_str == str(v) for v in field_value))
    return str(target_value) in str(field_value)


def _compare_in(field_value: Any, target_value: Any) -> bool:
    """Check if field_value is in target_value (which should be a list)."""
    if field_value is None:
        return False
    if not isinstance(target_value, list):
        raise InvalidRuleError(f"IN operator requires a list, got {type(target_value)}")

    field_str = str(field_value)
    return bool(any(field_str == str(v) for v in target_value))


def _elapsed_ms(start_time: float) -> int:
    """Calculate elapsed time in milliseconds."""
    return int((time.monotonic() - start_time) * 1000)


def _build_trigger_explanation(rule: RuleInput, action: ProposedAction) -> str:
    """Build a human-readable explanation of why a rule triggered."""
    parts = []
    for condition in rule.conditions:
        field_value = _get_field_value(condition.field_name, action)
        parts.append(
            f"{condition.field_name} ({field_value}) " f"{condition.operator} {condition.value}"
        )
    return " AND ".join(parts)


def _build_approval_reason(matched_rules: list[MatchedRule], action: ProposedAction) -> str:
    """Build a human-readable reason for REQUIRE_HUMAN_APPROVAL."""
    rule_names = [
        f"Rule #{r.rule_number}" for r in matched_rules if r.action == RuleAction.REQUIRE_APPROVAL
    ]
    amount_info = f" (amount: {action.amount} {action.currency})" if action.amount else ""
    return f"Requires human approval per {', '.join(rule_names)}{amount_info}"
