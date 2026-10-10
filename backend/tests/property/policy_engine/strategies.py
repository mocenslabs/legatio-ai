"""Hypothesis strategies for generating valid ProposedAction and RuleInput instances."""

from decimal import Decimal
from typing import Any

from hypothesis import strategies as st

from core.enums import RuleAction, RuleCategory, RuleOperator
from core.schemas.policy import ProposedAction, RuleCondition
from services.policy_engine.types import RuleInput


@st.composite
def decimal_amount(draw: st.DrawFn, min_value: int = 0, max_value: int = 10000) -> Decimal:
    """Generate a valid Decimal amount."""
    value = draw(st.integers(min_value=min_value, max_value=max_value))
    cents = draw(st.integers(min_value=0, max_value=99))
    return Decimal(f"{value}.{cents:02d}")


@st.composite
def currency_code(draw: st.DrawFn) -> str:
    """Generate a valid ISO 4217 currency code."""
    return draw(st.sampled_from(["EUR", "USD", "GBP", "CHF", "JPY"]))


@st.composite
def action_type(draw: st.DrawFn) -> str:
    """Generate a valid action type."""
    return draw(st.sampled_from(["purchase", "subscribe", "share_data", "rent", "book"]))


@st.composite
def proposed_action_strategy(draw: st.DrawFn) -> ProposedAction:
    """Generate a valid ProposedAction."""
    has_amount = draw(st.booleans())
    amount = draw(decimal_amount()) if has_amount else None
    currency = draw(currency_code()) if has_amount else None

    data_fields = draw(
        st.lists(
            st.sampled_from(["phone_number", "email", "health_data", "location", "address"]),
            min_size=0,
            max_size=3,
            unique=True,
        )
    )

    has_contract = draw(st.booleans())
    contract_length = draw(st.integers(min_value=1, max_value=36)) if has_contract else None
    category = draw(st.sampled_from(["books", "electronics", "travel", "gambling", None]))

    return ProposedAction(
        action_type=draw(action_type()),
        amount=amount,
        currency=currency,
        data_fields_requested=data_fields,
        contract_length_months=contract_length,
        auto_renewal=draw(st.booleans()),
        category=category,
        is_new_vendor=draw(st.booleans()),
        price_increase_pct=draw(decimal_amount(min_value=0, max_value=100))
        if draw(st.booleans())
        else None,
        metadata=draw(
            st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=50), max_size=3)
        ),
    )


@st.composite
def rule_condition_strategy(draw: st.DrawFn) -> RuleCondition:
    """Generate a valid RuleCondition."""
    field_name = draw(
        st.sampled_from(
            [
                "amount",
                "currency",
                "data_fields_requested",
                "contract_length_months",
                "auto_renewal",
                "category",
                "is_new_vendor",
                "price_increase_pct",
            ]
        )
    )
    operator = draw(st.sampled_from(list(RuleOperator)))
    category = draw(st.sampled_from(list(RuleCategory)))

    # Generate appropriate value based on operator
    value: Any
    if operator in (RuleOperator.IN, RuleOperator.NOT_IN):
        value = draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    elif operator in (RuleOperator.CONTAINS, RuleOperator.NOT_CONTAINS):
        value = draw(st.text(min_size=1, max_size=20))
    elif operator in (
        RuleOperator.GREATER_THAN,
        RuleOperator.GREATER_THAN_OR_EQUAL,
        RuleOperator.LESS_THAN,
        RuleOperator.LESS_THAN_OR_EQUAL,
    ):
        value = draw(st.integers(min_value=0, max_value=10000))
    else:  # EQUALS, NOT_EQUALS
        value = draw(st.one_of(st.booleans(), st.text(min_size=1, max_size=20), st.integers()))

    return RuleCondition(
        field_name=field_name,
        operator=operator,
        value=value,
        category=category,
    )


@st.composite
def rule_input_strategy(draw: st.DrawFn, rule_number: int = 1) -> RuleInput:
    """Generate a valid RuleInput."""
    conditions = draw(st.lists(rule_condition_strategy(), min_size=1, max_size=3))
    return RuleInput(
        rule_id=f"rule-{draw(st.uuids())}",
        rule_number=rule_number,
        name=draw(st.text(min_size=1, max_size=50)),
        category=draw(st.sampled_from(list(RuleCategory))),
        action=draw(st.sampled_from(list(RuleAction))),
        conditions=conditions,
        is_active=draw(st.booleans()),
    )


@st.composite
def rule_set_strategy(draw: st.DrawFn, size: int = 5) -> list[RuleInput]:
    """Generate a list of RuleInput with unique rule numbers."""
    return [draw(rule_input_strategy(rule_number=i + 1)) for i in range(size)]
