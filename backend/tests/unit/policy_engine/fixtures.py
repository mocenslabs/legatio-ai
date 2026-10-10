"""Test fixtures and helpers for Policy Engine tests."""

from decimal import Decimal
from typing import Any

from core.enums import RuleAction, RuleCategory, RuleOperator
from core.schemas.policy import ProposedAction, RuleCondition
from services.policy_engine.types import RuleInput


def make_action(**overrides: Any) -> ProposedAction:
    """Create a ProposedAction with sensible defaults."""
    defaults: dict[str, Any] = {
        "action_type": "purchase",
        "amount": Decimal("100.00"),
        "currency": "EUR",
        "data_fields_requested": [],
        "auto_renewal": False,
        "is_new_vendor": False,
    }
    defaults.update(overrides)
    return ProposedAction(**defaults)


def make_rule(
    rule_id: str = "test-rule-1",
    rule_number: int = 1,
    name: str = "Test Rule",
    category: RuleCategory = RuleCategory.CUSTOM,
    action: RuleAction = RuleAction.ALLOW,
    conditions: list[RuleCondition] | None = None,
    is_active: bool = True,
) -> RuleInput:
    """Create a RuleInput with sensible defaults."""
    if conditions is None:
        conditions = [
            RuleCondition(
                field_name="amount",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=1000,
            )
        ]
    return RuleInput(
        rule_id=rule_id,
        rule_number=rule_number,
        name=name,
        category=category,
        action=action,
        conditions=conditions,
        is_active=is_active,
    )


def make_condition(
    field_name: str = "amount",
    operator: RuleOperator = RuleOperator.LESS_THAN_OR_EQUAL,
    value: object = 1000,
    category: RuleCategory = RuleCategory.CUSTOM,
) -> RuleCondition:
    """Create a RuleCondition."""
    return RuleCondition(
        field_name=field_name,
        operator=operator,
        value=value,
        category=category,
    )


def use_case_1_travel_action() -> ProposedAction:
    """Use Case 1: Travel negotiation — hotel booking."""
    return make_action(
        action_type="purchase",
        amount=Decimal("820.00"),
        currency="EUR",
        data_fields_requested=[],
        metadata={"nights": 5, "breakfast": True},
    )


def use_case_1_privacy_violation_action() -> ProposedAction:
    """Use Case 1: Action requesting phone number (should be DENIED)."""
    return make_action(
        action_type="purchase",
        amount=Decimal("680.00"),
        currency="EUR",
        data_fields_requested=["phone_number"],
    )


def use_case_2_subscription_action() -> ProposedAction:
    """Use Case 2: ISP subscription negotiation."""
    return make_action(
        action_type="subscribe",
        amount=Decimal("35.00"),
        currency="EUR",
        contract_length_months=24,
        auto_renewal=True,
        price_increase_pct=Decimal("15.0"),
    )


def use_case_3_purchase_action() -> ProposedAction:
    """Use Case 3: Online purchase."""
    return make_action(
        action_type="purchase",
        amount=Decimal("150.00"),
        currency="EUR",
        category="electronics",
        is_new_vendor=True,
    )


def rule_never_share_phone() -> RuleInput:
    """Rule #17: Never share phone number."""
    return make_rule(
        rule_id="rule-17",
        rule_number=17,
        name="Never share phone",
        category=RuleCategory.PRIVACY,
        action=RuleAction.DENY,
        conditions=[
            make_condition(
                field_name="data_fields_requested",
                operator=RuleOperator.CONTAINS,
                value="phone_number",
                category=RuleCategory.PRIVACY,
            )
        ],
    )


def rule_max_amount_700() -> RuleInput:
    """Rule #22: Max amount 700 EUR."""
    return make_rule(
        rule_id="rule-22",
        rule_number=22,
        name="Max amount 700 EUR",
        category=RuleCategory.FINANCIAL,
        action=RuleAction.DENY,
        conditions=[
            make_condition(
                field_name="amount",
                operator=RuleOperator.GREATER_THAN,
                value=700,
                category=RuleCategory.FINANCIAL,
            )
        ],
    )


def rule_require_approval_over_200() -> RuleInput:
    """Rule #23: Require approval for amounts over 200 EUR."""
    return make_rule(
        rule_id="rule-23",
        rule_number=23,
        name="Require approval over 200",
        category=RuleCategory.FINANCIAL,
        action=RuleAction.REQUIRE_APPROVAL,
        conditions=[
            make_condition(
                field_name="amount",
                operator=RuleOperator.GREATER_THAN,
                value=200,
                category=RuleCategory.FINANCIAL,
            )
        ],
    )


def rule_no_auto_renewal() -> RuleInput:
    """Rule: No auto-renewal allowed."""
    return make_rule(
        rule_id="rule-no-autorenew",
        rule_number=30,
        name="No auto-renewal",
        category=RuleCategory.NEGOTIATION,
        action=RuleAction.DENY,
        conditions=[
            make_condition(
                field_name="auto_renewal",
                operator=RuleOperator.EQUALS,
                value=True,
                category=RuleCategory.NEGOTIATION,
            )
        ],
    )


def rule_max_contract_12_months() -> RuleInput:
    """Rule: Max contract length 12 months."""
    return make_rule(
        rule_id="rule-max-contract",
        rule_number=31,
        name="Max contract 12 months",
        category=RuleCategory.NEGOTIATION,
        action=RuleAction.DENY,
        conditions=[
            make_condition(
                field_name="contract_length_months",
                operator=RuleOperator.GREATER_THAN,
                value=12,
                category=RuleCategory.NEGOTIATION,
            )
        ],
    )
