"""API tests for ScheduledJob endpoints.

Tests cover list/retrieve operations, filtering, and access restrictions.
Scheduled jobs are read-only execution records.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.scheduling.models import JobStatus, ScheduledJob


@pytest.fixture
def user(db: None) -> User:
    """Create a test user.

    Args:
        db: The database fixture.

    Returns:
        A User instance.
    """
    return User.objects.create_user(email="user@example.com", password="testpass123")


@pytest.fixture
def api_client(user: User) -> APIClient:
    """Create an authenticated API client.

    Args:
        user: The user fixture.

    Returns:
        Authenticated APIClient instance.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestScheduledJobList:
    """Tests for ScheduledJob list and retrieve operations."""

    def test_list_jobs(self, api_client: APIClient) -> None:
        """Verify listing jobs returns paginated results."""
        ScheduledJob.objects.create(
            name="Job 1",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )
        ScheduledJob.objects.create(
            name="Job 2",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        url = reverse("scheduledjob-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_job(self, api_client: APIClient) -> None:
        """Verify retrieving a single job works."""
        job = ScheduledJob.objects.create(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.COMPLETED,
            result={"key": "value"},
        )

        url = reverse("scheduledjob-detail", kwargs={"pk": job.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Job"
        assert response.data["status"] == "COMPLETED"
        assert response.data["result"] == {"key": "value"}
        assert "is_finished" in response.data
        assert "succeeded" in response.data

    def test_filter_by_status(self, api_client: APIClient) -> None:
        """Verify filtering jobs by status works."""
        ScheduledJob.objects.create(
            name="Completed Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.COMPLETED,
        )
        ScheduledJob.objects.create(
            name="Failed Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
            status=JobStatus.FAILED,
        )

        url = reverse("scheduledjob-list")
        response = api_client.get(url, {"status": "COMPLETED"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "COMPLETED"

    def test_filter_by_task_name(self, api_client: APIClient) -> None:
        """Verify filtering jobs by task_name works."""
        ScheduledJob.objects.create(
            name="Task A",
            task_name="apps.agents.tasks.process_scheduled_rules",
            scheduled_for=timezone.now(),
        )
        ScheduledJob.objects.create(
            name="Task B",
            task_name="apps.scheduling.tasks.check_expired_agreements",
            scheduled_for=timezone.now(),
        )

        url = reverse("scheduledjob-list")
        response = api_client.get(url, {"task_name": "apps.agents.tasks.process_scheduled_rules"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert (
            response.data["results"][0]["task_name"] == "apps.agents.tasks.process_scheduled_rules"
        )


@pytest.mark.django_db
class TestScheduledJobRestrictions:
    """Tests for ScheduledJob access restrictions."""

    def test_create_not_allowed(self, api_client: APIClient) -> None:
        """Verify creating jobs via API returns 405."""
        url = reverse("scheduledjob-list")
        data = {
            "name": "Manual Job",
            "task_name": "apps.test.task",
            "scheduled_for": timezone.now().isoformat(),
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, api_client: APIClient) -> None:
        """Verify deleting jobs via API returns 405."""
        job = ScheduledJob.objects.create(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        url = reverse("scheduledjob-detail", kwargs={"pk": job.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_not_allowed(self, api_client: APIClient) -> None:
        """Verify updating jobs via API returns 405."""
        job = ScheduledJob.objects.create(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        url = reverse("scheduledjob-detail", kwargs={"pk": job.id})
        response = api_client.patch(url, {"name": "Modified"}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_unauthenticated_returns_401(self) -> None:
        """Verify unauthenticated requests return 401."""
        ScheduledJob.objects.create(
            name="Test Job",
            task_name="apps.test.task",
            scheduled_for=timezone.now(),
        )

        client = APIClient()
        url = reverse("scheduledjob-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
