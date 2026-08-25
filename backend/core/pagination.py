"""
Custom pagination classes for Legatio AI.
"""

from rest_framework.pagination import CursorPagination


class StandardCursorPagination(CursorPagination):
    """Standard cursor-based pagination."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"
