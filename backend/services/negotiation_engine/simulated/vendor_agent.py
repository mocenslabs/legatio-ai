"""
Simulated Vendor Agent for Use Case 3: Purchase Approval.

Reproduces the scenario from 04-BUSINESS-FLOW.md Section 6:
"Buy the book 'Clean Architecture' if it costs less than €30."

The agent follows a scripted sequence of 1 round:
  Round 1: €25 for the book (direct purchase, no negotiation needed)

Source: 04-BUSINESS-FLOW.md Section 6.2
"""

from decimal import Decimal
from typing import Any

from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)


class SimulatedVendorAgent(SimulatedAgent):
    """
    Simulated Vendor Agent for the purchase approval scenario.

    Hardcoded responses that reproduce the Use Case 3 flow.
    """

    RESPONSES: list[dict[str, Any]] = [
        # Round 1: Direct offer for the book (new vendor → REQUIRE_APPROVAL)
        {
            "action_type": "purchase",
            "amount": Decimal("25.00"),
            "currency": "EUR",
            "category": "books",
            "is_new_vendor": True,
            "data_fields_requested": [],
            "terms": {
                "product": "Clean Architecture",
                "author": "Robert C. Martin",
                "format": "hardcover",
                "category": "books",
                "is_new_vendor": True,
            },
            "summary": "Clean Architecture costs €25.",
        },
    ]

    def __init__(self) -> None:
        """Initialize the vendor agent."""
        self._round = 0

    @property
    def agent_name(self) -> str:
        return "Simulated Vendor Agent"

    @property
    def agent_type(self) -> str:
        return "vendor"

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
                f"Vendor agent has no response for round {round_number}. "
                f"Max rounds: {len(self.RESPONSES)}"
            )

        response_data = self.RESPONSES[round_number - 1]

        action = ProposedAction(
            action_type=response_data["action_type"],
            amount=response_data["amount"],
            currency=response_data["currency"],
            category=response_data.get("category"),
            is_new_vendor=response_data.get("is_new_vendor", False),
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
