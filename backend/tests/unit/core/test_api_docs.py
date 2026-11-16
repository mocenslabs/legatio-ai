"""API root, schema and standard error shape."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_root_lists_documentation_links() -> None:
    client = APIClient()
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert "documentation" in response.data
    assert "schema" in response.data["documentation"]
    assert "endpoints" in response.data
    assert "auth" in response.data["endpoints"]


@pytest.mark.django_db
def test_openapi_schema_available() -> None:
    client = APIClient()
    response = client.get("/api/v1/schema/")
    assert response.status_code == 200
    # spectacular returns yaml or json depending on accept
    assert (
        response.get("Content-Type", "").startswith(
            ("application/vnd.oai.openapi", "application/json", "application/yaml", "text/")
        )
        or "openapi" in response.get("Content-Type", "").lower()
        or len(response.content) > 100
    )


@pytest.mark.django_db
def test_error_shape_on_unauthorized_me() -> None:
    client = APIClient()
    response = client.get("/api/v1/auth/me/")
    assert response.status_code in (401, 403)
    assert "error" in response.data
    assert "code" in response.data["error"]
    assert "message" in response.data["error"]
