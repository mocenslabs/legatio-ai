"""
Internal types for the Policy Engine evaluator.

These types are independent of Django models and allow the evaluator
to be tested in pure Python without a database.

Source: 04-BUSINESS-FLOW.md Section 7
"""

from pydantic import BaseModel, ConfigDict, Field

from core.enums import RuleAction, RuleCategory
from core.schemas.policy import RuleCondition


class RuleInput(BaseModel):
    """
    Internal representation of a policy rule for evaluation.

    This is the input type consumed by evaluate_policy().
    It is intentionally decoupled from the Django PolicyRule model
    to allow pure unit testing without database access.
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., min_length=1, description="UUID of the rule")
    rule_number: int = Field(..., ge=1, description="Display number for ordering")
    name: str = Field(..., min_length=1, description="Human-readable rule name")
    category: RuleCategory = Field(..., description="Category of the rule")
    action: RuleAction = Field(..., description="Action when rule matches")
    conditions: list[RuleCondition] = Field(
        ...,
        min_length=1,
        description="List of conditions (AND logic)",
    )
    is_active: bool = Field(default=True, description="Whether the rule is active")
