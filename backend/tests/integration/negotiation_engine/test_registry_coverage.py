"""
Additional integration tests for registry to improve coverage.
Source: DEL-026
"""

import pytest

from services.negotiation_engine.base import SimulatedAgent
from services.negotiation_engine.registry import (
    AGENT_REGISTRY,
    create_agent,
    get_agent_class,
    list_available_agents,
)
from services.negotiation_engine.simulated import (
    SimulatedHotelAgent,
    SimulatedISPAgent,
    SimulatedVendorAgent,
)


class TestRegistryCoverage:
    """Additional registry tests for coverage."""

    def test_get_agent_class_unknown_raises_value_error(self) -> None:
        """Unknown agent type raises ValueError with helpful message."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent_class("nonexistent_agent")

    def test_create_agent_hotel_returns_simulated_hotel_agent(self) -> None:
        """create_agent('hotel') returns SimulatedHotelAgent."""
        agent = create_agent("hotel")
        assert isinstance(agent, SimulatedHotelAgent)
        assert isinstance(agent, SimulatedAgent)

    def test_create_agent_isp_returns_simulated_isp_agent(self) -> None:
        """create_agent('isp') returns SimulatedISPAgent."""
        agent = create_agent("isp")
        assert isinstance(agent, SimulatedISPAgent)

    def test_create_agent_vendor_returns_simulated_vendor_agent(self) -> None:
        """create_agent('vendor') returns SimulatedVendorAgent."""
        agent = create_agent("vendor")
        assert isinstance(agent, SimulatedVendorAgent)

    def test_list_available_agents_returns_sorted_list(self) -> None:
        """list_available_agents returns sorted list of types."""
        agents = list_available_agents()
        assert agents == ["hotel", "isp", "vendor"]

    def test_registry_contains_all_three_types(self) -> None:
        """Registry has all 3 expected agent types."""
        assert "hotel" in AGENT_REGISTRY
        assert "isp" in AGENT_REGISTRY
        assert "vendor" in AGENT_REGISTRY
        assert len(AGENT_REGISTRY) == 3

    def test_create_agent_creates_new_instance_each_time(self) -> None:
        """Each create_agent call returns a new instance."""
        a1 = create_agent("hotel")
        a2 = create_agent("hotel")
        assert a1 is not a2

    def test_all_registered_agents_are_simulated_agent_subclass(self) -> None:
        """Every registered agent class inherits from SimulatedAgent."""
        for agent_type, agent_class in AGENT_REGISTRY.items():
            assert issubclass(
                agent_class, SimulatedAgent
            ), f"{agent_type} class does not inherit from SimulatedAgent"
