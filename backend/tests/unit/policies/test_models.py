"""Unit tests for policy and constitution models.

Tests cover model creation, validation, and string representations.
"""

from __future__ import annotations

import uuid

import pytest
from django.db import IntegrityError

from apps.constitutions.models import Constitution
from apps.policies.models import PolicyRule, RuleActionType


@pytest.mark.django_db
class TestConstitution:
    """Tests for Constitution model."""

    def test_create_minimal(self) -> None:
        """Verify constitution can be created with minimal fields."""
        constitution = Constitution.objects.create(name="Test Constitution")

        assert constitution.name == "Test Constitution"
        assert constitution.description == ""
        assert constitution.is_active is True
        assert isinstance(constitution.id, uuid.UUID)

    def test_create_with_all_fields(self) -> None:
        """Verify constitution can be created with all fields."""
        constitution = Constitution.objects.create(
            name="Full Constitution",
            description="A complete governance framework",
            is_active=False,
        )

        assert constitution.name == "Full Constitution"
        assert constitution.description == "A complete governance framework"
        assert constitution.is_active is False

    def test_str_representation(self) -> None:
        """Verify string representation returns name."""
        constitution = Constitution.objects.create(name="My Constitution")

        assert str(constitution) == "My Constitution"

    def test_unique_name_constraint(self) -> None:
        """Verify name must be unique."""
        Constitution.objects.create(name="Unique Name")

        with pytest.raises(IntegrityError):
            Constitution.objects.create(name="Unique Name")

    def test_ordering(self) -> None:
        """Verify constitutions are ordered by created_at descending."""
        const1 = Constitution.objects.create(name="First")
        const2 = Constitution.objects.create(name="Second")

        constitutions = list(Constitution.objects.all())

        assert constitutions[0].id == const2.id
        assert constitutions[1].id == const1.id


@pytest.mark.django_db
class TestPolicyRule:
    """Tests for PolicyRule model."""

    def test_create_minimal(self) -> None:
        """Verify rule can be created with minimal required fields."""
        rule = PolicyRule.objects.create(
            name="Test Rule",
            condition={"field": "amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.DENY,
        )

        assert rule.name == "Test Rule"
        assert rule.condition == {"field": "amount", "operator": ">", "value": 1000}
        assert rule.action_type == RuleActionType.DENY
        assert rule.risk_level == "LOW"
        assert rule.priority == 100
        assert rule.is_active is True
        assert rule.constitution is None
        assert rule.requires_approval_from == []

    def test_create_with_all_fields(self) -> None:
        """Verify rule can be created with all fields."""
        constitution = Constitution.objects.create(name="Test Constitution")
        rule = PolicyRule.objects.create(
            name="Complete Rule",
            description="A fully specified rule",
            condition={"field": "actor.role", "operator": "==", "value": "admin"},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="HIGH",
            requires_approval_from=["manager", "director"],
            priority=50,
            is_active=False,
            constitution=constitution,
        )

        assert rule.name == "Complete Rule"
        assert rule.description == "A fully specified rule"
        assert rule.action_type == RuleActionType.REQUIRE_APPROVAL
        assert rule.risk_level == "HIGH"
        assert rule.requires_approval_from == ["manager", "director"]
        assert rule.priority == 50
        assert rule.is_active is False
        assert rule.constitution == constitution

    def test_str_representation(self) -> None:
        """Verify string representation includes name and action type."""
        rule = PolicyRule.objects.create(
            name="My Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
        )

        assert str(rule) == "My Rule (ALLOW)"

    def test_unique_name_constraint(self) -> None:
        """Verify name must be unique."""
        PolicyRule.objects.create(
            name="Unique Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
        )

        with pytest.raises(IntegrityError):
            PolicyRule.objects.create(
                name="Unique Rule",
                condition={"field": "test2", "operator": "==", "value": "value2"},
                action_type=RuleActionType.DENY,
            )

    def test_ordering_by_priority(self) -> None:
        """Verify rules are ordered by priority then created_at."""
        rule1 = PolicyRule.objects.create(
            name="Low Priority",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
            priority=200,
        )
        rule2 = PolicyRule.objects.create(
            name="High Priority",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.DENY,
            priority=10,
        )

        rules = list(PolicyRule.objects.all())

        assert rules[0].id == rule2.id
        assert rules[1].id == rule1.id

    def test_action_type_choices(self) -> None:
        """Verify all action types can be used."""
        for action_type in RuleActionType.values:
            rule = PolicyRule.objects.create(
                name=f"Rule {action_type}",
                condition={"field": "test", "operator": "==", "value": "value"},
                action_type=action_type,
            )
            assert rule.action_type == action_type

    def test_risk_level_choices(self) -> None:
        """Verify all risk levels can be used."""
        for risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            rule = PolicyRule.objects.create(
                name=f"Rule {risk_level}",
                condition={"field": "test", "operator": "==", "value": "value"},
                action_type=RuleActionType.ALLOW,
                risk_level=risk_level,
            )
            assert rule.risk_level == risk_level

    def test_cascade_delete_with_constitution(self) -> None:
        """Verify rules are deleted when constitution is deleted."""
        constitution = Constitution.objects.create(name="To Delete")
        rule = PolicyRule.objects.create(
            name="Linked Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
            constitution=constitution,
        )

        rule_id = rule.id
        constitution.delete()

        assert not PolicyRule.objects.filter(id=rule_id).exists()
