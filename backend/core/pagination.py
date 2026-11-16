"""Standard pagination for Legatio API."""

from rest_framework.pagination import CursorPagination


class StandardCursorPagination(CursorPagination):
    """
    Cursor pagination with a stable default ordering.

    Clients may override page size up to max_page_size via ?page_size=.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
    ordering = "-created_at"
