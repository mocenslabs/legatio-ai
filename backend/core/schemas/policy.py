"""
Pydantic schemas for the Policy Engine.
These schemas define the contract between the Policy Engine and the rest
of the system. They are the input/output types for evaluate_policy().
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.enums import (
    PolicyDecisionOutcome,
    RiskLevel,
    RuleAction,
    RuleCategory,
    RuleOperator,
)


# =============================================================================
# Input: ProposedAction
# =============================================================================
class ProposedAction(BaseModel):
    """
    Input to the Policy Engine.
    Represents a proposed action from an agent that needs to be evaluated
    against the active constitution.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    action_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of action (e.g., 'purchase', 'share_data', 'subscribe')",
    )
    amount: Decimal | None = Field(
        default=None,
        ge=0,
        description="Monetary amount involved in the action",
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
    )
    data_fields_requested: list[str] = Field(
        default_factory=list,
        description="List of data fields the action requests (e.g., ['phone_number'])",
    )
    contract_length_months: int | None = Field(
        default=None,
        ge=0,
        description="Contract length in months, if applicable",
    )
    auto_renewal: bool = Field(
        default=False,
        description="Whether the action involves auto-renewal",
    )
    category: str | None = Field(
        default=None,
        description="Category of the action (e.g., 'books', 'electronics')",
    )
    is_new_vendor: bool = Field(
        default=False,
        description="Whether this is a new vendor",
    )
    price_increase_pct: Decimal | None = Field(
        default=None,
        ge=0,
        description="Price increase percentage, if applicable",
    )
    terms: dict[str, Any] | None = Field(
        default=None,
        description="Additional structured terms of the proposal",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for custom rules",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency is uppercase ISO 4217."""
        if v is not None:
            v = v.upper()
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Currency must be a 3-letter ISO 4217 code")
        return v

    @field_validator("data_fields_requested")
    @classmethod
    def validate_data_fields(cls, v: list[str]) -> list[str]:
        """Validate data fields are non-empty strings."""
        return [field.strip() for field in v if field.strip()]


# =============================================================================
# Output: PolicyDecision
# =============================================================================
class MatchedRule(BaseModel):
    """
    A rule that matched during policy evaluation.
    Included in PolicyDecision to provide explainability.
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="UUID of the matched rule")
    rule_number: int = Field(..., ge=1, description="Display number of the rule")
    name: str = Field(..., min_length=1, description="Human-readable name")
    action: RuleAction = Field(..., description="Action of the matched rule")
    triggered_by: str = Field(
        ...,
        min_length=1,
        description="Human-readable description of what triggered the rule",
    )


class PolicyDecision(BaseModel):
    """
    Output from the Policy Engine.
    Represents the result of evaluating a ProposedAction against a set of rules.
    """

    model_config = ConfigDict(extra="forbid")

    outcome: PolicyDecisionOutcome = Field(
        ...,
        description="Final decision: ALLOW, DENY, REQUIRE_HUMAN_APPROVAL, or ERROR",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Overall risk level: LOW, MEDIUM, HIGH, or CRITICAL",
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the decision",
    )
    matched_rules: list[MatchedRule] = Field(
        default_factory=list,
        description="List of rules that matched during evaluation",
    )
    evaluation_duration_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to evaluate in milliseconds",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the evaluation was performed",
    )
    engine_version: str = Field(
        default="1.0.0",
        description="Version of the Policy Engine that performed the evaluation",
    )


# =============================================================================
# Rule definitions (used by loader and tests)
# =============================================================================
class RuleCondition(BaseModel):
    """
    A single condition within a rule.
    Rules can have multiple conditions (AND logic).
    """

    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(
        ...,
        min_length=1,
        description="Name of the ProposedAction field to evaluate",
    )
    operator: RuleOperator = Field(
        ...,
        description="Comparison operator",
    )
    value: Any = Field(
        ...,
        description="Value to compare against",
    )
    category: RuleCategory = Field(
        default=RuleCategory.CUSTOM,
        description="Category of the rule this condition belongs to",
    )

    @field_validator("value")
    @classmethod
    def validate_value_not_none(cls, v: Any) -> Any:
        """Reject None values."""
        if v is None:
            raise ValueError("Rule condition value cannot be None")
        return v


class RuleInput(BaseModel):
    """
    A rule as loaded by the Policy Engine.
    Used by evaluate_policy() to check against ProposedActions.
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="UUID of the rule")
    rule_number: int = Field(..., ge=1, description="Display number of the rule")
    name: str = Field(..., min_length=1, description="Human-readable name")
    category: RuleCategory = Field(..., description="Category of the rule")
    action: RuleAction = Field(..., description="Action to take if rule matches")
    conditions: list[RuleCondition] = Field(
        ...,
        min_length=1,
        description="List of conditions (AND logic)",
    )
    priority: int = Field(
        default=0,
        description="Priority for rule ordering (higher = evaluated first)",
    )
