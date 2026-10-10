"""
Edge case tests for Constitution validation and services.

Verifies behavior with malformed data, extreme values, and invalid states.
"""

import pytest
from django.contrib.auth import get_user_model
from pydantic import ValidationError

from apps.agents.models import Agent
from apps.constitutions.models import PolicyRule
from apps.constitutions.services import add_rule, create_constitution, create_version
from apps.constitutions.validators import RuleValidator
from core.enums import AgentType, ConstitutionStatus, RuleCategory, RuleOperator

User = get_user_model()


@pytest.mark.django_db
class TestRuleValidationEdgeCases:
    """Tests for Pydantic rule validation edge cases."""

    def test_in_operator_with_non_list_value(self) -> None:
        """IN operator must reject non-list values."""
        with pytest.raises(ValidationError) as exc_info:
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="category",
                operator=RuleOperator.IN,
                value="not_a_list",
            )
        assert "require a list value" in str(exc_info.value)

    def test_empty_list_for_in_operator(self) -> None:
        """IN operator must reject empty lists."""
        with pytest.raises(ValidationError) as exc_info:
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="category",
                operator=RuleOperator.IN,
                value=[],
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_numeric_operator_with_string_value(self) -> None:
        """Numeric operators must reject string values."""
        with pytest.raises(ValidationError) as exc_info:
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.FINANCIAL,
                field="amount",
                operator=RuleOperator.GREATER_THAN,
                value="one_hundred",
            )
        assert "requires a numeric value" in str(exc_info.value)

    def test_field_name_with_special_characters(self) -> None:
        """Field names with invalid characters must be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RuleValidator(
                rule_number=1,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="invalid field name!",
                operator=RuleOperator.EQUALS,
                value="test",
            )
        assert "alphanumeric characters, underscores, or hyphens" in str(exc_info.value)

    def test_rule_number_must_be_positive(self) -> None:
        """Rule number must be >= 1."""
        with pytest.raises(ValidationError):
            RuleValidator(
                rule_number=0,
                name="Test",
                category=RuleCategory.CUSTOM,
                field="test",
                operator=RuleOperator.EQUALS,
                value="test",
            )


@pytest.mark.django_db
class TestServiceEdgeCases:
    """Tests for service-layer edge cases."""

    def test_add_rule_to_archived_version_raises(self) -> None:
        """Cannot add a rule to an ARCHIVED version."""
        user = User.objects.create_user(email="edge@example.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="Edge Agent")
        constitution = create_constitution(agent=agent, name="Edge Const", user=user)
        version = create_version(constitution=constitution, user=user)

        # Manually set to ARCHIVED to simulate state
        version.status = ConstitutionStatus.ARCHIVED
        version.save()

        with pytest.raises(Exception) as exc_info:
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
        assert (
            "archived" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower()
        )

    def test_massive_rule_set_performance(self) -> None:
        """Adding 100 rules to a version should complete quickly."""
        import time

        user = User.objects.create_user(email="perf@example.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="Perf Agent")
        constitution = create_constitution(agent=agent, name="Perf Const", user=user)
        version = create_version(constitution=constitution, user=user)

        start_time = time.time()
        for i in range(100):
            add_rule(
                version=version,
                rule_number=i + 1,
                name=f"Rule {i}",
                category=RuleCategory.CUSTOM,
                field="test_field",
                operator=RuleOperator.EQUALS,
                value=f"value_{i}",
                user=user,
            )
        elapsed = time.time() - start_time

        # Should take less than 2 seconds for 100 rules
        assert elapsed < 2.0, f"Adding 100 rules took {elapsed:.2f}s, expected < 2.0s"
        assert PolicyRule.objects.filter(version=version).count() == 100
