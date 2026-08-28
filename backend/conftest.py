"""
Root pytest configuration for Legatio AI.

This file is automatically loaded by pytest before running tests.
It provides global fixtures and configuration.
"""

import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db: object) -> None:
    """
    Enable database access for all tests by default.

    This fixture uses pytest-django's db fixture to ensure
    the database is set up before each test runs.
    """
    pass
