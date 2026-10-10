"""
Unit tests for safe_evaluate.

Source: 04-BUSINESS-FLOW.md Section 7.4 and 11.1
"""

from unittest.mock import patch

from core.enums import PolicyDecisionOutcome, RiskLevel
from services.policy_engine.evaluator import safe_evaluate
from tests.unit.policy_engine.fixtures import make_action


class TestSafeEvaluate:
    def test_returns_decision_on_success(self) -> None:
        action = make_action()
        decision = safe_evaluate(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_returns_error_on_exception(self) -> None:
        """Any exception must return ERROR outcome, never raise."""
        with patch("services.policy_engine.evaluator.evaluate_policy") as mock_eval:
            mock_eval.side_effect = RuntimeError("Unexpected failure")
            action = make_action()
            decision = safe_evaluate(action, [])
            assert decision.outcome == PolicyDecisionOutcome.ERROR
            assert decision.risk_level == RiskLevel.CRITICAL
            assert "Unexpected failure" in decision.reason

    def test_never_raises(self) -> None:
        """safe_evaluate must never raise, regardless of input."""
        # This should not raise even with weird inputs
        decision = safe_evaluate(make_action(), [])
        assert decision.outcome in [
            PolicyDecisionOutcome.ALLOW,
            PolicyDecisionOutcome.DENY,
            PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            PolicyDecisionOutcome.ERROR,
        ]

    def test_error_has_engine_version(self) -> None:
        with patch("services.policy_engine.evaluator.evaluate_policy") as mock_eval:
            mock_eval.side_effect = ValueError("test")
            decision = safe_evaluate(make_action(), [])
            assert decision.engine_version == "1.0.0"

    def test_error_has_zero_duration(self) -> None:
        with patch("services.policy_engine.evaluator.evaluate_policy") as mock_eval:
            mock_eval.side_effect = ValueError("test")
            decision = safe_evaluate(make_action(), [])
            assert decision.evaluation_duration_ms == 0

    def test_error_has_empty_matched_rules(self) -> None:
        with patch("services.policy_engine.evaluator.evaluate_policy") as mock_eval:
            mock_eval.side_effect = ValueError("test")
            decision = safe_evaluate(make_action(), [])
            assert decision.matched_rules == []
