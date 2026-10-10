"""Performance tests for the Policy Engine."""

import time
from decimal import Decimal

from core.enums import RuleOperator
from services.policy_engine.evaluator import evaluate_policy
from tests.unit.policy_engine.fixtures import make_action, make_condition, make_rule


class TestPerformance:
    def test_100_rules_under_50ms(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        rules = [
            make_rule(
                rule_id=f"perf-rule-{i}",
                rule_number=i + 1,
                name=f"Performance Rule {i}",
                conditions=[
                    make_condition("amount", RuleOperator.GREATER_THAN, 10000),
                ],
            )
            for i in range(100)
        ]
        start = time.monotonic()
        _ = evaluate_policy(action, rules)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        assert elapsed_ms < 50, f"Evaluation took {elapsed_ms}ms, expected < 50ms"

    def test_1000_rules_under_500ms(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        rules = [
            make_rule(
                rule_id=f"stress-rule-{i}",
                rule_number=i + 1,
                name=f"Stress Rule {i}",
                conditions=[
                    make_condition("amount", RuleOperator.GREATER_THAN, 10000),
                ],
            )
            for i in range(1000)
        ]
        start = time.monotonic()
        _ = evaluate_policy(action, rules)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        assert elapsed_ms < 500, f"Evaluation took {elapsed_ms}ms, expected < 500ms"
