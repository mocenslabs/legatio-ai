"""
Unit tests for Constitution, ConstitutionVersion, and PolicyRule models.

Source: 03-DATA-MODEL.md Section 8
"""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.agents.models import Agent
from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from core.enums import (
    AgentType,
    ConstitutionStatus,
    RuleAction,
    RuleCategory,
    RuleOperator,
)

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
class TestConstitutionModel:
    """Tests for the Constitution model."""

    def test_create_constitution(self, user: Any, agent: Any) -> None:
        """Constitution can be created."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Travel Constitution",
            description="Rules for travel negotiations",
        )
        assert constitution.agent == agent
        assert constitution.name == "Travel Constitution"
        assert constitution.status == ConstitutionStatus.DRAFT
        assert constitution.active_version is None

    def test_constitution_id_is_uuid(self, agent: Any) -> None:
        """Constitution ID is a UUID."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        import uuid as uuid_module

        assert isinstance(constitution.id, uuid_module.UUID)

    def test_soft_delete_constitution(self, agent: Any) -> None:
        """Constitution can be soft-deleted."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        constitution.soft_delete()
        constitution.refresh_from_db()
        assert constitution.is_deleted is True
        assert Constitution.objects.count() == 0

    def test_cascade_delete_with_agent(self, user: Any, agent: Any) -> None:
        """Deleting agent deletes their constitutions."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        constitution_id = constitution.id
        agent.delete()
        assert not Constitution.all_objects.filter(id=constitution_id).exists()

    def test_str_representation(self, agent: Any) -> None:
        """String representation includes name and status."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Travel",
        )
        assert "Travel" in str(constitution)
        assert "Draft" in str(constitution)


@pytest.mark.django_db
class TestConstitutionVersionModel:
    """Tests for the ConstitutionVersion model."""

    def test_create_version(self, user: Any, agent: Any) -> None:
        """ConstitutionVersion can be created."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        assert version.constitution == constitution
        assert version.version_number == 1
        assert version.status == ConstitutionStatus.DRAFT
        assert version.created_by == user

    def test_version_number_unique_per_constitution(self, user: Any, agent: Any) -> None:
        """Version number must be unique per constitution."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        with pytest.raises(IntegrityError):
            ConstitutionVersion.objects.create(
                constitution=constitution,
                version_number=1,
                created_by=user,
            )

    def test_same_version_number_different_constitutions(self, user: Any) -> None:
        """Same version number is allowed for different constitutions."""
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
        const1 = Constitution.objects.create(agent=agent1, name="Const 1")
        const2 = Constitution.objects.create(agent=agent2, name="Const 2")

        # Both can have version 1
        ConstitutionVersion.objects.create(
            constitution=const1,
            version_number=1,
            created_by=user,
        )
        ConstitutionVersion.objects.create(
            constitution=const2,
            version_number=1,
            created_by=user,
        )
        assert ConstitutionVersion.objects.count() == 2

    def test_version_immutability_when_active(self, user: Any, agent: Any) -> None:
        """Active version cannot be modified."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            status=ConstitutionStatus.ACTIVE,
            created_by=user,
        )
        version.status = ConstitutionStatus.ARCHIVED
        with pytest.raises(RuntimeError, match="immutable"):
            version.save()

    def test_version_immutability_when_archived(self, user: Any, agent: Any) -> None:
        """Archived version cannot be modified."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            status=ConstitutionStatus.ARCHIVED,
            created_by=user,
        )
        version.name = "Modified"
        with pytest.raises(RuntimeError, match="immutable"):
            version.save()

    def test_draft_version_can_be_modified(self, user: Any, agent: Any) -> None:
        """Draft version can be modified."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Test",
        )
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            status=ConstitutionStatus.DRAFT,
            created_by=user,
        )
        version.rules_snapshot = {"test": "data"}
        version.save()  # Should not raise
        version.refresh_from_db()
        assert version.rules_snapshot == {"test": "data"}

    def test_str_representation(self, user: Any, agent: Any) -> None:
        """String representation includes constitution name and version."""
        constitution = Constitution.objects.create(
            agent=agent,
            name="Travel",
        )
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=3,
            created_by=user,
        )
        assert "Travel" in str(version)
        assert "v3" in str(version)


@pytest.mark.django_db
class TestPolicyRuleModel:
    """Tests for the PolicyRule model."""

    def test_create_rule(self, user: Any, agent: Any) -> None:
        """PolicyRule can be created."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=17,
            name="Never share phone",
            category=RuleCategory.PRIVACY,
            field="phone_number",
            operator=RuleOperator.EQUALS,
            value=True,
            action=RuleAction.DENY,
        )
        assert rule.version == version
        assert rule.rule_number == 17
        assert rule.name == "Never share phone"
        assert rule.category == RuleCategory.PRIVACY
        assert rule.action == RuleAction.DENY

    def test_rule_number_unique_per_version(self, user: Any, agent: Any) -> None:
        """Rule number must be unique per version."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Rule 1",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
            action=RuleAction.ALLOW,
        )
        with pytest.raises(IntegrityError):
            PolicyRule.objects.create(
                version=version,
                rule_number=1,
                name="Rule 1 Duplicate",
                category=RuleCategory.FINANCIAL,
                field="amount",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=800,
                action=RuleAction.ALLOW,
            )

    def test_same_rule_number_different_versions(self, user: Any, agent: Any) -> None:
        """Same rule number is allowed in different versions."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version1 = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        version2 = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=2,
            created_by=user,
        )
        PolicyRule.objects.create(
            version=version1,
            rule_number=1,
            name="Rule 1 v1",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
        )
        PolicyRule.objects.create(
            version=version2,
            rule_number=1,
            name="Rule 1 v2",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=800,
        )
        assert PolicyRule.objects.count() == 2

    def test_rule_default_action_is_deny(self, user: Any, agent: Any) -> None:
        """Default action is DENY (fail-safe)."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
        )
        assert rule.action == RuleAction.DENY

    def test_rule_default_priority(self, user: Any, agent: Any) -> None:
        """Default priority is 100."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
        )
        assert rule.priority == 100

    def test_rule_default_is_active(self, user: Any, agent: Any) -> None:
        """Default is_active is True."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
        )
        assert rule.is_active is True

    def test_rule_value_json_field(self, user: Any, agent: Any) -> None:
        """Rule value can be various JSON types."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        # Numeric value
        rule1 = PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Amount rule",
            category=RuleCategory.FINANCIAL,
            field="amount",
            operator=RuleOperator.LESS_THAN_OR_EQUAL,
            value=700,
        )
        assert rule1.value == 700

        # String value
        rule2 = PolicyRule.objects.create(
            version=version,
            rule_number=2,
            name="Currency rule",
            category=RuleCategory.FINANCIAL,
            field="currency",
            operator=RuleOperator.EQUALS,
            value="EUR",
        )
        assert rule2.value == "EUR"

        # Boolean value
        rule3 = PolicyRule.objects.create(
            version=version,
            rule_number=3,
            name="Phone rule",
            category=RuleCategory.PRIVACY,
            field="phone_number",
            operator=RuleOperator.EQUALS,
            value=True,
        )
        assert rule3.value is True

        # List value
        rule4 = PolicyRule.objects.create(
            version=version,
            rule_number=4,
            name="Category rule",
            category=RuleCategory.CUSTOM,
            field="category",
            operator=RuleOperator.IN,
            value=["books", "electronics"],
        )
        assert rule4.value == ["books", "electronics"]

    def test_str_representation(self, user: Any, agent: Any) -> None:
        """String representation includes rule number and name."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=17,
            name="Never share phone",
            category=RuleCategory.PRIVACY,
            field="phone_number",
            operator=RuleOperator.EQUALS,
            value=True,
        )
        assert "Rule #17" in str(rule)
        assert "Never share phone" in str(rule)

    def test_cascade_delete_with_version(self, user: Any, agent: Any) -> None:
        """Deleting version deletes its rules."""
        constitution = Constitution.objects.create(agent=agent, name="Test")
        version = ConstitutionVersion.objects.create(
            constitution=constitution,
            version_number=1,
            created_by=user,
        )
        rule = PolicyRule.objects.create(
            version=version,
            rule_number=1,
            name="Test",
            category=RuleCategory.CUSTOM,
            field="test",
            operator=RuleOperator.EQUALS,
            value="test",
        )
        rule_id = rule.id
        version.delete()
        assert not PolicyRule.objects.filter(id=rule_id).exists()
