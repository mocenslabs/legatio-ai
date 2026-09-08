"""Root pytest configuration.

This module provides shared fixtures for the entire test suite.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache_between_tests() -> Iterator[None]:
    """Clear the Django cache before and after each test.

    This ensures throttle state does not accumulate across tests,
    preventing rate-limit false positives in the test suite.
    """
    cache.clear()
    yield
    cache.clear()
