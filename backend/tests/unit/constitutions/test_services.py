"""
Unit tests for Constitution services.

Source: 04-BUSINESS-FLOW.md Section 8.5
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from pydantic import ValidationError

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, PolicyRule
from apps.constitutions.services import (
    activate_version,
    add_rule,
    create_constitution,
    create_constitution_with_rules,
    create_version,
)
from core.enums import AgentType, ConstitutionStatus, RuleAction, RuleCategory, RuleOperator
from core.exceptions import ConstitutionImmutableError, MultipleActiveConstitutionsError

User = get_user_model()


@pytest.fixture
def user() -> Any:
    """Create a test user."""
    return User.objects.create_user(email="user@example.com", password="pass")


@pytest.fixture
def agent(user: Any) -> Any:
    """Create a test agent."""
    return Agent.objects.create(
        owner=user,
        agent_type=AgentType.USER_AGENT,
        name="Test Agent",
    )


@pytest.mark.django_db
class TestCreateConstitution:
    def test_create_constitution(self, user: Any, agent: Any) -> None:
        """Constitution can be created."""
        constitution = create_constitution(
            agent=agent,
            name="Travel Constitution",
            description="Rules for travel",
            user=user,
        )
        assert constitution.agent == agent
        assert constitution.name == "Travel Constitution"
        assert constitution.status == ConstitutionStatus.DRAFT

    def test_create_constitution_creates_audit_event(self, user: Any, agent: Any) -> None:
        """Creating a constitution creates an audit event."""
        from apps.audit.models import AuditEvent

        initial_count = AuditEvent.objects.count()
        create_constitution(
            agent=agent,
            name="Test",
            user=user,
        )
        assert AuditEvent.objects.count() == initial_count + 1


@pytest.mark.django_db
class TestCreateVersion:
    def test_create_first_version(self, user: Any, agent: Any) -> None:
        """First version gets number 1."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        assert version.version_number == 1

    def test_create_second_version(self, user: Any, agent: Any) -> None:
        """Second version gets number 2."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        create_version(constitution=constitution, user=user)
        version2 = create_version(constitution=constitution, user=user)
        assert version2.version_number == 2


@pytest.mark.django_db
class TestAddRule:
    def test_add_rule(self, user: Any, agent: Any) -> None:
        """Rule can be added to version."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)

        rule = add_rule(
            version=version,
            rule_number=1,
            name="Max amount",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
            action=RuleAction.ALLOW,
            user=user,
        )

        assert rule.version == version
        assert rule.rule_number == 1
        assert rule.name == "Max amount"

    def test_add_rule_creates_audit_event(self, user: Any, agent: Any) -> None:
        """Adding a rule creates an audit event."""
        from apps.audit.models import AuditEvent

        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)

        initial_count = AuditEvent.objects.count()
        add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
            user=user,
        )
        assert AuditEvent.objects.count() == initial_count + 1

    def test_add_rule_to_active_version_raises(self, user: Any, agent: Any) -> None:
        """Cannot add rule to ACTIVE version."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        activate_version(version=version, user=user)

        with pytest.raises(ConstitutionImmutableError):
            add_rule(
                version=version,
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="test",
                operator=RuleOperator.EQUALS,
                value="test",
                user=user,
            )


@pytest.mark.django_db
class TestActivateVersion:
    def test_activate_version(self, user: Any, agent: Any) -> None:
        """Version can be activated."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)

        activated = activate_version(version=version, user=user)

        assert activated.status == ConstitutionStatus.ACTIVE
        assert activated.activated_at is not None
        assert constitution.active_version == activated

    def test_activate_archives_previous(self, user: Any, agent: Any) -> None:
        """Activating new version archives previous."""
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version1 = create_version(constitution=constitution, user=user)
        activate_version(version=version1, user=user)

        version2 = create_version(constitution=constitution, user=user)
        activate_version(version=version2, user=user)

        version1.refresh_from_db()
        assert version1.status == ConstitutionStatus.ARCHIVED
        assert version1.archived_at is not None

    def test_activate_creates_audit_event(self, user: Any, agent: Any) -> None:
        """Activating a version creates an audit event."""
        from apps.audit.models import AuditEvent

        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)

        initial_count = AuditEvent.objects.count()
        activate_version(version=version, user=user)
        assert AuditEvent.objects.count() == initial_count + 1

    def test_activate_prevents_multiple_active_per_agent(self, user: Any) -> None:
        """Cannot have two ACTIVE constitutions for same agent."""
        agent1 = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="Agent 1",
        )
        agent2 = Agent.objects.create(
            owner=user,
            agent_type=AgentType.USER_AGENT,
            name="Agent 2",
        )

        const1 = create_constitution(agent=agent1, name="Const 1", user=user)
        version1 = create_version(constitution=const1, user=user)
        activate_version(version=version1, user=user)

        const2 = create_constitution(agent=agent2, name="Const 2", user=user)
        version2 = create_version(constitution=const2, user=user)

        # This should work (different agents)
        activate_version(version=version2, user=user)

        # Now try to activate another for agent1
        const3 = create_constitution(agent=agent1, name="Const 3", user=user)
        version3 = create_version(constitution=const3, user=user)

        with pytest.raises(MultipleActiveConstitutionsError):
            activate_version(version=version3, user=user)


@pytest.mark.django_db
class TestCreateConstitutionWithRules:
    def test_create_with_rules(self, user: Any, agent: Any) -> None:
        """Constitution with rules can be created atomically."""
        rules = [
            {
                "rule_number": 1,
                "name": "Max amount",
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
                "field": "phone_number",
                "operator": "EQUALS",
                "value": True,
                "action": "DENY",
            },
        ]

        constitution, version = create_constitution_with_rules(
            agent=agent,
            name="Travel",
            description="Travel rules",
            rules=rules,
            user=user,
        )

        assert constitution.name == "Travel"
        assert version.version_number == 1
        assert PolicyRule.objects.filter(version=version).count() == 2

    def test_create_with_rules_is_atomic(self, user: Any, agent: Any) -> None:
        """If one rule fails, entire operation rolls back."""
        rules = [
            {
                "rule_number": 1,
                "name": "Valid rule",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
            },
            {
                "rule_number": 1,  # Duplicate rule number
                "name": "Invalid rule",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 800,
            },
        ]

        with pytest.raises(ValidationError):  # Rule numbers must be unique
            create_constitution_with_rules(
                agent=agent,
                name="Test",
                description=None,
                rules=rules,
                user=user,
            )

        # Constitution should not exist (rolled back)
        assert Constitution.objects.filter(agent=agent).count() == 0
