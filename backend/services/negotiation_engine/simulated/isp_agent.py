"""
Simulated ISP Agent for subscription / internet-bill negotiations.

Scripted, deterministic offers so demos and tests can exercise the real
policy engine without live counterparties:

  Round 1 — High price + long lock-in + auto-renewal (amount / contract rules)
  Round 2 — Still pricey and asks for phone_number (privacy DENY)
  Round 3 — Removes phone demand; shorter term but auto-renewal remains
  Round 4 — Lower price, still auto-renewal (grey zone / human OK)
  Round 5 — Clean compromise under common budgets (ALLOW or soft OK)

Recommended demo rules (optional, user-defined):
  - REQUIRE_APPROVAL if amount > 80 (or 100)
  - DENY if amount > 150
  - DENY if data_fields_requested CONTAINS phone_number
  - Optional: DENY or ask on auto_renewal / long contract via custom fields

Source: expands Use Case 2 (04-BUSINESS-FLOW.md) for broader trial coverage.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)


class SimulatedISPAgent(SimulatedAgent):
    """
    Simulated ISP agent with a multi-round scripted playbook.

    Deterministic: same round_number always yields the same ProposedAction.
    """

    RESPONSES: list[dict[str, Any]] = [
        # Round 1: opening offer — expensive + 24 months + auto-renewal
        {
            "action_type": "subscribe",
            "amount": Decimal("129.00"),
            "currency": "EUR",
            "contract_length_months": 24,
            "auto_renewal": True,
            "data_fields_requested": [],
            "terms": {
                "service": "internet",
                "speed": "600Mbps",
                "category": "subscription",
            },
            "summary": (
                "Opening offer: €129/month for 24 months with auto-renewal "
                "(600 Mbps fibre)."
            ),
        },
        # Round 2: slight concession but requests phone (privacy trigger)
        {
            "action_type": "subscribe",
            "amount": Decimal("99.00"),
            "currency": "EUR",
            "contract_length_months": 24,
            "auto_renewal": True,
            "data_fields_requested": ["phone_number"],
            "terms": {
                "service": "internet",
                "speed": "600Mbps",
                "category": "subscription",
            },
            "summary": (
                "I can do €99/month for 24 months with auto-renewal, "
                "but I need your phone number to activate the line."
            ),
        },
        # Round 3: drops phone request; shorter term; still auto-renewal
        {
            "action_type": "subscribe",
            "amount": Decimal("99.00"),
            "currency": "EUR",
            "contract_length_months": 12,
            "auto_renewal": True,
            "data_fields_requested": [],
            "terms": {
                "service": "internet",
                "speed": "600Mbps",
                "category": "subscription",
            },
            "summary": (
                "No phone needed. €99/month for 12 months, auto-renewal still on."
            ),
        },
        # Round 4: better price, auto-renewal remains (human grey zone)
        {
            "action_type": "subscribe",
            "amount": Decimal("85.00"),
            "currency": "EUR",
            "contract_length_months": 12,
            "auto_renewal": True,
            "data_fields_requested": [],
            "terms": {
                "service": "internet",
                "speed": "600Mbps",
                "category": "subscription",
            },
            "summary": "€85/month for 12 months. Auto-renewal remains enabled.",
        },
        # Round 5: clean compromise for typical budgets
        {
            "action_type": "subscribe",
            "amount": Decimal("72.00"),
            "currency": "EUR",
            "contract_length_months": 12,
            "auto_renewal": False,
            "data_fields_requested": [],
            "terms": {
                "service": "internet",
                "speed": "600Mbps",
                "category": "subscription",
            },
            "summary": (
                "Final offer: €72/month for 12 months, no auto-renewal, "
                "no personal data required."
            ),
        },
    ]

    def __init__(self) -> None:
        """Initialize the ISP agent."""
        self._round = 0

    @property
    def agent_name(self) -> str:
        return "Simulated ISP Agent"

    @property
    def agent_type(self) -> str:
        return "isp"

    def respond(
        self,
        round_number: int,
        user_instruction: str,
        previous_proposals: list[ProposedAction],
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Return the scripted response for the current round."""
        if round_number < 1 or round_number > len(self.RESPONSES):
            raise NegotiationCompletedError(
                f"ISP agent has no response for round {round_number}. "
                f"Max rounds: {len(self.RESPONSES)}"
            )

        response_data = self.RESPONSES[round_number - 1]

        action = ProposedAction(
            action_type=response_data["action_type"],
            amount=response_data["amount"],
            currency=response_data["currency"],
            contract_length_months=response_data["contract_length_months"],
            auto_renewal=response_data["auto_renewal"],
            data_fields_requested=list(response_data["data_fields_requested"]),
            terms=dict(response_data["terms"]),
        )

        return AgentResponse(
            action=action,
            natural_language_summary=response_data["summary"],
            metadata={"round": round_number, "agent_type": self.agent_type},
        )

    def reset(self) -> None:
        """Reset the agent for a new negotiation."""
        self._round = 0
