"""
Health check tests to verify the testing framework is working.
"""

import pytest


def test_framework_is_configured():
    """
    Verify pytest is properly configured.

    This is a placeholder test to ensure the test framework
    runs correctly. It will be replaced with real tests
    as development progresses.
    """
    assert True


@pytest.mark.django_db
def test_database_connection():
    """
    Verify the database connection is working.

    This test confirms that pytest-django can connect
    to the test database successfully.
    """
    from django.db import connection

    assert connection is not None
