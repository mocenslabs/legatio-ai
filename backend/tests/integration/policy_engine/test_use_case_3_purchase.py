"""Integration tests for Use Case 3: Purchase Approval."""

from decimal import Decimal
from typing import Any

import pytest

from core.enums import PolicyDecisionOutcome, RiskLevel
from core.schemas.policy import ProposedAction
from services.policy_engine.evaluator import evaluate_policy
from tests.integration.policy_engine.fixtures import purchase_constitution_rules


class TestUseCase3PurchaseApproval:
    @pytest.fixture
    def rules(self) -> list[Any]:
        return purchase_constitution_rules()

    def test_clean_architecture_book_25_eur(self, rules: list[Any]) -> None:
        """€25 book → REQUIRE_APPROVAL (amount 25 > 20 triggers pur-rule-5)."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("25.00"),
            currency="EUR",
            category="books",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_small_purchase_auto_approved(self, rules: list[Any]) -> None:
        """€15 book → ALLOW (under €20 auto-approve limit)."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("15.00"),
            currency="EUR",
            category="books",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_gambling_category_denied(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("25.00"),
            currency="EUR",
            category="gambling",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert any(r.rule_id == "pur-rule-10" for r in decision.matched_rules)

    def test_new_vendor_requires_approval(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("15.00"),
            currency="EUR",
            category="books",
            is_new_vendor=True,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert any(r.rule_id == "pur-rule-15" for r in decision.matched_rules)

    def test_electronics_allowed(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("18.00"),
            currency="EUR",
            category="electronics",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_unknown_category_no_allow_match(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("15.00"),
            currency="EUR",
            category="clothing",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_gambling_and_new_vendor(self, rules: list[Any]) -> None:
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("25.00"),
            currency="EUR",
            category="gambling",
            is_new_vendor=True,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.CRITICAL

    def test_over_max_transaction(self, rules: list[Any]) -> None:
        """€60 purchase → REQUIRE_APPROVAL (amount 60 > 20 triggers pur-rule-5)."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("60.00"),
            currency="EUR",
            category="books",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_boundary_exactly_20_eur(self, rules: list[Any]) -> None:
        """Boundary: amount = €20 (Rule #5: > 20 fails)."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("20.00"),
            currency="EUR",
            category="books",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_boundary_exactly_21_eur(self, rules: list[Any]) -> None:
        """Boundary: amount = €21 (Rule #5: > 20 triggers REQUIRE_APPROVAL)."""
        action = ProposedAction(
            action_type="purchase",
            amount=Decimal("21.00"),
            currency="EUR",
            category="books",
            is_new_vendor=False,
        )
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
