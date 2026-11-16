"""Readiness check includes channel_layer status."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_readiness_includes_channel_layer_check() -> None:
    client = APIClient()
    url = reverse("health:readiness-check")
    response = client.get(url)
    assert response.status_code in (200, 503)
    assert "checks" in response.data
    assert "channel_layer" in response.data["checks"]
    assert "database" in response.data["checks"]
    assert "cache" in response.data["checks"]
