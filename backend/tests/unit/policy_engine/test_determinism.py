"""
Tests to verify Policy Engine determinism.

Source: 02-ARCHITECTURE.md Section 8.1
"Same input → same output. Always."
"""

from decimal import Decimal

from services.policy_engine.evaluator import evaluate_policy
from tests.unit.policy_engine.fixtures import (
    make_action,
    rule_max_amount_700,
    rule_never_share_phone,
    rule_require_approval_over_200,
)


class TestDeterminism:
    def test_same_input_same_output_allow(self) -> None:
        """Running the same evaluation 100 times must produce identical results."""
        action = make_action(amount=Decimal("100.00"))
        rules = [rule_require_approval_over_200()]
        results = [evaluate_policy(action, rules) for _ in range(100)]
        assert all(r.outcome == results[0].outcome for r in results)
        assert all(r.risk_level == results[0].risk_level for r in results)
        assert all(r.reason == results[0].reason for r in results)

    def test_same_input_same_output_deny(self) -> None:
        action = make_action(data_fields_requested=["phone_number"])
        rules = [rule_never_share_phone()]
        results = [evaluate_policy(action, rules) for _ in range(100)]
        assert all(r.outcome == results[0].outcome for r in results)
        assert all(len(r.matched_rules) == len(results[0].matched_rules) for r in results)

    def test_same_input_same_output_approval(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        rules = [rule_require_approval_over_200()]
        results = [evaluate_policy(action, rules) for _ in range(100)]
        assert all(r.outcome == results[0].outcome for r in results)

    def test_rule_order_does_not_affect_deny_priority(self) -> None:
        """DENY must win regardless of rule order."""
        action = make_action(amount=Decimal("800.00"), data_fields_requested=["phone_number"])
        rules_order_1 = [rule_never_share_phone(), rule_max_amount_700()]
        rules_order_2 = [rule_max_amount_700(), rule_never_share_phone()]
        d1 = evaluate_policy(action, rules_order_1)
        d2 = evaluate_policy(action, rules_order_2)
        assert d1.outcome == d2.outcome  # Both DENY
