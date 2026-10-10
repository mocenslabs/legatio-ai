"""
Pydantic validators for Constitution rules.

Ensures that rules are valid before persistence.

Source: 03-DATA-MODEL.md Section 8.3
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.enums import RuleAction, RuleCategory, RuleOperator


class RuleValidator(BaseModel):
    """
    Validator for a single PolicyRule.

    Ensures that the rule has valid fields, operator, and value types.
    """

    model_config = ConfigDict(extra="forbid")

    rule_number: int = Field(..., ge=1, description="Display number for the rule")
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    category: RuleCategory
    field: str = Field(..., min_length=1, max_length=100)
    operator: RuleOperator
    value: Any = Field(..., description="Typed value (number, string, list, boolean)")
    action: RuleAction = Field(default=RuleAction.DENY)
    priority: int = Field(default=100, ge=1)
    is_active: bool = Field(default=True)

    @field_validator("field")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Validate that field name is not empty and is a valid identifier."""
        v = v.strip()
        if not v:
            raise ValueError("Field name cannot be empty")
        # Allow alphanumeric, underscore, and hyphen
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "Field name must contain only alphanumeric characters, underscores, or hyphens"
            )
        return v

    @field_validator("value")
    @classmethod
    def validate_value_type(cls, v: Any, info: Any) -> Any:
        """Validate that value type is compatible with operator."""
        if v is None:
            raise ValueError("Value cannot be None")

        # For IN and NOT_IN operators, value must be a list
        if info.data.get("operator") in (RuleOperator.IN, RuleOperator.NOT_IN):
            if not isinstance(v, list):
                raise ValueError("IN and NOT_IN operators require a list value")
            if len(v) == 0:
                raise ValueError("List value cannot be empty")

        # For CONTAINS and NOT_CONTAINS, value should be a string
        if info.data.get("operator") in (
            RuleOperator.CONTAINS,
            RuleOperator.NOT_CONTAINS,
        ) and not isinstance(v, str):
            # Allow conversion to string
            return str(v)

        # For numeric operators, value should be numeric
        if info.data.get("operator") in (
            RuleOperator.GREATER_THAN,
            RuleOperator.GREATER_THAN_OR_EQUAL,
            RuleOperator.LESS_THAN,
            RuleOperator.LESS_THAN_OR_EQUAL,
        ) and not isinstance(v, int | float):
            raise ValueError(f"Operator {info.data.get('operator')} requires a numeric value")

        return v


class ConstitutionValidator(BaseModel):
    """Validator for Constitution creation/update."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ConstitutionVersionValidator(BaseModel):
    """Validator for ConstitutionVersion creation."""

    model_config = ConfigDict(extra="forbid")

    version_number: int = Field(..., ge=1)


class RuleSetValidator(BaseModel):
    """Validator for a set of rules in a constitution version."""

    model_config = ConfigDict(extra="forbid")

    rules: list[RuleValidator] = Field(default_factory=list)

    @field_validator("rules")
    @classmethod
    def validate_unique_rule_numbers(cls, v: list[RuleValidator]) -> list[RuleValidator]:
        """Ensure all rule numbers are unique within the version."""
        rule_numbers = [r.rule_number for r in v]
        if len(rule_numbers) != len(set(rule_numbers)):
            raise ValueError("Rule numbers must be unique within a version")
        return v
