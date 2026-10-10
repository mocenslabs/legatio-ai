"""Unit tests for evaluate_policy."""

from decimal import Decimal

from core.enums import PolicyDecisionOutcome, RiskLevel, RuleAction, RuleOperator
from services.policy_engine.evaluator import evaluate_policy
from tests.unit.policy_engine.fixtures import (
    make_action,
    make_condition,
    make_rule,
    rule_max_amount_700,
    rule_max_contract_12_months,
    rule_never_share_phone,
    rule_no_auto_renewal,
    rule_require_approval_over_200,
    use_case_1_privacy_violation_action,
    use_case_1_travel_action,
    use_case_2_subscription_action,
    use_case_3_purchase_action,
)


class TestAllowOutcome:
    def test_allow_when_no_rules_match(self) -> None:
        action = make_action(amount=Decimal("50.00"))
        rules = [rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW
        assert decision.risk_level == RiskLevel.LOW

    def test_allow_when_all_rules_pass(self) -> None:
        action = make_action(amount=Decimal("100.00"))
        rules = [
            make_rule(
                rule_number=1,
                action=RuleAction.ALLOW,
                conditions=[make_condition("amount", RuleOperator.LESS_THAN_OR_EQUAL, 1000)],
            ),
        ]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW

    def test_allow_with_empty_rules(self) -> None:
        action = make_action()
        decision = evaluate_policy(action, [])
        assert decision.outcome == PolicyDecisionOutcome.ALLOW


class TestDenyOutcome:
    def test_deny_phone_number(self) -> None:
        action = use_case_1_privacy_violation_action()
        rules = [rule_never_share_phone(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert decision.risk_level == RiskLevel.CRITICAL
        assert len(decision.matched_rules) >= 1
        assert any(r.rule_id == "rule-17" for r in decision.matched_rules)

    def test_deny_amount_over_700(self) -> None:
        action = use_case_1_travel_action()
        rules = [rule_max_amount_700(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY

    def test_deny_has_immediate_priority(self) -> None:
        action = make_action(amount=Decimal("800.00"), data_fields_requested=["phone_number"])
        rules = [rule_never_share_phone(), rule_max_amount_700()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert len(decision.matched_rules) == 1
        assert decision.matched_rules[0].rule_id == "rule-17"


class TestRequireApprovalOutcome:
    def test_require_approval_over_200(self) -> None:
        """Amount 300 > 200 triggers REQUIRE_APPROVAL; 300 < 500 → MEDIUM risk."""
        action = make_action(amount=Decimal("300.00"), data_fields_requested=[])
        rules = [rule_never_share_phone(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL
        assert decision.risk_level == RiskLevel.MEDIUM

    def test_require_approval_with_allow_rules(self) -> None:
        action = make_action(amount=Decimal("300.00"))
        rules = [
            make_rule(
                rule_number=1,
                action=RuleAction.ALLOW,
                conditions=[make_condition("amount", RuleOperator.LESS_THAN_OR_EQUAL, 1000)],
            ),
            rule_require_approval_over_200(),
        ]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL


class TestUseCaseScenarios:
    def test_use_case_1_round_1(self) -> None:
        action = use_case_1_travel_action()
        rules = [rule_never_share_phone(), rule_max_amount_700(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY

    def test_use_case_1_round_2(self) -> None:
        action = use_case_1_privacy_violation_action()
        rules = [rule_never_share_phone(), rule_max_amount_700(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY
        assert any(r.rule_id == "rule-17" for r in decision.matched_rules)

    def test_use_case_1_round_3(self) -> None:
        action = make_action(amount=Decimal("700.00"), currency="EUR", data_fields_requested=[])
        rules = [rule_never_share_phone(), rule_max_amount_700(), rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL

    def test_use_case_2_auto_renewal_denied(self) -> None:
        action = use_case_2_subscription_action()
        rules = [rule_no_auto_renewal(), rule_max_contract_12_months()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.DENY

    def test_use_case_3_small_purchase_allowed(self) -> None:
        action = use_case_3_purchase_action()
        rules = [rule_require_approval_over_200()]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW


class TestInactiveRules:
    def test_inactive_rules_ignored(self) -> None:
        action = make_action(data_fields_requested=["phone_number"])
        deny_rule = rule_never_share_phone()
        deny_rule.is_active = False
        rules = [deny_rule]
        decision = evaluate_policy(action, rules)
        assert decision.outcome == PolicyDecisionOutcome.ALLOW


class TestDecisionMetadata:
    def test_decision_has_engine_version(self) -> None:
        action = make_action()
        decision = evaluate_policy(action, [])
        assert decision.engine_version == "1.0.0"

    def test_decision_has_duration(self) -> None:
        action = make_action()
        decision = evaluate_policy(action, [])
        assert decision.evaluation_duration_ms >= 0

    def test_decision_has_reason(self) -> None:
        action = make_action()
        decision = evaluate_policy(action, [])
        assert len(decision.reason) > 0

    def test_deny_reason_includes_rule_info(self) -> None:
        action = use_case_1_privacy_violation_action()
        rules = [rule_never_share_phone()]
        decision = evaluate_policy(action, rules)
        assert "Rule #17" in decision.reason
