"""Policy Engine Service layer.

This module provides the Django-integrated service that bridges the pure
policy engine with database models, loading active rules and executing
deterministic evaluations.
"""

from __future__ import annotations

import uuid
from typing import Any

from apps.policies.engine.core import assess_risk, evaluate_policy
from apps.policies.engine.types import (
    PolicyDecision,
    ProposedAction,
    RiskLevel,
)
from apps.policies.models import PolicyRule


class PolicyEngineService:
    """Service layer for policy engine operations.

    This class integrates the pure policy engine with Django models,
    providing high-level operations for policy evaluation.
    """

    @staticmethod
    def evaluate_action(
        action_type: str,
        target_resource: str,
        payload: dict[str, Any],
        actor_id: uuid.UUID,
        constitution_id: uuid.UUID | None = None,
    ) -> PolicyDecision:
        """Evaluate a proposed action against active policy rules.

        Args:
            action_type: The type of action being proposed.
            target_resource: The resource or entity the action targets.
            payload: Arbitrary data associated with the action.
            actor_id: The UUID of the user or agent proposing the action.
            constitution_id: Optional UUID of the constitution to scope rules.

        Returns:
            PolicyDecision with the deterministic outcome.
        """
        action = ProposedAction(
            action_type=action_type,
            target_resource=target_resource,
            payload=payload,
            actor_id=actor_id,
        )

        rules = PolicyEngineService._load_active_rules(constitution_id)
        return evaluate_policy(action, rules)

    @staticmethod
    def assess_action_risk(
        action_type: str,
        target_resource: str,
        payload: dict[str, Any],
        actor_id: uuid.UUID,
        constitution_id: uuid.UUID | None = None,
    ) -> RiskLevel:
        """Assess the risk level of a proposed action.

        Args:
            action_type: The type of action being proposed.
            target_resource: The resource or entity the action targets.
            payload: Arbitrary data associated with the action.
            actor_id: The UUID of the user or agent proposing the action.
            constitution_id: Optional UUID of the constitution to scope rules.

        Returns:
            The maximum risk level from all matching rules.
        """
        action = ProposedAction(
            action_type=action_type,
            target_resource=target_resource,
            payload=payload,
            actor_id=actor_id,
        )

        rules = PolicyEngineService._load_active_rules(constitution_id)
        return assess_risk(action, rules)

    @staticmethod
    def _load_active_rules(constitution_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        """Load active policy rules from the database.

        Args:
            constitution_id: Optional UUID to scope rules to a specific constitution.

        Returns:
            List of rule dictionaries suitable for the policy engine.
        """
        queryset = PolicyRule.objects.filter(is_active=True)

        if constitution_id is not None:
            queryset = queryset.filter(constitution_id=constitution_id)

        queryset = queryset.order_by("priority", "created_at")

        return [PolicyEngineService._rule_to_dict(rule) for rule in queryset]

    @staticmethod
    def _rule_to_dict(rule: PolicyRule) -> dict[str, Any]:
        """Convert a PolicyRule model instance to a dictionary.

        Args:
            rule: PolicyRule model instance.

        Returns:
            Dictionary representation suitable for the policy engine.
        """
        return {
            "id": str(rule.id),
            "name": rule.name,
            "condition": rule.condition,
            "action_type": rule.action_type,
            "risk_level": rule.risk_level,
            "priority": rule.priority,
            "requires_approval_from": rule.requires_approval_from,
        }

    @staticmethod
    def get_decision_summary(decision: PolicyDecision) -> dict[str, Any]:
        """Convert a PolicyDecision to a serializable dictionary.

        Args:
            decision: PolicyDecision instance.

        Returns:
            Dictionary representation of the decision.
        """
        return {
            "outcome": decision.outcome.value,
            "risk_level": decision.risk_level.value,
            "reason": decision.reason,
            "matched_rules": [str(rule_id) for rule_id in decision.matched_rules],
            "requires_approval_from": decision.requires_approval_from,
            "timestamp": decision.timestamp.isoformat(),
        }
