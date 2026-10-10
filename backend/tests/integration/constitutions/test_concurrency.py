"""
Concurrency tests for Constitution activation.
"""

import threading
import time
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.agents.models import Agent
from apps.constitutions.models import Constitution
from apps.constitutions.services import activate_version, create_constitution, create_version
from core.enums import AgentType, ConstitutionStatus

User = get_user_model()


@pytest.fixture(autouse=True)
def ensure_unique_active_index(db: Any) -> None:
    """Ensure the partial unique index exists in the test database."""
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_constitution_active
            ON legatio_constitutions_constitution (agent_id)
            WHERE status = 'ACTIVE' AND deleted_at IS NULL;
        """)


@pytest.mark.django_db(transaction=True)
class TestConstitutionActivationConcurrency:
    def test_concurrent_activation_prevented_by_db_index(self) -> None:
        user = User.objects.create_user(email="concurrent@example.com", password="pass")
        agent = Agent.objects.create(
            owner=user, agent_type=AgentType.USER_AGENT, name="Concurrent Agent"
        )

        const1 = create_constitution(agent=agent, name="Const 1", user=user)
        version1 = create_version(constitution=const1, user=user)
        const2 = create_constitution(agent=agent, name="Const 2", user=user)
        version2 = create_version(constitution=const2, user=user)

        errors: list[str] = []
        successes: list[Any] = []

        def activate_const(
            constitution: Any, version: Any, result_list: list[Any], error_list: list[str]
        ) -> None:
            try:
                time.sleep(0.1)
                activate_version(version=version, user=user)
                result_list.append(constitution.id)
            except Exception as e:
                error_list.append(str(e))

        thread1 = threading.Thread(
            target=activate_const, args=(const1, version1, successes, errors)
        )
        thread2 = threading.Thread(
            target=activate_const, args=(const2, version2, successes, errors)
        )
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        assert len(successes) == 1, f"Exactly one activation should succeed, got {len(successes)}"
        assert len(errors) == 1, f"Exactly one activation should fail, got {len(errors)}"
        assert "unique constraint" in errors[0].lower() or "uniq_constitution_active" in errors[0]

        active_count = Constitution.objects.filter(
            agent=agent, status=ConstitutionStatus.ACTIVE, deleted_at__isnull=True
        ).count()
        assert active_count == 1, "DB must have exactly one ACTIVE constitution"

    def test_concurrent_version_creation_safe(self) -> None:
        user = User.objects.create_user(email="versioning@example.com", password="pass")
        agent = Agent.objects.create(
            owner=user, agent_type=AgentType.USER_AGENT, name="Versioning Agent"
        )
        constitution = create_constitution(agent=agent, name="Version Test", user=user)

        versions_created: list[int] = []
        errors: list[str] = []

        def create_v(
            user_obj: Any, const: Any, result_list: list[int], error_list: list[str]
        ) -> None:
            try:
                v = create_version(constitution=const, user=user_obj)
                result_list.append(v.version_number)
            except Exception as e:
                error_list.append(str(e))

        threads = [
            threading.Thread(target=create_v, args=(user, constitution, versions_created, errors))
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(versions_created) + len(errors) == 5, "Total threads should be 5"
        assert len(versions_created) == len(
            set(versions_created)
        ), "No duplicate versions should be created"
