"""
Simulated ISP Agent for Use Case 2: Subscription Negotiation.

Reproduces the scenario from 04-BUSINESS-FLOW.md Section 5:
"Negotiate my internet bill. I want to pay less than €100/month
and I don't want auto-renewal."

The agent follows a scripted sequence of 2 rounds:
  Round 1: €60/month, 24 months, auto-renewal (tests contract length rule)
  Round 2: €70/month, 12 months, no auto-renewal (acceptable offer)

Source: 04-BUSINESS-FLOW.md Section 5.2
"""

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
    Simulated ISP Agent for the subscription negotiation scenario.

    Hardcoded responses that reproduce the Use Case 2 flow.
    """

    RESPONSES: list[dict[str, Any]] = [
        # Round 1: Initial offer with long contract and auto-renewal
        {
            "action_type": "subscribe",
            "amount": Decimal("60.00"),
            "currency": "EUR",
            "contract_length_months": 24,
            "auto_renewal": True,
            "data_fields_requested": [],
            "terms": {"service": "internet", "speed": "600Mbps", "category": "subscription"},
            "summary": "I offer you €60/month for 24 months with auto-renewal.",
        },
        # Round 2: Counter-offer with acceptable terms
        {
            "action_type": "subscribe",
            "amount": Decimal("70.00"),
            "currency": "EUR",
            "contract_length_months": 12,
            "auto_renewal": False,
            "data_fields_requested": [],
            "terms": {"service": "internet", "speed": "600Mbps", "category": "subscription"},
            "summary": "€70/month for 12 months, no auto-renewal.",
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
            data_fields_requested=response_data["data_fields_requested"],
            terms=response_data["terms"],
        )

        return AgentResponse(
            action=action,
            natural_language_summary=response_data["summary"],
            metadata={"round": round_number, "agent_type": self.agent_type},
        )

    def reset(self) -> None:
        """Reset the agent for a new negotiation."""
        self._round = 0
