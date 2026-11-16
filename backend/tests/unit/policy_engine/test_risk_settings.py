"""Tests that risk amount thresholds are configurable via Django settings."""

from decimal import Decimal

from django.test import override_settings

from core.enums import RiskLevel
from services.policy_engine.evaluator import _risk_thresholds, assess_risk
from tests.unit.policy_engine.fixtures import make_action


@override_settings(RISK_HIGH_AMOUNT_THRESHOLD=100, RISK_CRITICAL_AMOUNT_THRESHOLD=200)
def test_thresholds_read_from_settings() -> None:
    high, critical = _risk_thresholds()
    assert high == 100
    assert critical == 200


@override_settings(RISK_HIGH_AMOUNT_THRESHOLD=100, RISK_CRITICAL_AMOUNT_THRESHOLD=200)
def test_assess_risk_respects_custom_high_threshold() -> None:
    action = make_action(amount=Decimal("150"))
    assert assess_risk(action, []) == RiskLevel.HIGH


@override_settings(RISK_HIGH_AMOUNT_THRESHOLD=100, RISK_CRITICAL_AMOUNT_THRESHOLD=200)
def test_assess_risk_respects_custom_critical_threshold() -> None:
    action = make_action(amount=Decimal("250"))
    assert assess_risk(action, []) == RiskLevel.CRITICAL


@override_settings(RISK_HIGH_AMOUNT_THRESHOLD=100, RISK_CRITICAL_AMOUNT_THRESHOLD=200)
def test_assess_risk_below_custom_high_is_low() -> None:
    action = make_action(amount=Decimal("50"))
    assert assess_risk(action, []) == RiskLevel.LOW


def test_default_thresholds_unchanged() -> None:
    """Without override, defaults remain 500 / 1000."""
    high, critical = _risk_thresholds()
    assert high == 500
    assert critical == 1000
