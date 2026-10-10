"""
End-to-end tests for the complete Constitution lifecycle.
Simulates a real user interacting with the API to build, version,
and activate a constitution.
Source: 05-ROADMAP.md Section 6.4
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from core.enums import AgentType, ConstitutionStatus

User = get_user_model()


@pytest.mark.django_db
class TestConstitutionE2EFlow:
    """End-to-end flow for creating and activating a constitution."""

    def test_full_constitution_lifecycle(self) -> None:
        """
        Scenario: User creates an agent, builds a constitution with rules,
        creates a new version, and activates it.
        """
        # 1. Setup: Create user, authenticate, and create agent via ORM
        # (Agents API is not fully exposed yet, DEL-020)
        user = User.objects.create_user(email="e2e@example.com", password="e2e1234")
        agent = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="E2E Travel Agent",
            description="For testing",
        )

        client = APIClient()
        from apps.accounts.services.auth import generate_access_token

        token = generate_access_token(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 2. Create Constitution with Rules (Atomic Builder)
        rules_payload = [
            {
                "rule_number": 1,
                "name": "Max transaction",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
            },
            {
                "rule_number": 17,
                "name": "Never share phone",
                "category": "PRIVACY",
                "field": "data_fields_requested",
                "operator": "CONTAINS",
                "value": "phone_number",
                "action": "DENY",
            },
        ]
        const_response = client.post(
            "/api/v1/constitutions/with-rules/",
            {
                "agent_id": str(agent.id),
                "name": "Madrid Travel Rules",
                "description": "Rules for hotel booking",
                "rules": rules_payload,
            },
            format="json",
        )
        assert const_response.status_code == status.HTTP_201_CREATED
        constitution_id = const_response.data["constitution"]["id"]
        version_data = const_response.data["version"]
        assert version_data is not None
        version_1_id = str(version_data["id"])
        assert const_response.data["rules_count"] == 2

        # 3. Verify initial state
        constitution = Constitution.objects.get(id=constitution_id)
        assert constitution.status == ConstitutionStatus.DRAFT
        assert constitution.active_version is None

        # 4. Activate Version 1
        activate_response = client.post(
            f"/api/v1/constitutions/{constitution_id}/activate/",
            {"version_id": version_1_id},
            format="json",
        )
        assert activate_response.status_code == status.HTTP_200_OK
        assert activate_response.data["constitution"]["status"] == "ACTIVE"
        constitution.refresh_from_db()
        assert constitution.status == ConstitutionStatus.ACTIVE
        assert constitution.active_version is not None
        assert str(constitution.active_version.id) == version_1_id

        # 5. Verify we CANNOT modify active version rules
        rule_add_response = client.post(
            f"/api/v1/constitutions/{constitution_id}/rules/",
            {
                "version_id": version_1_id,
                "rule_number": 23,
                "name": "Large payments",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "GREATER_THAN",
                "value": 200,
                "action": "REQUIRE_APPROVAL",
            },
            format="json",
        )
        assert rule_add_response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "active" in rule_add_response.data["error"].lower()
            or "immutable" in rule_add_response.data["error"].lower()
        )

        # 6. Verify Audit Events were created
        from apps.audit.models import AuditEvent

        audit_events = AuditEvent.objects.filter(
            entity_type__in=["Constitution", "ConstitutionVersion", "PolicyRule"]
        )
        assert audit_events.count() >= 4

    def test_e2e_policy_engine_integration(self) -> None:
        """
        Scenario: After activating a constitution, the Policy Engine
        correctly evaluates a proposal using those rules.
        """
        from decimal import Decimal

        from apps.constitutions.services import activate_version, create_constitution_with_rules
        from core.schemas.policy import ProposedAction
        from services.policy_engine.evaluator import evaluate_policy
        from services.policy_engine.loader import load_active_rules_for_agent

        user = User.objects.create_user(email="pe2e@example.com", password="pass")
        agent = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="PE2E Agent",
        )
        rules = [
            {
                "rule_number": 1,
                "name": "Max 700",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
            },
            {
                "rule_number": 17,
                "name": "No phone",
                "category": "PRIVACY",
                "field": "data_fields_requested",
                "operator": "CONTAINS",
                "value": "phone_number",
                "action": "DENY",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=agent,
            name="PE2E Rules",
            description=None,
            rules=rules,
            user=user,
        )
        activate_version(version=version, user=user)

        loaded_rules = load_active_rules_for_agent(agent)
        assert len(loaded_rules) == 2

        # Test DENY scenario
        action_deny = ProposedAction(
            action_type="purchase",
            amount=Decimal("600.00"),
            data_fields_requested=["phone_number"],
        )
        decision_deny = evaluate_policy(action_deny, loaded_rules)
        assert decision_deny.outcome.value == "DENY"
        assert decision_deny.risk_level.value == "CRITICAL"

        # Test ALLOW scenario
        action_allow = ProposedAction(
            action_type="purchase",
            amount=Decimal("500.00"),
            data_fields_requested=[],
        )
        decision_allow = evaluate_policy(action_allow, loaded_rules)
        assert decision_allow.outcome.value == "ALLOW"
