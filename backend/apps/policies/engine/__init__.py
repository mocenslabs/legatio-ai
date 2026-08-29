"""Policy Engine module.

Exposes core domain types and evaluation functions for policy evaluation.
"""

from apps.policies.engine.core import assess_risk, evaluate_policy
from apps.policies.engine.evaluator import (
    EvaluationResult,
    evaluate_condition,
    safe_evaluate,
)
from apps.policies.engine.types import (
    DecisionOutcome,
    PolicyDecision,
    ProposedAction,
    RiskLevel,
)

__all__ = [
    "DecisionOutcome",
    "EvaluationResult",
    "PolicyDecision",
    "ProposedAction",
    "RiskLevel",
    "assess_risk",
    "evaluate_condition",
    "evaluate_policy",
    "safe_evaluate",
]
