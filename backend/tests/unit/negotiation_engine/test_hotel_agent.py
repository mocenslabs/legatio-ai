"""
Unit tests for the SimulatedHotelAgent.

Verifies the Use Case 1: AI Travel Negotiation flow.

Source: 04-BUSINESS-FLOW.md Section 4
"""

from decimal import Decimal

import pytest

from services.negotiation_engine.base import NegotiationCompletedError
from services.negotiation_engine.simulated.hotel_agent import SimulatedHotelAgent


class TestSimulatedHotelAgent:
    def test_agent_properties(self) -> None:
        """Agent has correct name and type."""
        agent = SimulatedHotelAgent()
        assert agent.agent_name == "Simulated Hotel Agent"
        assert agent.agent_type == "hotel"

    def test_round_1_initial_offer(self) -> None:
        """Round 1: €820, no phone, breakfast included."""
        agent = SimulatedHotelAgent()
        response = agent.respond(
            round_number=1,
            user_instruction="Find hotel in Madrid, 5 nights, < €700",
            previous_proposals=[],
        )
        assert response.action.action_type == "purchase"
        assert response.action.amount == Decimal("820.00")
        assert response.action.currency == "EUR"
        assert response.action.data_fields_requested == []
        assert response.action.terms is not None
        assert response.action.terms is not None
        assert response.action.terms["nights"] == 5
        assert response.action.terms is not None
        assert response.action.terms["breakfast"] is True

    def test_round_2_phone_request(self) -> None:
        """Round 2: €680, with phone number (privacy violation)."""
        agent = SimulatedHotelAgent()
        response = agent.respond(
            round_number=2,
            user_instruction="Find hotel in Madrid",
            previous_proposals=[],
        )
        assert response.action.amount == Decimal("680.00")
        assert "phone_number" in response.action.data_fields_requested

    def test_round_3_final_offer(self) -> None:
        """Round 3: €700, no phone, 48h cancellation."""
        agent = SimulatedHotelAgent()
        response = agent.respond(
            round_number=3,
            user_instruction="Find hotel in Madrid",
            previous_proposals=[],
        )
        assert response.action.amount == Decimal("700.00")
        assert response.action.data_fields_requested == []
        assert response.action.terms is not None
        assert response.action.terms is not None
        assert response.action.terms["cancellation"] == "48h"

    def test_round_4_raises_completed_error(self) -> None:
        """Round 4 raises NegotiationCompletedError."""
        agent = SimulatedHotelAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(
                round_number=4,
                user_instruction="test",
                previous_proposals=[],
            )

    def test_round_0_raises_completed_error(self) -> None:
        """Round 0 raises NegotiationCompletedError."""
        agent = SimulatedHotelAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(
                round_number=0,
                user_instruction="test",
                previous_proposals=[],
            )

    def test_responses_are_deterministic(self) -> None:
        """Same input produces same output (100 runs)."""
        agent = SimulatedHotelAgent()
        responses = [agent.respond(1, "test", []) for _ in range(100)]
        amounts = {r.action.amount for r in responses}
        assert amounts == {Decimal("820.00")}

    def test_reset_clears_state(self) -> None:
        """reset() allows reusing the agent."""
        agent = SimulatedHotelAgent()
        agent.respond(1, "test", [])
        agent.reset()
        # Should be able to respond again
        response = agent.respond(1, "test", [])
        assert response.action.amount == Decimal("820.00")

    def test_response_has_summary(self) -> None:
        """Each response has a natural language summary."""
        agent = SimulatedHotelAgent()
        for round_num in range(1, 4):
            response = agent.respond(round_num, "test", [])
            assert len(response.natural_language_summary) > 0

    def test_response_has_metadata(self) -> None:
        """Each response includes metadata."""
        agent = SimulatedHotelAgent()
        response = agent.respond(1, "test", [])
        assert response.metadata is not None
        assert response.metadata["round"] == 1
        assert response.metadata["agent_type"] == "hotel"


class TestHotelAgentUseCase1Flow:
    """Integration test for the full Use Case 1 flow."""

    def test_full_negotiation_flow(self) -> None:
        """
        Full flow from 04-BUSINESS-FLOW.md Section 4.2:
          Round 1: €820 → REQUIRE_APPROVAL (amount > €200)
          Round 2: €680 + phone → DENY (Rule #17)
          Round 3: €700, no phone → REQUIRE_APPROVAL
        """
        agent = SimulatedHotelAgent()

        # Round 1
        r1 = agent.respond(1, "Find hotel Madrid", [])
        assert r1.action.amount == Decimal("820.00")
        assert r1.action.data_fields_requested == []

        # Round 2
        r2 = agent.respond(2, "Find hotel Madrid", [r1.action])
        assert r2.action.amount == Decimal("680.00")
        assert "phone_number" in r2.action.data_fields_requested

        # Round 3
        r3 = agent.respond(3, "Find hotel Madrid", [r1.action, r2.action])
        assert r3.action.amount == Decimal("700.00")
        assert r3.action.data_fields_requested == []
