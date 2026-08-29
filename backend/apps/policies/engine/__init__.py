"""Policy Engine module.

Exposes core domain types and evaluation functions for policy evaluation.
"""

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
    "evaluate_condition",
    "safe_evaluate",
]
