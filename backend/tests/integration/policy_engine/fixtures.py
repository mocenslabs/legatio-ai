"""
Integration test fixtures for the 3 MVP use cases.
Source: 04-BUSINESS-FLOW.md Sections 4-6
"""

from core.enums import RuleAction, RuleCategory, RuleOperator
from core.schemas.policy import RuleCondition
from services.policy_engine.types import RuleInput


def make_rule(
    rule_id: str,
    rule_number: int,
    name: str,
    category: RuleCategory,
    field: str,
    operator: RuleOperator,
    value: object,
    action: RuleAction,
) -> RuleInput:
    """Helper to create a RuleInput from a single condition."""
    return RuleInput(
        rule_id=rule_id,
        rule_number=rule_number,
        name=name,
        category=category,
        action=action,
        conditions=[
            RuleCondition(field_name=field, operator=operator, value=value, category=category)
        ],
    )


def travel_constitution_rules() -> list[RuleInput]:
    """Constitution for travel negotiation (Use Case 1)."""
    return [
        make_rule(
            rule_id="travel-rule-1",
            rule_number=1,
            name="Max transaction amount",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
            action=RuleAction.ALLOW,
        ),
        make_rule(
            rule_id="travel-rule-17",
            rule_number=17,
            name="Never share phone number",
            category=RuleCategory.PRIVACY,
            field="data_fields_requested",
            operator=RuleOperator.CONTAINS,
            value="phone_number",
            action=RuleAction.DENY,
        ),
        make_rule(
            rule_id="travel-rule-23",
            rule_number=23,
            name="Large payments need approval",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.GREATER_THAN,
            value=200,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
        make_rule(
            rule_id="travel-rule-31",
            rule_number=31,
            name="Email sharing allowed",
            category=RuleCategory.PRIVACY,
            field="data_fields_requested",
            operator=RuleOperator.CONTAINS,
            value="email",
            action=RuleAction.ALLOW,
        ),
    ]


def subscription_constitution_rules() -> list[RuleInput]:
    """Constitution for subscription negotiation (Use Case 2)."""
    return [
        make_rule(
            rule_id="sub-rule-1",
            rule_number=1,
            name="Max monthly spend",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=100,
            action=RuleAction.ALLOW,
        ),
        make_rule(
            rule_id="sub-rule-5",
            rule_number=5,
            name="Require approval over 50",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.GREATER_THAN,
            value=50,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
        make_rule(
            rule_id="sub-rule-12",
            rule_number=12,
            name="Max contract length",
            category=RuleCategory.NEGOTIATION,
            field="contract_length_months",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=12,
            action=RuleAction.ALLOW,
        ),
        make_rule(
            rule_id="sub-rule-15",
            rule_number=15,
            name="Auto-renewal requires approval",
            category=RuleCategory.NEGOTIATION,
            field="auto_renewal",
            operator=RuleOperator.EQUALS,
            value=True,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
        make_rule(
            rule_id="sub-rule-20",
            rule_number=20,
            name="Price increase requires approval",
            category=RuleCategory.FINANCIAL,
            field="price_increase_pct",
            operator=RuleOperator.GREATER_THAN,
            value=10,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
    ]


def purchase_constitution_rules() -> list[RuleInput]:
    """Constitution for purchase approval (Use Case 3)."""
    return [
        make_rule(
            rule_id="pur-rule-1",
            rule_number=1,
            name="Max transaction",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=50,
            action=RuleAction.ALLOW,
        ),
        make_rule(
            rule_id="pur-rule-5",
            rule_number=5,
            name="Require approval over 20",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.GREATER_THAN,
            value=20,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
        make_rule(
            rule_id="pur-rule-8",
            rule_number=8,
            name="Allowed categories",
            category=RuleCategory.CUSTOM,
            field="category",
            operator=RuleOperator.IN,
            value=["books", "electronics"],
            action=RuleAction.ALLOW,
        ),
        make_rule(
            rule_id="pur-rule-10",
            rule_number=10,
            name="Prohibited categories",
            category=RuleCategory.CUSTOM,
            field="category",
            operator=RuleOperator.IN,
            value=["gambling"],
            action=RuleAction.DENY,
        ),
        make_rule(
            rule_id="pur-rule-15",
            rule_number=15,
            name="New vendor requires approval",
            category=RuleCategory.CUSTOM,
            field="is_new_vendor",
            operator=RuleOperator.EQUALS,
            value=True,
            action=RuleAction.REQUIRE_APPROVAL,
        ),
    ]
