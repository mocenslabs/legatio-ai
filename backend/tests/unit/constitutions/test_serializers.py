"""Unit tests for constitution serializers."""

from __future__ import annotations

import pytest
from rest_framework.exceptions import ValidationError

from apps.constitutions.models import Constitution
from apps.constitutions.serializers import ConstitutionSerializer


@pytest.mark.django_db
class TestConstitutionSerializer:
    def test_valid_creation(self) -> None:
        data = {
            "name": "Test Constitution",
            "description": "A test constitution",
            "is_active": True,
        }
        serializer = ConstitutionSerializer(data=data)
        assert serializer.is_valid()

    def test_unique_name_validation(self) -> None:
        Constitution.objects.create(name="Existing Constitution")
        data = {"name": "Existing Constitution", "description": "Duplicate name"}
        serializer = ConstitutionSerializer(data=data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "name" in exc_info.value.detail

    def test_update_allows_same_name(self) -> None:
        constitution = Constitution.objects.create(name="Original Name")
        data = {"name": "Original Name", "description": "Updated description"}
        serializer = ConstitutionSerializer(constitution, data=data)
        assert serializer.is_valid()
