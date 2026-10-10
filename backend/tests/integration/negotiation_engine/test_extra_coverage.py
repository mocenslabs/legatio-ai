"""
Additional tests to boost coverage to >= 95%.
Targets:
- proposals/managers.py lines 14, 17 (AppendOnlyQuerySet via CounterProposal/PolicyDecision)
- negotiation_engine/base.py lines 43, 49, 75 (SimulatedAgent properties and reset)
- negotiation_engine/registry.py line 41 (error path)
- simulated/hotel_agent.py lines 76, 105, 128
- simulated/isp_agent.py lines 64, 79, 104
- simulated/vendor_agent.py lines 57, 72, 97
Source: DEL-026
"""

from decimal import Decimal
from typing import Any

import pytest

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.negotiations.models import NegotiationRoom
from apps.proposals.models import CounterProposal, PolicyDecision, Proposal
from core.enums import (
    AgentType,
    ConstitutionStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)
from core.schemas.policy import ProposedAction
from services.negotiation_engine.base import (
    AgentResponse,
    NegotiationCompletedError,
    SimulatedAgent,
)
from services.negotiation_engine.registry import create_agent, get_agent_class
from services.negotiation_engine.simulated.hotel_agent import SimulatedHotelAgent
from services.negotiation_engine.simulated.isp_agent import SimulatedISPAgent
from services.negotiation_engine.simulated.vendor_agent import SimulatedVendorAgent


@pytest.fixture
def user() -> Any:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(email="extra@example.com", password="pass")


@pytest.fixture
def user_agent(user: Any) -> Any:
    return Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="User Agent")


@pytest.fixture
def external_agent() -> Any:
    return Agent.objects.create(owner=None, agent_type=AgentType.SIMULATED, name="External Agent")


@pytest.fixture
def constitution(user: Any, user_agent: Any) -> Any:
    return Constitution.objects.create(
        agent=user_agent,
        name="Test Constitution",
        status=ConstitutionStatus.ACTIVE,
    )


@pytest.fixture
def constitution_version(user: Any, constitution: Any) -> Any:
    return ConstitutionVersion.objects.create(
        constitution=constitution,
        version_number=1,
        status=ConstitutionStatus.ACTIVE,
        created_by=user,
    )


@pytest.fixture
def room(user_agent: Any, external_agent: Any, constitution: Any) -> Any:
    return NegotiationRoom.objects.create(
        user_agent=user_agent,
        external_agent=external_agent,
        constitution=constitution,
        reference_code="NEG-EXTRA-001",
        title="Test",
        user_instruction="test",
    )


@pytest.mark.django_db(transaction=True)
class TestProposalsManagersCoverage:
    """Cover proposals/managers.py lines 14, 17.

    Proposal uses default Django manager (not AppendOnlyManager).
    CounterProposal and PolicyDecision use AppendOnlyManager.
    """

    def test_counter_proposal_update_raises(
        self,
        room: Any,
        external_agent: Any,
    ) -> None:
        """Line 14: AppendOnlyQuerySet.update() raises RuntimeError on CounterProposal."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="test",
            amount=Decimal("10.00"),
            currency="EUR",
            status=ProposalStatus.RECEIVED,
            round_number=1,
        )
        CounterProposal.objects.create(
            proposal=proposal,
            sender=user_agent if hasattr(self, "user_agent") else external_agent,
            adjustments={"amount": "9.00"},
            reasoning="Test",
        )
        with pytest.raises(RuntimeError, match="append-only"):
            CounterProposal.objects.all().update(reasoning="changed")

    def test_counter_proposal_delete_raises(
        self,
        room: Any,
        external_agent: Any,
    ) -> None:
        """Line 17: AppendOnlyQuerySet.delete() raises RuntimeError on CounterProposal."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="test",
            amount=Decimal("10.00"),
            currency="EUR",
            status=ProposalStatus.RECEIVED,
            round_number=1,
        )
        CounterProposal.objects.create(
            proposal=proposal,
            sender=external_agent,
            adjustments={"amount": "9.00"},
            reasoning="Test",
        )
        with pytest.raises(RuntimeError, match="append-only"):
            CounterProposal.objects.all().delete()

    def test_policy_decision_update_raises(
        self,
        room: Any,
        external_agent: Any,
        constitution_version: Any,
    ) -> None:
        """Line 14: AppendOnlyQuerySet.update() raises RuntimeError on PolicyDecision."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="test",
            amount=Decimal("10.00"),
            currency="EUR",
            status=ProposalStatus.RECEIVED,
            round_number=1,
        )
        PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        with pytest.raises(RuntimeError, match="append-only"):
            PolicyDecision.objects.all().update(reason="changed")

    def test_policy_decision_delete_raises(
        self,
        room: Any,
        external_agent: Any,
        constitution_version: Any,
    ) -> None:
        """Line 17: AppendOnlyQuerySet.delete() raises RuntimeError on PolicyDecision."""
        proposal = Proposal.objects.create(
            room=room,
            sender=external_agent,
            action_type="test",
            amount=Decimal("10.00"),
            currency="EUR",
            status=ProposalStatus.RECEIVED,
            round_number=1,
        )
        PolicyDecision.objects.create(
            proposal=proposal,
            constitution_version=constitution_version,
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        with pytest.raises(RuntimeError, match="append-only"):
            PolicyDecision.objects.all().delete()


class TestSimulatedAgentBaseCoverage:
    """Cover base.py SimulatedAgent abstract methods and reset."""

    def test_simulated_agent_agent_name(self) -> None:
        """Line 43: agent_name property via concrete subclass."""
        agent = SimulatedHotelAgent()
        assert agent.agent_name == "Simulated Hotel Agent"

    def test_simulated_agent_agent_type(self) -> None:
        """Line 49: agent_type property via concrete subclass."""
        agent = SimulatedISPAgent()
        assert agent.agent_type == "isp"

    def test_simulated_agent_reset_noop(self) -> None:
        """Line 75: SimulatedAgent.reset() default is no-op."""

        # Create a minimal subclass that doesn't override reset
        class NoopAgent(SimulatedAgent):
            @property
            def agent_name(self) -> Any:
                return "Noop"

            @property
            def agent_type(self) -> Any:
                return "noop"

            def respond(
                self,
                round_number: Any,
                user_instruction: Any,
                previous_proposals: Any,
                context: Any = None,
            ) -> Any:
                return AgentResponse(
                    action=ProposedAction(action_type="test", amount=Decimal("1"), currency="EUR"),
                    natural_language_summary="test",
                )

        agent = NoopAgent()
        # reset() is a no-op and returns None by contract.
        agent.reset()

    def test_hotel_agent_respond_round_1(self) -> None:
        """Cover hotel agent respond for round 1."""
        agent = SimulatedHotelAgent()
        response = agent.respond(1, "Find hotel", [])
        assert response.action.amount == Decimal("820.00")

    def test_hotel_agent_respond_round_2(self) -> None:
        """Cover hotel agent respond for round 2."""
        agent = SimulatedHotelAgent()
        response = agent.respond(2, "Find hotel", [])
        assert response.action.amount == Decimal("680.00")

    def test_hotel_agent_respond_round_3(self) -> None:
        """Cover hotel agent respond for round 3."""
        agent = SimulatedHotelAgent()
        response = agent.respond(3, "Find hotel", [])
        assert response.action.amount == Decimal("700.00")

    def test_hotel_agent_completed_error(self) -> None:
        """Line 76: hotel agent raises NegotiationCompletedError when round > 3."""
        agent = SimulatedHotelAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(4, "Find hotel", [])

    def test_hotel_agent_invalid_round(self) -> None:
        """Line 76: hotel agent raises for round < 1."""
        agent = SimulatedHotelAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(0, "Find hotel", [])

    def test_hotel_agent_reset(self) -> None:
        """Line 128: hotel agent reset() resets _round to 0."""
        agent = SimulatedHotelAgent()
        agent._round = 5
        agent.reset()
        assert agent._round == 0

    def test_isp_agent_respond_round_1(self) -> None:
        """Cover ISP agent respond for round 1."""
        agent = SimulatedISPAgent()
        response = agent.respond(1, "Negotiate ISP", [])
        assert response.action.amount == Decimal("60.00")

    def test_isp_agent_respond_round_2(self) -> None:
        """Cover ISP agent respond for round 2."""
        agent = SimulatedISPAgent()
        response = agent.respond(2, "Negotiate ISP", [])
        assert response.action.amount == Decimal("70.00")

    def test_isp_agent_completed_error(self) -> None:
        """Line 64: ISP agent raises NegotiationCompletedError when round > 2."""
        agent = SimulatedISPAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(3, "Negotiate ISP", [])

    def test_isp_agent_reset(self) -> None:
        """Line 104: ISP agent reset() resets _round to 0."""
        agent = SimulatedISPAgent()
        agent._round = 3
        agent.reset()
        assert agent._round == 0

    def test_vendor_agent_respond_round_1(self) -> None:
        """Cover vendor agent respond for round 1."""
        agent = SimulatedVendorAgent()
        response = agent.respond(1, "Buy book", [])
        assert response.action.amount == Decimal("25.00")

    def test_vendor_agent_completed_error(self) -> None:
        """Line 57: vendor agent raises NegotiationCompletedError when round > 1."""
        agent = SimulatedVendorAgent()
        with pytest.raises(NegotiationCompletedError):
            agent.respond(2, "Buy book", [])

    def test_vendor_agent_reset(self) -> None:
        """Line 97: vendor agent reset() resets _round to 0."""
        agent = SimulatedVendorAgent()
        agent._round = 1
        agent.reset()
        assert agent._round == 0


class TestRegistryErrorPath:
    """Cover registry.py error paths."""

    def test_get_agent_class_unknown_raises_value_error(self) -> None:
        """Line 41: get_agent_class raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent_class("nonexistent_type")

    def test_create_agent_unknown_raises(self) -> None:
        """create_agent propagates ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_agent("nonexistent_type")
