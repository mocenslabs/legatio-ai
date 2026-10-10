"""
Unit tests for the SimulatedVendorAgent.

Verifies the Use Case 3: Purchase Approval flow.

Source: 04-BUSINESS-FLOW.md Section 6
"""

from decimal import Decimal

import pytest

from services.negotiation_engine.base import NegotiationCompletedError
from services.negotiation_engine.simulated.vendor_agent import SimulatedVendorAgent


class TestSimulatedVendorAgent:
    def test_agent_properties(self) -> None:
        """Agent has correct name and type."""
        agent = SimulatedVendorAgent()
        assert agent.agent_name == "Simulated Vendor Agent"
        assert agent.agent_type == "vendor"

    def test_round_1_book_offer(self) -> None:
        """Round 1: €25 for Clean Architecture book."""
        agent = SimulatedVendorAgent()
        response = agent.respond(
            round_number=1,
            user_instruction="Buy Clean Architecture",
            previous_proposals=[],
        )
        assert response.action.action_type == "purchase"
        assert response.action.amount == Decimal("25.00")
        assert response.action.currency == "EUR"
        assert response.action.category == "books"
        assert response.action.terms is not None
        assert response.action.terms is not None
        assert response.action.terms["product"] == "Clean Architecture"

    def test_round_2_raises_completed_error(self) -> None:
        """Round 2 raises NegotiationCompletedError (only 1 round)."""
        agent = SimulatedVendorAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(2, "test", [])

    def test_responses_are_deterministic(self) -> None:
        """Same input produces same output."""
        agent = SimulatedVendorAgent()
        r1 = agent.respond(1, "test", [])
        r2 = agent.respond(1, "test", [])
        assert r1.action.amount == r2.action.amount
        assert r1.action.terms == r2.action.terms

    def test_reset_clears_state(self) -> None:
        """reset() allows reusing the agent."""
        agent = SimulatedVendorAgent()
        agent.respond(1, "test", [])
        agent.reset()
        response = agent.respond(1, "test", [])
        assert response.action.amount == Decimal("25.00")


class TestVendorAgentUseCase3Flow:
    """Integration test for the full Use Case 3 flow."""

    def test_full_negotiation_flow(self) -> None:
        """
        Full flow from 04-BUSINESS-FLOW.md Section 6.2:
          Round 1: €25 for Clean Architecture → REQUIRE_APPROVAL
        """
        agent = SimulatedVendorAgent()

        r1 = agent.respond(1, "Buy Clean Architecture", [])
        assert r1.action.amount == Decimal("25.00")
        assert r1.action.category == "books"
        assert r1.action.terms is not None
        assert r1.action.terms["product"] == "Clean Architecture"
