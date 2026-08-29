"""Core policy evaluation engine.

This module implements the deterministic policy evaluation algorithm that
processes proposed actions against a set of policy rules to produce decisions.
"""

from __future__ import annotations

import uuid
from typing import Any

from apps.policies.engine.evaluator import safe_evaluate
from apps.policies.engine.types import (
    DecisionOutcome,
    PolicyDecision,
    ProposedAction,
    RiskLevel,
)


def evaluate_policy(
    action: ProposedAction,
    rules: list[dict[str, Any]],
) -> PolicyDecision:
    """Evaluate a proposed action against a set of policy rules.

    Algorithm:
    1. For each rule (sorted by priority): evaluate condition.
    2. If any rule DENYs → return DENY immediately.
    3. If any rule requires approval → mark for approval.
    4. If no DENY and no approval required → ALLOW.
    5. If approval required → REQUIRE_HUMAN_APPROVAL.
    6. Any exception → ERROR outcome (fail-safe).

    Args:
        action: The proposed action to evaluate.
        rules: List of policy rule dictionaries with keys:
            - id: UUID of the rule
            - condition: JSON condition to evaluate
            - action_type: "ALLOW", "DENY", or "REQUIRE_APPROVAL"
            - risk_level: "LOW", "MEDIUM", "HIGH", or "CRITICAL"
            - requires_approval_from: List of roles/users for approval

    Returns:
        PolicyDecision with the deterministic outcome.
    """
    try:
        # Build context from action
        context = _build_context(action)

        # Sort rules by priority (lower = higher priority)
        sorted_rules = sorted(rules, key=lambda r: r.get("priority", 100))

        matched_rules: list[uuid.UUID] = []
        requires_approval = False
        approval_from: list[str] = []
        max_risk = RiskLevel.LOW
        deny_reason = ""

        # Evaluate each rule
        for rule in sorted_rules:
            condition = rule.get("condition", {})
            eval_result = safe_evaluate(condition, context)

            # Skip rules that fail to evaluate or don't match
            if not eval_result.success or not eval_result.result:
                continue

            # Rule matched
            rule_id = rule.get("id")
            if rule_id:
                matched_rules.append(uuid.UUID(str(rule_id)))

            action_type = rule.get("action_type", "ALLOW")
            rule_risk = rule.get("risk_level", "LOW")

            # Update max risk level
            max_risk = _get_higher_risk(max_risk, RiskLevel(rule_risk))

            # DENY → immediate return (fail-fast)
            if action_type == "DENY":
                deny_reason = f"Denied by rule: {rule.get('name', 'unnamed')}"
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    risk_level=max_risk,
                    reason=deny_reason,
                    matched_rules=matched_rules,
                )

            # REQUIRE_APPROVAL → mark for approval
            if action_type == "REQUIRE_APPROVAL":
                requires_approval = True
                approval_from.extend(rule.get("requires_approval_from", []))

        # No DENY found
        if requires_approval:
            return PolicyDecision(
                outcome=DecisionOutcome.REQUIRE_HUMAN_APPROVAL,
                risk_level=max_risk,
                reason="Action requires human approval",
                matched_rules=matched_rules,
                requires_approval_from=approval_from,
            )

        # Default: ALLOW
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=max_risk,
            reason="Action allowed by policy",
            matched_rules=matched_rules,
        )

    except Exception as e:  # noqa: BLE001
        # Fail-safe: any unexpected error → ERROR outcome
        return PolicyDecision(
            outcome=DecisionOutcome.ERROR,
            risk_level=RiskLevel.CRITICAL,
            reason=f"Policy evaluation error: {str(e)}",
        )


def _build_context(action: ProposedAction) -> dict[str, Any]:
    """Build evaluation context from a proposed action.

    Args:
        action: The proposed action.

    Returns:
        Dictionary context for condition evaluation.
    """
    return {
        "action_type": action.action_type,
        "target_resource": action.target_resource,
        "actor_id": str(action.actor_id),
        "payload": action.payload,
    }


def _get_higher_risk(current: RiskLevel, new: RiskLevel) -> RiskLevel:
    """Return the higher risk level between two values.

    Args:
        current: Current risk level.
        new: New risk level to compare.

    Returns:
        The higher risk level.
    """
    risk_order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    return new if risk_order[new] > risk_order[current] else current


def assess_risk(
    action: ProposedAction,
    rules: list[dict[str, Any]],
) -> RiskLevel:
    """Assess the risk level of a proposed action without full evaluation.

    This is a lightweight function that only determines risk level,
    useful for quick risk assessments without full policy evaluation.

    Args:
        action: The proposed action to assess.
        rules: List of policy rule dictionaries.

    Returns:
        The maximum risk level from all matching rules.
    """
    try:
        context = _build_context(action)
        max_risk = RiskLevel.LOW

        for rule in rules:
            condition = rule.get("condition", {})
            eval_result = safe_evaluate(condition, context)

            if eval_result.success and eval_result.result:
                rule_risk = rule.get("risk_level", "LOW")
                max_risk = _get_higher_risk(max_risk, RiskLevel(rule_risk))

        return max_risk

    except Exception:  # noqa: BLE001
        # Fail-safe: any error → CRITICAL risk
        return RiskLevel.CRITICAL
