"""
Unit tests for assess_risk.

Source: 04-BUSINESS-FLOW.md Section 7.3
"""

from decimal import Decimal

from core.enums import RiskLevel, RuleAction
from core.schemas.policy import MatchedRule
from services.policy_engine.evaluator import assess_risk
from tests.unit.policy_engine.fixtures import make_action


def _matched(action: RuleAction = RuleAction.ALLOW) -> MatchedRule:
    return MatchedRule(
        rule_id="test",
        rule_number=1,
        name="Test",
        action=action,
        triggered_by="test",
    )


class TestAssessRisk:
    def test_low_risk_no_matches(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        assert assess_risk(action, []) == RiskLevel.LOW

    def test_low_risk_small_amount(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        assert assess_risk(action, [_matched(RuleAction.ALLOW)]) == RiskLevel.LOW

    def test_medium_risk_require_approval(self) -> None:
        action = make_action(amount=Decimal("300.00"))
        assert assess_risk(action, [_matched(RuleAction.REQUIRE_APPROVAL)]) == RiskLevel.MEDIUM

    def test_high_risk_amount_500(self) -> None:
        action = make_action(amount=Decimal("500.00"))
        assert assess_risk(action, [_matched(RuleAction.REQUIRE_APPROVAL)]) == RiskLevel.HIGH

    def test_high_risk_amount_999(self) -> None:
        action = make_action(amount=Decimal("999.00"))
        assert assess_risk(action, []) == RiskLevel.HIGH

    def test_critical_risk_amount_1000(self) -> None:
        action = make_action(amount=Decimal("1000.00"))
        assert assess_risk(action, []) == RiskLevel.CRITICAL

    def test_critical_risk_deny_matched(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        assert assess_risk(action, [_matched(RuleAction.DENY)]) == RiskLevel.CRITICAL

    def test_critical_risk_deny_overrides_amount(self) -> None:
        """DENY matched → CRITICAL regardless of amount."""
        action = make_action(amount=Decimal("10.00"))
        assert assess_risk(action, [_matched(RuleAction.DENY)]) == RiskLevel.CRITICAL

    def test_no_amount_with_approval(self) -> None:
        action = make_action(amount=None)
        assert assess_risk(action, [_matched(RuleAction.REQUIRE_APPROVAL)]) == RiskLevel.MEDIUM
