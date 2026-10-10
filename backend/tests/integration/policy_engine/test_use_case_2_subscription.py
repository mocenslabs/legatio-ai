"""Integration tests for Use Case 2: Subscription Negotiation."""

from decimal import Decimal
from typing import Any

import pytest

from core.enums import PolicyDecisionOutcome, RiskLevel
from core.schemas.policy import ProposedAction
from services.policy_engine.evaluator import evaluate_policy
from tests.integration.policy_engine.fixtures import subscription_constitution_rules


class TestUseCase2SubscriptionNegotiation:
    @pytest.fixture
    def rules(self) -> list[Any]:
        return subscription_constitution_rules()

    def test_initial_offer_60_eur_24_months_auto_renewal(self, rules: list[Any]) -> None:
        """€60/month, 24 months, auto-renewal → REQUIRE_APPROVAL (auto-renewal)."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("60.00"),
            currency="EUR",
            contract_length_months=24,
            auto_renewal=True,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert any(r.rule_id == "sub-rule-15" for r in decision.matched_rules)

    def test_counter_70_eur_12_months_no_auto_renewal(self, rules: list[Any]) -> None:
        """€70/month, 12 months, no auto-renewal → REQUIRE_APPROVAL (amount 70 > 50)."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("70.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_small_subscription_auto_approved(self, rules: list[Any]) -> None:
        """€40/month, 12 months, no auto-renewal → ALLOW."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("40.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_price_increase_triggers_approval(self, rules: list[Any]) -> None:
        """€50/month with 15% price increase → REQUIRE_APPROVAL."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("50.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
            price_increase_pct=Decimal("15.0"),
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert any(r.rule_id == "sub-rule-20" for r in decision.matched_rules)

    def test_small_price_increase_allowed(self, rules: list[Any]) -> None:
        """€50/month with 5% price increase → ALLOW (under 10% threshold)."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("50.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
            price_increase_pct=Decimal("5.0"),
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_over_max_monthly_spend(self, rules: list[Any]) -> None:
        """€150/month → REQUIRE_APPROVAL (amount 150 > 50 triggers sub-rule-5)."""
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("150.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
        )
        decision = evaluate_policy(action, rules)
        # 150 > 50 triggers REQUIRE_APPROVAL
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_contract_length_boundary_12_months(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("40.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_combined_auto_renewal_and_price_increase(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="subscribe",
            amount=Decimal("70.00"),
            currency="EUR",
            contract_length_months=12,
            auto_renewal=True,
            price_increase_pct=Decimal("15.0"),
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        matched_ids = {r.rule_id for r in decision.matched_rules}
        assert "sub-rule-15" in matched_ids
        assert "sub-rule-20" in matched_ids
