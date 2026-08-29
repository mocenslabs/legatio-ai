"""Unit tests for policy engine type definitions.

Tests cover ProposedAction, PolicyDecision dataclasses and all enums.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from apps.policies.engine.types import (
    DecisionOutcome,
    PolicyDecision,
    ProposedAction,
    RiskLevel,
)


class TestDecisionOutcome:
    """Tests for DecisionOutcome enum."""

    def test_all_values_exist(self) -> None:
        """Verify all expected outcomes are defined."""
        assert DecisionOutcome.ALLOW.value == "ALLOW"
        assert DecisionOutcome.DENY.value == "DENY"
        assert DecisionOutcome.REQUIRE_HUMAN_APPROVAL.value == "REQUIRE_HUMAN_APPROVAL"
        assert DecisionOutcome.ERROR.value == "ERROR"

    def test_enum_is_string(self) -> None:
        """Verify enum values are strings."""
        assert isinstance(DecisionOutcome.ALLOW, str)
        assert isinstance(DecisionOutcome.DENY, str)


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_all_values_exist(self) -> None:
        """Verify all risk levels are defined."""
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.CRITICAL.value == "CRITICAL"

    def test_enum_is_string(self) -> None:
        """Verify enum values are strings."""
        assert isinstance(RiskLevel.LOW, str)
        assert isinstance(RiskLevel.CRITICAL, str)


class TestProposedAction:
    """Tests for ProposedAction dataclass."""

    def test_creation_with_valid_data(self) -> None:
        """Verify action can be created with valid data."""
        actor_id = uuid.uuid4()
        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={"amount": 10000},
            actor_id=actor_id,
        )

        assert action.action_type == "CREATE_PROPOSAL"
        assert action.target_resource == "proposals"
        assert action.payload == {"amount": 10000}
        assert action.actor_id == actor_id

    def test_frozen_dataclass(self) -> None:
        """Verify dataclass is immutable."""
        actor_id = uuid.uuid4()
        action = ProposedAction(
            action_type="CREATE_PROPOSAL",
            target_resource="proposals",
            payload={},
            actor_id=actor_id,
        )

        with pytest.raises(AttributeError):
            action.action_type = "UPDATE_PROPOSAL"  # type: ignore[misc]

    def test_empty_payload(self) -> None:
        """Verify action can have empty payload."""
        action = ProposedAction(
            action_type="VIEW_PROPOSAL",
            target_resource="proposals",
            payload={},
            actor_id=uuid.uuid4(),
        )

        assert action.payload == {}


class TestPolicyDecision:
    """Tests for PolicyDecision dataclass."""

    def test_creation_with_minimal_data(self) -> None:
        """Verify decision can be created with minimal required data."""
        decision = PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test reason",
        )

        assert decision.outcome == DecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW
        assert decision.reason == "Test reason"
        assert decision.matched_rules == []
        assert decision.requires_approval_from == []
        assert isinstance(decision.timestamp, datetime)

    def test_creation_with_all_data(self) -> None:
        """Verify decision can be created with all fields."""
        rule_id = uuid.uuid4()
        decision = PolicyDecision(
            outcome=DecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=RiskLevel.HIGH,
            reason="Requires approval",
            matched_rules=[rule_id],
            requires_approval_from=["admin", "manager"],
        )

        assert decision.outcome == DecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert decision.risk_level == RiskLevel.HIGH
        assert decision.matched_rules == [rule_id]
        assert decision.requires_approval_from == ["admin", "manager"]

    def test_frozen_dataclass(self) -> None:
        """Verify dataclass is immutable."""
        decision = PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
        )

        with pytest.raises(AttributeError):
            decision.outcome = DecisionOutcome.DENY  # type: ignore[misc]

    def test_timestamp_is_utc(self) -> None:
        """Verify timestamp is in UTC."""
        decision = PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test",
        )

        assert decision.timestamp.tzinfo == UTC

    def test_default_factory_creates_new_lists(self) -> None:
        """Verify default_factory creates independent list instances."""
        decision1 = PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test 1",
        )
        decision2 = PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="Test 2",
        )

        decision1.matched_rules.append(uuid.uuid4())

        assert len(decision1.matched_rules) == 1
        assert len(decision2.matched_rules) == 0
