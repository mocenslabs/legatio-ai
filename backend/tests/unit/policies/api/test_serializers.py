"""Unit tests for policy serializers."""

from __future__ import annotations

import uuid

import pytest
from rest_framework.exceptions import ValidationError

from apps.policies.models import PolicyRule, RuleActionType
from apps.policies.serializers import (
    PolicyEvaluationRequestSerializer,
    PolicyRuleSerializer,
)


@pytest.mark.django_db
class TestPolicyRuleSerializer:
    def test_valid_creation(self) -> None:
        data = {
            "name": "Test Rule",
            "description": "A test rule",
            "condition": {"field": "amount", "operator": ">", "value": 1000},
            "action_type": "DENY",
            "risk_level": "HIGH",
            "priority": 10,
            "is_active": True,
        }
        serializer = PolicyRuleSerializer(data=data)
        assert serializer.is_valid()

    def test_unique_name_validation(self) -> None:
        PolicyRule.objects.create(
            name="Existing Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
        )
        data = {
            "name": "Existing Rule",
            "condition": {"field": "test2", "operator": "==", "value": "value2"},
            "action_type": "DENY",
        }
        serializer = PolicyRuleSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "name" in exc_info.value.detail

    def test_condition_missing_field(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"operator": ">", "value": 1000},
            "action_type": "DENY",
        }
        serializer = PolicyRuleSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "condition" in exc_info.value.detail

    def test_condition_invalid_operator(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"field": "amount", "operator": "invalid", "value": 1000},
            "action_type": "DENY",
        }
        serializer = PolicyRuleSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "condition" in exc_info.value.detail

    def test_condition_missing_value_for_non_exists_operator(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"field": "amount", "operator": ">"},
            "action_type": "DENY",
        }
        serializer = PolicyRuleSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "condition" in exc_info.value.detail

    def test_condition_exists_operator_no_value_required(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"field": "optional_field", "operator": "exists"},
            "action_type": "ALLOW",
        }
        serializer = PolicyRuleSerializer(data=data)
        assert serializer.is_valid()

    def test_require_approval_without_approvers(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"field": "amount", "operator": ">", "value": 1000},
            "action_type": "REQUIRE_APPROVAL",
            "requires_approval_from": [],
        }
        serializer = PolicyRuleSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "requires_approval_from" in exc_info.value.detail

    def test_require_approval_with_approvers(self) -> None:
        data = {
            "name": "Test Rule",
            "condition": {"field": "amount", "operator": ">", "value": 1000},
            "action_type": "REQUIRE_APPROVAL",
            "requires_approval_from": ["manager", "director"],
        }
        serializer = PolicyRuleSerializer(data=data)
        assert serializer.is_valid()


class TestPolicyEvaluationRequestSerializer:
    def test_valid_request(self) -> None:
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        serializer = PolicyEvaluationRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_valid_request_with_constitution(self) -> None:
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
            "constitution_id": str(uuid.uuid4()),
        }
        serializer = PolicyEvaluationRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_empty_action_type(self) -> None:
        data = {
            "action_type": "",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        serializer = PolicyEvaluationRequestSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "action_type" in exc_info.value.detail

    def test_empty_target_resource(self) -> None:
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        serializer = PolicyEvaluationRequestSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "target_resource" in exc_info.value.detail

    def test_invalid_actor_id(self) -> None:
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": "not-a-uuid",
        }
        serializer = PolicyEvaluationRequestSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "actor_id" in exc_info.value.detail
