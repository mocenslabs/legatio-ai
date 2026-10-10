"""
Counter-offer generation logic.

When a proposal is DENIED by the Policy Engine, the system generates
a counter-offer that addresses the reason for denial.

Source: 04-BUSINESS-FLOW.md Section 4.2 (Round 5-6)
"""

from decimal import Decimal
from typing import Any, Protocol

from core.schemas.policy import ProposedAction


class HasReason(Protocol):
    """Minimal protocol for anything that exposes a denial reason."""

    reason: str


def generate_counter_offer(
    original_proposal: ProposedAction,
    policy_decision: HasReason,
) -> ProposedAction:
    """
    Generate a counter-offer based on the reason for denial.

    Args:
        original_proposal: The proposal that was denied.
        policy_decision: Object with a ``reason`` attribute explaining the denial
            (schema PolicyDecision, Django model, or SimpleNamespace).

    Returns:
        A new ProposedAction with adjustments to address the denial.
    """
    # Start with a copy of the original proposal
    terms_dict: dict[str, Any] = dict(original_proposal.terms) if original_proposal.terms else {}

    counter_data: dict[str, Any] = {
        "action_type": original_proposal.action_type,
        "amount": original_proposal.amount,
        "currency": original_proposal.currency,
        "data_fields_requested": list(original_proposal.data_fields_requested),
        "contract_length_months": original_proposal.contract_length_months,
        "auto_renewal": original_proposal.auto_renewal,
        "category": original_proposal.category,
        "is_new_vendor": original_proposal.is_new_vendor,
        "terms": terms_dict,
    }

    # Analyze the denial reason and adjust
    reason_lower = policy_decision.reason.lower()

    # If denied due to data fields (privacy violation), remove them
    if "phone_number" in reason_lower or "data_fields" in reason_lower:
        fields = list(counter_data["data_fields_requested"])
        if "phone_number" in fields:
            fields.remove("phone_number")
        counter_data["data_fields_requested"] = fields

    # If denied due to amount, reduce it slightly
    if ("amount" in reason_lower or "exceeds" in reason_lower) and counter_data[
        "amount"
    ] is not None:
        counter_data["amount"] = counter_data["amount"] * Decimal("0.90")

    # If denied due to contract length, reduce it
    if ("contract" in reason_lower or "length" in reason_lower) and counter_data[
        "contract_length_months"
    ] is not None:
        counter_data["contract_length_months"] = min(counter_data["contract_length_months"], 12)

    # If denied due to auto-renewal, disable it
    if "auto" in reason_lower and "renewal" in reason_lower:
        counter_data["auto_renewal"] = False

    return ProposedAction(**counter_data)
