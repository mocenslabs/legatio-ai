"""
Unit tests for Pydantic schemas.

Verifies that schemas correctly validate input/output of the Policy Engine
as specified in 04-BUSINESS-FLOW.md Section 7.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.enums import PolicyDecisionOutcome, RiskLevel, RuleAction, RuleOperator
from core.schemas.policy import (
    MatchedRule,
    PolicyDecision,
    ProposedAction,
    RuleCondition,
)


class TestProposedAction:
    """Tests for ProposedAction schema."""

    def test_minimal_valid_action(self) -> None:
        """A minimal ProposedAction must only require action_type."""
        action = ProposedAction(action_type="purchase")
        assert action.action_type == "purchase"
        assert action.amount is None
        assert action.currency is None
        assert action.data_fields_requested == []
        assert action.auto_renewal is False

    def test_full_valid_action(self) -> None:
        """A full ProposedAction with all fields must validate."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            data_fields_requested=["email"],
            contract_length_months=12,
            auto_renewal=False,
            category="travel",
            is_new_vendor=True,
            metadata={"destination": "Madrid"},
        )
        assert action.amount == Decimal("700.00")
        assert action.currency == "EUR"
        assert "email" in action.data_fields_requested

    def test_currency_normalized_to_uppercase(self) -> None:
        """Currency must be normalized to uppercase."""
        action = ProposedAction(action_type="purchase", currency="eur")
        assert action.currency == "EUR"

    def test_invalid_currency_rejected(self) -> None:
        """Invalid currency codes must be rejected."""
        with pytest.raises(ValidationError):
            ProposedAction(action_type="purchase", currency="EURO")

    def test_negative_amount_rejected(self) -> None:
        """Negative amounts must be rejected."""
        with pytest.raises(ValidationError):
            ProposedAction(action_type="purchase", amount=Decimal("-10.00"))

    def test_empty_action_type_rejected(self) -> None:
        """Empty action_type must be rejected."""
        with pytest.raises(ValidationError):
            ProposedAction(action_type="")

    def test_data_fields_stripped(self) -> None:
        """Data fields must be stripped of whitespace."""
        action = ProposedAction(
            action_type="purchase",
            data_fields_requested=["  phone_number  ", " email "],
        )
        assert action.data_fields_requested == ["phone_number", "email"]

    def test_extra_fields_rejected(self) -> None:
        """Extra fields must be rejected (extra='forbid')."""
        with pytest.raises(ValidationError):
            ProposedAction(action_type="purchase", unknown_field="value")  # type: ignore[call-arg]

    def test_use_case_1_travel(self) -> None:
        """Use Case 1: Travel negotiation action."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("820.00"),
            currency="EUR",
            data_fields_requested=[],
            metadata={"nights": 5, "breakfast": True},
        )
        assert action.amount == Decimal("820.00")

    def test_use_case_1_privacy_violation(self) -> None:
        """Use Case 1: Action requesting phone number."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("680.00"),
            currency="EUR",
            data_fields_requested=["phone_number"],
        )
        assert "phone_number" in action.data_fields_requested


class TestMatchedRule:
    """Tests for MatchedRule schema."""

    def test_valid_matched_rule(self) -> None:
        """A valid MatchedRule must validate."""
        rule = MatchedRule(
            rule_id="550e8400-e29b-41d4-a716-446655440000",
            rule_number=17,
            name="Never share phone",
            action=RuleAction.DENY,
            triggered_by="data_fields_requested contains 'phone_number'",
        )
        assert rule.rule_number == 17
        assert rule.action == RuleAction.DENY

    def test_invalid_rule_number_rejected(self) -> None:
        """Rule number must be positive."""
        with pytest.raises(ValidationError):
            MatchedRule(
                rule_id="550e8400-e29b-41d4-a716-446655440000",
                rule_number=0,
                name="Invalid",
                action=RuleAction.DENY,
                triggered_by="test",
            )


class TestPolicyDecision:
    """Tests for PolicyDecision schema."""

    def test_valid_allow_decision(self) -> None:
        """A valid ALLOW decision must validate."""
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="All policy checks passed",
            matched_rules=[],
            evaluation_duration_ms=12,
            engine_version="1.0.0",
        )
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_valid_deny_decision(self) -> None:
        """A valid DENY decision with matched rules must validate."""
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.CRITICAL,
            reason="Blocked by Rule #17: Never share phone",
            matched_rules=[
                MatchedRule(
                    rule_id="550e8400-e29b-41d4-a716-446655440000",
                    rule_number=17,
                    name="Never share phone",
                    action=RuleAction.DENY,
                    triggered_by="data_fields_requested contains 'phone_number'",
                )
            ],
            evaluation_duration_ms=15,
            engine_version="1.0.0",
        )
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert len(decision.matched_rules) == 1

    def test_valid_require_approval_decision(self) -> None:
        """A valid REQUIRE_HUMAN_APPROVAL decision must validate."""
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=RiskLevel.LOW,
            reason="Amount exceeds auto-approve limit",
            matched_rules=[],
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_valid_error_decision(self) -> None:
        """A valid ERROR decision (fail-safe) must validate."""
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.ERROR,
            risk_level=RiskLevel.CRITICAL,
            reason="Policy evaluation failed: malformed rule",
            matched_rules=[],
            evaluation_duration_ms=0,
            engine_version="1.0.0",
        )
        assert decision.outcome == PolicyDecisionOutcome.ERROR

    def test_negative_duration_rejected(self) -> None:
        """Negative evaluation duration must be rejected."""
        with pytest.raises(ValidationError):
            PolicyDecision(
                outcome=PolicyDecisionOutcome.ALLOW,
                risk_level=RiskLevel.LOW,
                reason="test",
                evaluation_duration_ms=-1,
                engine_version="1.0.0",
            )

    def test_empty_reason_rejected(self) -> None:
        """Empty reason must be rejected."""
        with pytest.raises(ValidationError):
            PolicyDecision(
                outcome=PolicyDecisionOutcome.ALLOW,
                risk_level=RiskLevel.LOW,
                reason="",
                evaluation_duration_ms=10,
                engine_version="1.0.0",
            )


class TestRuleCondition:
    """Tests for RuleCondition schema."""

    def test_valid_numeric_condition(self) -> None:
        """A valid numeric condition must validate."""
        condition = RuleCondition(
            field_name="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
        )
        assert condition.field_name == "amount"
        assert condition.operator == RuleOperator.LESS_THAN_OR_EQUAL

    def test_valid_string_condition(self) -> None:
        """A valid string condition must validate."""
        condition = RuleCondition(
            field_name="phone_number",
            operator=RuleOperator.EQUALS,
            value=True,
        )
        assert condition.field_name == "phone_number"

    def test_valid_list_condition(self) -> None:
        """A valid list condition (IN operator) must validate."""
        condition = RuleCondition(
            field_name="category",
            operator=RuleOperator.IN,
            value=["books", "electronics"],
        )
        assert isinstance(condition.value, list)

    def test_null_value_rejected(self) -> None:
        """Null value must be rejected."""
        with pytest.raises(ValidationError):
            RuleCondition(
                field_name="amount",
                operator=RuleOperator.EQUALS,
                value=None,
            )

    def test_empty_field_name_rejected(self) -> None:
        """Empty field name must be rejected."""
        with pytest.raises(ValidationError):
            RuleCondition(
                field_name="",
                operator=RuleOperator.EQUALS,
                value=100,
            )


class TestSchemaIntegration:
    """Integration tests for schema interactions."""

    def test_proposed_action_serialization_roundtrip(self) -> None:
        """ProposedAction must serialize and deserialize correctly."""
        original = ProposedAction(
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            data_fields_requested=["email"],
        )
        json_str = original.model_dump_json()
        restored = ProposedAction.model_validate_json(json_str)
        assert restored.action_type == original.action_type
        assert restored.amount == original.amount

    def test_policy_decision_serialization_roundtrip(self) -> None:
        """PolicyDecision must serialize and deserialize correctly."""
        original = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Test reason",
            matched_rules=[
                MatchedRule(
                    rule_id="test-id",
                    rule_number=1,
                    name="Test Rule",
                    action=RuleAction.DENY,
                    triggered_by="test",
                )
            ],
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        json_str = original.model_dump_json()
        restored = PolicyDecision.model_validate_json(json_str)
        assert restored.outcome == original.outcome
        assert len(restored.matched_rules) == 1
