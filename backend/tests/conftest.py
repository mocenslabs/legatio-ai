"""
Test fixtures for Legatio AI.

Common fixtures used across unit, integration, and e2e tests.
"""

import pytest


@pytest.fixture
def sample_user_data() -> dict[str, str]:
    """
    Provide sample user data for tests.

    Returns:
        dict: Sample user creation data.
    """
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
    }
