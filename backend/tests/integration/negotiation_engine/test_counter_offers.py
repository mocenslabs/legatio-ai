"""
Integration tests for counter-offer generation logic.
Source: DEL-026 - improve coverage of services.negotiation_engine.counter_offers
"""

from decimal import Decimal

from core.enums import PolicyDecisionOutcome, RiskLevel
from core.schemas.policy import PolicyDecision, ProposedAction
from services.negotiation_engine.counter_offers import generate_counter_offer


class TestGenerateCounterOffer:
    """Tests for generate_counter_offer function."""

    def test_counter_offer_removes_phone_number(self) -> None:
        """When denied for phone_number, counter removes it."""
        original = ProposedAction(
            action_type="purchase",
            amount=Decimal("680"),
            currency="EUR",
            data_fields_requested=["phone_number", "email"],
            terms={"nights": 5},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.CRITICAL,
            reason="Denied by Rule #17: phone_number is not allowed",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert "phone_number" not in counter.data_fields_requested

    def test_counter_offer_reduces_amount(self) -> None:
        """When denied for amount, counter reduces by 10%."""
        original = ProposedAction(
            action_type="purchase",
            amount=Decimal("1000"),
            currency="EUR",
            data_fields_requested=[],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Amount exceeds maximum limit",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.amount == Decimal("900")

    def test_counter_offer_reduces_contract_length(self) -> None:
        """When denied for contract length, counter reduces to max 12."""
        original = ProposedAction(
            action_type="subscribe",
            amount=Decimal("60"),
            currency="EUR",
            contract_length_months=24,
            data_fields_requested=[],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Contract length exceeds maximum",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.contract_length_months == 12

    def test_counter_offer_disables_auto_renewal(self) -> None:
        """When denied for auto-renewal, counter disables it."""
        original = ProposedAction(
            action_type="subscribe",
            amount=Decimal("60"),
            currency="EUR",
            auto_renewal=True,
            data_fields_requested=[],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Auto renewal requires approval",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.auto_renewal is False

    def test_counter_offer_no_amount_does_not_crash(self) -> None:
        """When proposal has no amount, amount adjustment is skipped."""
        original = ProposedAction(
            action_type="share_data",
            amount=None,
            currency=None,
            data_fields_requested=["phone_number"],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Amount exceeds limit and phone_number not allowed",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.amount is None
        assert "phone_number" not in counter.data_fields_requested

    def test_counter_offer_no_contract_length_does_not_crash(self) -> None:
        """When proposal has no contract_length_months, adjustment is skipped."""
        original = ProposedAction(
            action_type="purchase",
            amount=Decimal("100"),
            currency="EUR",
            contract_length_months=None,
            data_fields_requested=[],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Contract length too long",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.contract_length_months is None

    def test_counter_offer_preserves_action_type(self) -> None:
        """Counter-offer preserves the original action type."""
        original = ProposedAction(
            action_type="subscribe",
            amount=Decimal("100"),
            currency="EUR",
            data_fields_requested=[],
            terms={},
        )
        decision = PolicyDecision(
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.HIGH,
            reason="Some reason",
            matched_rules=[],
            evaluation_duration_ms=5,
            engine_version="1.0.0",
        )
        counter = generate_counter_offer(original, decision)
        assert counter.action_type == "subscribe"
