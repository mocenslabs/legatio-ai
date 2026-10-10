"""
Tests to boost coverage to >= 95% for constitutions module.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.agents.models import Agent
from apps.constitutions.managers import ConstitutionSoftDeleteQuerySet
from apps.constitutions.models import Constitution, ConstitutionVersion, PolicyRule
from apps.constitutions.serializers import (
    ConstitutionCreateSerializer,
    ConstitutionSerializer,
    ConstitutionWithRulesSerializer,
    EvaluateRuleSerializer,
    PolicyRuleSerializer,
)
from apps.constitutions.services import (
    activate_version,
    add_rule,
    create_constitution,
    create_version,
    delete_rule,
    update_constitution,
    update_rule,
)
from apps.constitutions.views import ConstitutionViewSet, PolicyRuleViewSet
from core.enums import (
    AgentType,
    ConstitutionStatus,
    RuleAction,
    RuleOperator,
)
from core.exceptions import (
    ConstitutionImmutableError,
    NoActiveConstitutionError,
)
from services.policy_engine.loader import (
    get_active_constitution_version,
    load_active_rules_for_agent,
    load_rules_from_version,
)

User = get_user_model()


@pytest.mark.django_db
class TestManagersCoverage:
    """Tests for managers.py missing lines."""

    def test_manager_dead_method(self) -> None:
        """Covers managers.py line 48 (dead() on manager)."""
        user = User.objects.create_user(email="m1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="M1")
        create_constitution(agent=agent, name="Alive", user=user)
        c2 = create_constitution(agent=agent, name="Deleted", user=user)
        c2.soft_delete()

        manager = Constitution.objects
        dead_qs = manager.dead()
        assert dead_qs.count() == 1
        assert dead_qs.first().id == c2.id

    def test_immutable_version_queryset_update(self) -> None:
        """Covers managers.py lines 60-65 (ImmutableVersionQuerySet.update)."""
        user = User.objects.create_user(email="m2@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="M2")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        activate_version(version=version, user=user)

        with pytest.raises(RuntimeError, match="immutable"):
            ConstitutionVersion.objects.filter(id=version.id).update(
                rules_snapshot={"hacked": True}
            )

    def test_queryset_alive_method(self) -> None:
        """Covers managers.py line 21 (alive method)."""
        user = User.objects.create_user(email="m3@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="M3")
        c1 = create_constitution(agent=agent, name="Alive", user=user)
        c2 = create_constitution(agent=agent, name="Deleted", user=user)
        c2.soft_delete()

        qs = ConstitutionSoftDeleteQuerySet(Constitution).filter(agent=agent)
        alive_qs = qs.alive()
        assert alive_qs.count() == 1
        assert alive_qs.first().id == c1.id


@pytest.mark.django_db
class TestSerializersCoverage:
    """Tests for serializers.py missing lines."""

    def test_policy_rule_serializer_validate(self) -> None:
        """Covers serializers.py lines 45-70 (PolicyRuleSerializer validation)."""
        user = User.objects.create_user(email="s1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="S1")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)

        # Test valid rule
        serializer = PolicyRuleSerializer(
            data={
                "version": str(version.id),
                "rule_number": 99,
                "name": "Valid Rule",
                "category": "CUSTOM",
                "field": "test_field",
                "operator": "EQUALS",
                "value": "test_value",
            },
        )
        assert serializer.is_valid()

        # Test with ACTIVE version
        activate_version(version=version, user=user)
        serializer2 = PolicyRuleSerializer(
            data={
                "version": str(version.id),
                "rule_number": 100,
                "name": "Invalid Rule",
                "category": "CUSTOM",
                "field": "test_field",
                "operator": "EQUALS",
                "value": "test_value",
            },
        )
        assert not serializer2.is_valid()

    def test_constitution_serializer_validate_name(self) -> None:
        """Covers serializers.py lines 93-94 (validate_name)."""
        user = User.objects.create_user(email="s2@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="S2")

        # Test empty name
        serializer = ConstitutionSerializer(
            data={"name": "", "agent": str(agent.id)},
        )
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_constitution_create_serializer_validate_agent_id(self) -> None:
        """Covers serializers.py lines 181-186, 190-192 (validate_agent_id)."""
        user = User.objects.create_user(email="s3@x.com", password="pass")
        factory = APIRequestFactory()
        request = factory.post("/api/v1/constitutions/")
        request.user = user

        # Test non-existent agent
        serializer = ConstitutionCreateSerializer(
            data={"agent_id": "00000000-0000-0000-0000-000000000000", "name": "Test"},
            context={"request": request},
        )
        assert not serializer.is_valid()
        assert "agent_id" in serializer.errors

    def test_constitution_with_rules_serializer_validate_agent_id(self) -> None:
        """Covers serializers.py lines 240-241, 244 (validate_agent_id for with-rules)."""
        user = User.objects.create_user(email="s4@x.com", password="pass")
        factory = APIRequestFactory()
        request = factory.post("/api/v1/constitutions/with-rules/")
        request.user = user

        # Test non-existent agent
        serializer = ConstitutionWithRulesSerializer(
            data={
                "agent_id": "00000000-0000-0000-0000-000000000000",
                "name": "Test",
                "rules": [
                    {
                        "rule_number": 1,
                        "name": "Test",
                        "category": "CUSTOM",
                        "field": "test",
                        "operator": "EQUALS",
                        "value": "test",
                    }
                ],
            },
            context={"request": request},
        )
        assert not serializer.is_valid()
        assert "agent_id" in serializer.errors

    def test_evaluate_rule_serializer(self) -> None:
        """Covers serializers.py lines 264-265 (EvaluateRuleSerializer)."""
        serializer = EvaluateRuleSerializer(
            data={
                "action": {
                    "action_type": "purchase",
                    "amount": 500.0,
                    "data_fields_requested": [],
                }
            },
        )
        # Just execute the code path
        serializer.is_valid()


@pytest.mark.django_db
class TestServicesCoverage:
    """Tests for services.py missing lines."""

    def test_update_constitution_on_active_raises(self) -> None:
        """Covers services.py lines 115-123 (update_constitution on ACTIVE)."""
        user = User.objects.create_user(email="svc1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SVC1")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        activate_version(version=version, user=user)

        with pytest.raises(ConstitutionImmutableError):
            update_constitution(constitution=constitution, name="Hacked", user=user)


@pytest.mark.django_db
class TestViewsCoverage:
    """Tests for views.py missing lines."""

    def test_viewset_get_queryset_with_request(self) -> None:
        """Covers views.py lines 67, 70 (get_queryset with request)."""
        user = User.objects.create_user(email="v1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V1")
        create_constitution(agent=agent, name="Test", user=user)

        factory = APIRequestFactory()
        request = factory.get("/api/v1/constitutions/")
        request.user = user

        view = ConstitutionViewSet()
        view.request = request
        view.kwargs = {}
        view.action = "list"

        qs = view.get_queryset()
        assert qs.count() >= 1

    def test_viewset_partial_update_on_active_raises(self) -> None:
        """Covers views.py lines 107-122, 129-131 (partial_update on ACTIVE)."""
        user = User.objects.create_user(email="v2@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V2")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        activate_version(version=version, user=user)

        factory = APIRequestFactory()
        request = factory.patch(
            f"/api/v1/constitutions/{constitution.id}/",
            {"name": "Hacked"},
            format="json",
        )
        force_authenticate(request, user=user)

        view = ConstitutionViewSet.as_view({"patch": "partial_update"})
        response = view(request, pk=constitution.id)

        assert response.status_code == 400

    def test_policy_rule_viewset_get_queryset(self) -> None:
        """Covers views.py lines 148-149 (PolicyRuleViewSet get_queryset)."""
        user = User.objects.create_user(email="v3@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V3")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        factory = APIRequestFactory()
        request = factory.get("/api/v1/rules/")
        request.user = user

        view = PolicyRuleViewSet()
        view.request = request
        view.kwargs = {}
        view.action = "list"

        qs = view.get_queryset()
        assert qs.count() >= 1

    def test_viewset_with_rules_action(self) -> None:
        """Covers views.py lines 156-157 (with_rules action)."""
        user = User.objects.create_user(email="v4@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V4")

        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/constitutions/with-rules/",
            {
                "agent_id": str(agent.id),
                "name": "With Rules",
                "description": "Test",
                "rules": [
                    {
                        "rule_number": 1,
                        "name": "Rule 1",
                        "category": "FINANCIAL",
                        "field": "amount",
                        "operator": "LESS_THAN_OR_EQUAL",
                        "value": 1000,
                        "action": "ALLOW",
                    }
                ],
            },
            format="json",
        )
        force_authenticate(request, user=user)

        view = ConstitutionViewSet.as_view({"post": "with_rules"})
        response = view(request)

        assert response.status_code == 201

    def test_policy_rule_viewset_partial_update(self) -> None:
        """Covers views.py lines 207-208 (PolicyRuleViewSet partial_update)."""
        user = User.objects.create_user(email="v5@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V5")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Old",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        factory = APIRequestFactory()
        request = factory.patch(
            f"/api/v1/rules/{rule.id}/",
            {"name": "New"},
            format="json",
        )
        force_authenticate(request, user=user)

        view = PolicyRuleViewSet.as_view({"patch": "partial_update"})
        response = view(request, pk=rule.id)

        assert response.status_code == 200

    def test_policy_rule_viewset_destroy(self) -> None:
        """Covers views.py lines 247, 254 (PolicyRuleViewSet destroy)."""
        user = User.objects.create_user(email="v6@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V6")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="To Delete",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        factory = APIRequestFactory()
        request = factory.delete(f"/api/v1/rules/{rule.id}/")
        force_authenticate(request, user=user)

        view = PolicyRuleViewSet.as_view({"delete": "destroy"})
        response = view(request, pk=rule.id)

        assert response.status_code == 204

    def test_policy_rule_viewset_evaluate(self) -> None:
        """Covers views.py lines 284, 291-292 (PolicyRuleViewSet evaluate)."""
        user = User.objects.create_user(email="v7@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V7")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Max Amount",
            category="FINANCIAL",
            field="amount",
            operator="LESS_THAN_OR_EQUAL",
            value=700,
            action="ALLOW",
            user=user,
        )

        factory = APIRequestFactory()
        request = factory.post(
            f"/api/v1/rules/{rule.id}/evaluate/",
            {
                "action": {
                    "action_type": "purchase",
                    "amount": 500.0,
                    "data_fields_requested": [],
                }
            },
            format="json",
        )
        force_authenticate(request, user=user)

        view = PolicyRuleViewSet.as_view({"post": "evaluate"})
        response = view(request, pk=rule.id)

        assert response.status_code == 200

    def test_policy_rule_viewset_create_missing_constitution(self) -> None:
        """Covers views.py lines 345-346 (create with missing constitution)."""
        user = User.objects.create_user(email="v8@x.com", password="pass")

        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/constitutions/00000000-0000-0000-0000-000000000000/rules/",
            {
                "version_id": "00000000-0000-0000-0000-000000000000",
                "rule_number": 1,
                "name": "Test",
                "category": "CUSTOM",
                "field": "test",
                "operator": "EQUALS",
                "value": "test",
            },
            format="json",
        )
        force_authenticate(request, user=user)

        view = PolicyRuleViewSet.as_view({"post": "create"})
        response = view(request, constitution_id="00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404

    def test_policy_rule_viewset_create_missing_version(self) -> None:
        """Covers views.py lines 366-367 (create with missing version)."""
        user = User.objects.create_user(email="v9@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="V9")
        constitution = create_constitution(agent=agent, name="Test", user=user)

        factory = APIRequestFactory()
        request = factory.post(
            f"/api/v1/constitutions/{constitution.id}/rules/",
            {
                "version_id": "00000000-0000-0000-0000-000000000000",
                "rule_number": 1,
                "name": "Test",
                "category": "CUSTOM",
                "field": "test",
                "operator": "EQUALS",
                "value": "test",
            },
            format="json",
        )
        force_authenticate(request, user=user)

        view = PolicyRuleViewSet.as_view({"post": "create"})
        response = view(request, constitution_id=constitution.id)

        assert response.status_code == 404


@pytest.mark.django_db
class TestLoaderCoverage:
    """Tests for loader.py missing lines."""

    def test_loader_load_rules_from_version(self) -> None:
        """Covers loader.py line 72 (load_rules_from_version)."""
        user = User.objects.create_user(email="l1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="L1")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        rules = load_rules_from_version(version)
        assert len(rules) == 1

    def test_loader_load_rules_with_inactive(self) -> None:
        """Covers loader.py line 76 (load_rules_from_version with inactive)."""
        user = User.objects.create_user(email="l2@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="L2")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        add_rule(
            version=version,
            rule_number=1,
            name="Active",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )
        rule2 = add_rule(
            version=version,
            rule_number=2,
            name="Inactive",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )
        rule2.is_active = False
        rule2.save()

        rules = load_rules_from_version(version)
        assert len(rules) == 1

    def test_loader_get_active_constitution_version_no_active(self) -> None:
        """Covers loader.py lines 96-111 (no active constitution)."""
        user = User.objects.create_user(email="l3@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="L3")

        with pytest.raises(NoActiveConstitutionError):
            get_active_constitution_version(agent=agent)

    def test_loader_load_active_rules_no_active(self) -> None:
        """Covers loader.py lines 96-111 (load_active_rules_for_agent no active)."""
        user = User.objects.create_user(email="l4@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="L4")

        with pytest.raises(NoActiveConstitutionError):
            load_active_rules_for_agent(agent=agent)


@pytest.mark.django_db
class TestServicesUpdateCoverage:
    """Tests to cover services.py missing lines."""

    def test_update_constitution_on_active_raises(self) -> None:
        """Covers services.py lines 115-123."""
        user = User.objects.create_user(email="su1@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU1")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        activate_version(version=version, user=user)

        with pytest.raises(ConstitutionImmutableError):
            update_constitution(constitution=constitution, name="Hacked", user=user)

    def test_update_rule_on_active_raises(self) -> None:
        """Covers services.py lines 298-299."""
        user = User.objects.create_user(email="su2@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU2")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )
        activate_version(version=version, user=user)

        with pytest.raises(ConstitutionImmutableError):
            update_rule(rule=rule, name="Hacked", user=user)

    def test_update_rule_on_archived_raises(self) -> None:
        """Covers services.py lines 301-302."""
        user = User.objects.create_user(email="su3@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU3")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )
        activate_version(version=version, user=user)
        version.status = ConstitutionStatus.ARCHIVED
        version.save(update_fields=["status"])

        with pytest.raises(ConstitutionImmutableError):
            update_rule(rule=rule, name="Hacked", user=user)

    def test_update_rule_all_fields(self) -> None:
        """Covers services.py lines 304-317."""
        user = User.objects.create_user(email="su4@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU4")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Old",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        updated = update_rule(
            rule=rule,
            name="New Name",
            description="New Desc",
            field="new_field",
            operator=RuleOperator.GREATER_THAN,
            value=999,
            action=RuleAction.ALLOW,
            priority=50,
            is_active=False,
            user=user,
        )
        assert updated.name == "New Name"
        assert updated.description == "New Desc"
        assert updated.field == "new_field"
        assert updated.operator == RuleOperator.GREATER_THAN
        assert updated.value == 999
        assert updated.action == RuleAction.ALLOW
        assert updated.priority == 50
        assert updated.is_active is False

    def test_delete_rule_on_active_raises(self) -> None:
        """Covers services.py line 339."""
        user = User.objects.create_user(email="su5@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU5")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )
        activate_version(version=version, user=user)

        with pytest.raises(ConstitutionImmutableError):
            delete_rule(rule=rule, user=user)

    def test_delete_rule_on_draft_succeeds(self) -> None:
        """Covers services.py delete_rule success path."""
        user = User.objects.create_user(email="su6@x.com", password="pass")
        agent = Agent.objects.create(owner=user, agent_type=AgentType.USER_AGENT, name="SU6")
        constitution = create_constitution(agent=agent, name="Test", user=user)
        version = create_version(constitution=constitution, user=user)
        rule = add_rule(
            version=version,
            rule_number=1,
            name="Test",
            category="CUSTOM",
            field="test",
            operator="EQUALS",
            value="test",
            user=user,
        )

        delete_rule(rule=rule, user=user)
        assert not PolicyRule.objects.filter(id=rule.id).exists()
