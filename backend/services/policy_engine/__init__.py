"""
Policy Engine — The Heart of Legatio AI.

Deterministic policy evaluation. No LLM. No randomness.
Same input → same output. Always.
"""

from services.policy_engine.evaluator import (
    assess_risk,
    evaluate_condition,
    evaluate_policy,
    safe_evaluate,
)
from services.policy_engine.types import RuleInput

__all__ = [
    "evaluate_policy",
    "evaluate_condition",
    "assess_risk",
    "safe_evaluate",
    "RuleInput",
]
