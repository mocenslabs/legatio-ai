"""
Unit tests for the SimulatedISPAgent multi-round subscription playbook.
"""

from decimal import Decimal

import pytest

from services.negotiation_engine.base import NegotiationCompletedError
from services.negotiation_engine.simulated.isp_agent import SimulatedISPAgent


class TestSimulatedISPAgent:
    def test_agent_properties(self) -> None:
        agent = SimulatedISPAgent()
        assert agent.agent_name == "Simulated ISP Agent"
        assert agent.agent_type == "isp"

    def test_playbook_length(self) -> None:
        assert len(SimulatedISPAgent.RESPONSES) == 5

    def test_round_1_high_price_lock_in(self) -> None:
        agent = SimulatedISPAgent()
        response = agent.respond(1, "Negotiate internet bill", [])
        assert response.action.action_type == "subscribe"
        assert response.action.amount == Decimal("129.00")
        assert response.action.contract_length_months == 24
        assert response.action.auto_renewal is True
        assert response.action.data_fields_requested == []

    def test_round_2_requests_phone(self) -> None:
        agent = SimulatedISPAgent()
        response = agent.respond(2, "Negotiate internet bill", [])
        assert response.action.amount == Decimal("99.00")
        assert "phone_number" in response.action.data_fields_requested
        assert response.action.auto_renewal is True

    def test_round_3_no_phone_shorter_term(self) -> None:
        agent = SimulatedISPAgent()
        response = agent.respond(3, "Negotiate internet bill", [])
        assert response.action.amount == Decimal("99.00")
        assert response.action.contract_length_months == 12
        assert response.action.data_fields_requested == []
        assert response.action.auto_renewal is True

    def test_round_4_lower_price_still_auto_renew(self) -> None:
        agent = SimulatedISPAgent()
        response = agent.respond(4, "Negotiate internet bill", [])
        assert response.action.amount == Decimal("85.00")
        assert response.action.auto_renewal is True
        assert response.action.data_fields_requested == []

    def test_round_5_clean_compromise(self) -> None:
        agent = SimulatedISPAgent()
        response = agent.respond(5, "Negotiate internet bill", [])
        assert response.action.amount == Decimal("72.00")
        assert response.action.contract_length_months == 12
        assert response.action.auto_renewal is False
        assert response.action.data_fields_requested == []

    def test_round_6_raises_completed_error(self) -> None:
        agent = SimulatedISPAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(6, "test", [])

    def test_round_zero_raises(self) -> None:
        agent = SimulatedISPAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(0, "test", [])

    def test_responses_are_deterministic(self) -> None:
        agent = SimulatedISPAgent()
        r1 = agent.respond(2, "test", [])
        r2 = agent.respond(2, "test", [])
        assert r1.action.amount == r2.action.amount
        assert r1.action.data_fields_requested == r2.action.data_fields_requested

    def test_reset_clears_state(self) -> None:
        agent = SimulatedISPAgent()
        agent.respond(1, "test", [])
        agent.reset()
        response = agent.respond(1, "test", [])
        assert response.action.amount == Decimal("129.00")


class TestISPAgentDemoCoverageFlow:
    """Full script order: price pressure → privacy → concessions → clean offer."""

    def test_full_five_round_flow(self) -> None:
        agent = SimulatedISPAgent()
        previous: list = []

        r1 = agent.respond(1, "Pay less, no phone, no auto-renew", previous)
        previous.append(r1.action)
        assert r1.action.amount == Decimal("129.00")

        r2 = agent.respond(2, "Pay less, no phone, no auto-renew", previous)
        previous.append(r2.action)
        assert "phone_number" in r2.action.data_fields_requested

        r3 = agent.respond(3, "Pay less, no phone, no auto-renew", previous)
        previous.append(r3.action)
        assert r3.action.data_fields_requested == []

        r4 = agent.respond(4, "Pay less, no phone, no auto-renew", previous)
        previous.append(r4.action)
        assert r4.action.amount == Decimal("85.00")

        r5 = agent.respond(5, "Pay less, no phone, no auto-renew", previous)
        assert r5.action.amount == Decimal("72.00")
        assert r5.action.auto_renewal is False
        assert r5.action.data_fields_requested == []
