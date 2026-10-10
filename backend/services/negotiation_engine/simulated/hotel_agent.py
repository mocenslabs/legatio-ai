"""
Simulated Hotel Agent for Use Case 1: AI Travel Negotiation.

Reproduces the exact scenario from 04-BUSINESS-FLOW.md Section 4:
"Find me a hotel in Madrid for 5 nights. Don't spend more than €700
and never share my phone number."

The agent follows a scripted sequence of 3 rounds:
  Round 1: €820, no phone (initial offer)
  Round 2: €680, with phone (privacy violation test)
  Round 3: €700, no phone, 48h cancellation (final offer)

Source: 05-ROADMAP.md Section 7.5
Source: 04-BUSINESS-FLOW.md Section 4.2
"""

from decimal import Decimal
from typing import Any

from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)


class SimulatedHotelAgent(SimulatedAgent):
    """
    Simulated Hotel Agent for the Madrid travel scenario.

    Hardcoded responses that reproduce the Use Case 1 flow.
    """

    # Scripted responses per round
    RESPONSES: list[dict[str, Any]] = [
        # Round 1: Initial offer
        {
            "action_type": "purchase",
            "amount": Decimal("820.00"),
            "currency": "EUR",
            "data_fields_requested": [],
            "terms": {"nights": 5, "breakfast": True, "destination": "Madrid"},
            "summary": "I offer €820 for 5 nights in Madrid, breakfast included.",
        },
        # Round 2: Counter with phone request (tests privacy rule)
        {
            "action_type": "purchase",
            "amount": Decimal("680.00"),
            "currency": "EUR",
            "data_fields_requested": ["phone_number"],
            "terms": {"nights": 5, "destination": "Madrid", "category": "travel"},
            "summary": "I can do €680, but I need your phone number for the booking.",
        },
        # Round 3: Final offer without phone
        {
            "action_type": "purchase",
            "amount": Decimal("700.00"),
            "currency": "EUR",
            "data_fields_requested": [],
            "terms": {
                "nights": 5,
                "cancellation": "48h",
                "destination": "Madrid",
            },
            "summary": "OK. €700 final price, no phone, 48h cancellation.",
        },
    ]

    def __init__(self) -> None:
        """Initialize the hotel agent."""
        self._round = 0

    @property
    def agent_name(self) -> str:
        return "Simulated Hotel Agent"

    @property
    def agent_type(self) -> str:
        return "hotel"

    def respond(
        self,
        round_number: int,
        user_instruction: str,
        previous_proposals: list[ProposedAction],
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """
        Return the scripted response for the current round.

        Args:
            round_number: Current round (1-indexed).
            user_instruction: User's original instruction.
            previous_proposals: Proposals made so far.
            context: Additional context.

        Returns:
            AgentResponse with the scripted proposal.

        Raises:
            NegotiationCompletedError: If round exceeds available responses.
        """
        if round_number < 1 or round_number > len(self.RESPONSES):
            raise NegotiationCompletedError(
                f"Hotel agent has no response for round {round_number}. "
                f"Max rounds: {len(self.RESPONSES)}"
            )

        response_data = self.RESPONSES[round_number - 1]

        action = ProposedAction(
            action_type=response_data["action_type"],
            amount=response_data["amount"],
            currency=response_data["currency"],
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
