"""
Unit tests for the SimulatedISPAgent.

Verifies the Use Case 2: Subscription Negotiation flow.

Source: 04-BUSINESS-FLOW.md Section 5
"""

from decimal import Decimal

import pytest

from services.negotiation_engine.base import NegotiationCompletedError
from services.negotiation_engine.simulated.isp_agent import SimulatedISPAgent


class TestSimulatedISPAgent:
    def test_agent_properties(self) -> None:
        """Agent has correct name and type."""
        agent = SimulatedISPAgent()
        assert agent.agent_name == "Simulated ISP Agent"
        assert agent.agent_type == "isp"

    def test_round_1_long_contract(self) -> None:
        """Round 1: €60/month, 24 months, auto-renewal."""
        agent = SimulatedISPAgent()
        response = agent.respond(
            round_number=1,
            user_instruction="Negotiate internet bill",
            previous_proposals=[],
        )
        assert response.action.action_type == "subscribe"
        assert response.action.amount == Decimal("60.00")
        assert response.action.contract_length_months == 24
        assert response.action.auto_renewal is True

    def test_round_2_acceptable_offer(self) -> None:
        """Round 2: €70/month, 12 months, no auto-renewal."""
        agent = SimulatedISPAgent()
        response = agent.respond(
            round_number=2,
            user_instruction="Negotiate internet bill",
            previous_proposals=[],
        )
        assert response.action.amount == Decimal("70.00")
        assert response.action.contract_length_months == 12
        assert response.action.auto_renewal is False

    def test_round_3_raises_completed_error(self) -> None:
        """Round 3 raises NegotiationCompletedError."""
        agent = SimulatedISPAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(3, "test", [])

    def test_responses_are_deterministic(self) -> None:
        """Same input produces same output."""
        agent = SimulatedISPAgent()
        r1 = agent.respond(1, "test", [])
        r2 = agent.respond(1, "test", [])
        assert r1.action.amount == r2.action.amount
        assert r1.action.contract_length_months == r2.action.contract_length_months

    def test_reset_clears_state(self) -> None:
        """reset() allows reusing the agent."""
        agent = SimulatedISPAgent()
        agent.respond(1, "test", [])
        agent.reset()
        response = agent.respond(1, "test", [])
        assert response.action.amount == Decimal("60.00")


class TestISPAgentUseCase2Flow:
    """Integration test for the full Use Case 2 flow."""

    def test_full_negotiation_flow(self) -> None:
        """
        Full flow from 04-BUSINESS-FLOW.md Section 5.2:
          Round 1: €60, 24 months, auto-renewal → DENY (contract > 12)
          Round 2: €70, 12 months, no auto-renewal → REQUIRE_APPROVAL
        """
        agent = SimulatedISPAgent()

        # Round 1
        r1 = agent.respond(1, "Negotiate internet bill", [])
        assert r1.action.amount == Decimal("60.00")
        assert r1.action.contract_length_months == 24
        assert r1.action.auto_renewal is True

        # Round 2
        r2 = agent.respond(2, "Negotiate internet bill", [r1.action])
        assert r2.action.amount == Decimal("70.00")
        assert r2.action.contract_length_months == 12
        assert r2.action.auto_renewal is False
