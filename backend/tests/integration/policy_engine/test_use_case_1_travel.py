"""Integration tests for Use Case 1: AI Travel Negotiation."""

from decimal import Decimal
from typing import Any

import pytest

from core.enums import PolicyDecisionOutcome, RiskLevel
from core.schemas.policy import ProposedAction
from services.policy_engine.evaluator import evaluate_policy, safe_evaluate
from tests.integration.policy_engine.fixtures import travel_constitution_rules


class TestUseCase1TravelNegotiation:
    @pytest.fixture
    def rules(self) -> list[Any]:
        return travel_constitution_rules()

    def test_round_1_initial_offer_820_eur(self, rules: list[Any]) -> None:
        """Round 1: €820, no phone → REQUIRE_APPROVAL.
        Risk is HIGH because amount 820 > 500 (RISK_HIGH_AMOUNT_THRESHOLD).
        """
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("820.00"),
            currency="EUR",
            data_fields_requested=[],
            metadata={"nights": 5, "breakfast": True},
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        # 820 > 500 → HIGH risk (amount-based, not rule-based)
        assert decision.risk_level == RiskLevel.HIGH
        assert "Rule #23" in decision.reason

    def test_round_2_counter_680_with_phone_denied(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("680.00"),
            currency="EUR",
            data_fields_requested=["phone_number"],
            metadata={"nights": 5},
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.CRITICAL
        assert "Rule #17" in decision.reason

    def test_round_2_deny_has_immediate_priority(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("680.00"),
            currency="EUR",
            data_fields_requested=["phone_number"],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert any(r.rule_id == "travel-rule-17" for r in decision.matched_rules)

    def test_round_3_final_offer_700_no_phone(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            data_fields_requested=[],
            metadata={"nights": 5, "cancellation": "48h"},
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_round_3_boundary_exactly_700(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            data_fields_requested=[],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_round_3_boundary_701_denied(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("701.00"),
            currency="EUR",
            data_fields_requested=[],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_email_sharing_allowed(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            data_fields_requested=["email"],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_phone_and_email_together_denied(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("100.00"),
            currency="EUR",
            data_fields_requested=["email", "phone_number"],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert any(r.rule_id == "travel-rule-17" for r in decision.matched_rules)

    def test_small_amount_no_phone_allowed(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("150.00"),
            currency="EUR",
            data_fields_requested=[],
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_safe_evaluate_never_fails(self, rules: list[Any]) -> None:
        action = ProposedAction(action_type="purchase", amount=Decimal("700.00"), currency="EUR")
        decision = safe_evaluate(action, rules)
        assert decision.outcome in [
            PolicyDecisionOutcome.ALLOW,
            PolicyDecisionOutcome.DENY,
            PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            PolicyDecisionOutcome.ERROR,
        ]
