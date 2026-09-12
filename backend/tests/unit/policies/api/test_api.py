"""Integration tests for policy API endpoints."""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.policies.models import PolicyRule, RuleActionType


@pytest.fixture
def api_client() -> APIClient:
    user = User.objects.create_user(email="test@example.com", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestPolicyRuleAPI:
    def test_list_policy_rules(self, api_client: APIClient) -> None:
        PolicyRule.objects.create(
            name="Rule 1",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
        )
        PolicyRule.objects.create(
            name="Rule 2",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.DENY,
        )
        url = reverse("policyrule-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_create_policy_rule(self, api_client: APIClient) -> None:
        url = reverse("policyrule-list")
        data = {
            "name": "New Rule",
            "condition": {"field": "amount", "operator": ">", "value": 1000},
            "action_type": "DENY",
            "risk_level": "HIGH",
            "priority": 10,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Rule"

    def test_filter_by_action_type(self, api_client: APIClient) -> None:
        PolicyRule.objects.create(
            name="Allow Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
        )
        PolicyRule.objects.create(
            name="Deny Rule",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.DENY,
        )
        url = reverse("policyrule-list")
        response = api_client.get(url, {"action_type": "DENY"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["action_type"] == "DENY"

    def test_filter_by_risk_level(self, api_client: APIClient) -> None:
        PolicyRule.objects.create(
            name="Low Risk",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
            risk_level="LOW",
        )
        PolicyRule.objects.create(
            name="High Risk",
            condition={"field": "test", "operator": "==", "value": "value"},
            action_type=RuleActionType.ALLOW,
            risk_level="HIGH",
        )
        url = reverse("policyrule-list")
        response = api_client.get(url, {"risk_level": "HIGH"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["risk_level"] == "HIGH"


@pytest.mark.django_db
class TestPolicyEvaluationAPI:
    def test_evaluate_action_allow(self, api_client: APIClient) -> None:
        url = reverse("policy-evaluate")
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 500},
            "actor_id": str(uuid.uuid4()),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["outcome"] == "ALLOW"

    def test_evaluate_action_deny(self, api_client: APIClient) -> None:
        PolicyRule.objects.create(
            name="Deny High Amount",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
        )
        url = reverse("policy-evaluate")
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["outcome"] == "DENY"
        assert response.data["risk_level"] == "HIGH"

    def test_evaluate_action_require_approval(self, api_client: APIClient) -> None:
        PolicyRule.objects.create(
            name="Require Approval",
            condition={"field": "payload.amount", "operator": ">", "value": 1000},
            action_type=RuleActionType.REQUIRE_APPROVAL,
            risk_level="MEDIUM",
            priority=10,
            requires_approval_from=["manager"],
        )
        url = reverse("policy-evaluate")
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["outcome"] == "REQUIRE_HUMAN_APPROVAL"
        assert "manager" in response.data["requires_approval_from"]

    def test_evaluate_action_with_constitution_scope(self, api_client: APIClient) -> None:
        from apps.constitutions.models import Constitution

        constitution = Constitution.objects.create(name="Test Constitution")
        PolicyRule.objects.create(
            name="Scoped Deny",
            condition={"field": "payload.amount", "operator": ">", "value": 0},
            action_type=RuleActionType.DENY,
            risk_level="HIGH",
            priority=10,
            constitution=constitution,
        )
        url = reverse("policy-evaluate")
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 1000},
            "actor_id": str(uuid.uuid4()),
            "constitution_id": str(constitution.id),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["outcome"] == "DENY"

    def test_evaluate_action_invalid_request(self, api_client: APIClient) -> None:
        url = reverse("policy-evaluate")
        data = {
            "action_type": "",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_evaluate_action_unauthenticated(self) -> None:
        client = APIClient()
        url = reverse("policy-evaluate")
        data = {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": str(uuid.uuid4()),
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
