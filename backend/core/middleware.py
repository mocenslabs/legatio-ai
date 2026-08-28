"""
Custom middleware for Legatio AI.
"""

import logging
import uuid

from django.http import HttpRequest, HttpResponseBase
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Middleware to add correlation ID to requests for tracing.
    """

    def process_request(self, request: HttpRequest) -> None:
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID", str(uuid.uuid4()))
        setattr(request, "correlation_id", correlation_id)
        logger.info("Request started", extra={"correlation_id": correlation_id})

    def process_response(
        self, request: HttpRequest, response: HttpResponseBase
    ) -> HttpResponseBase:
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id is not None:
            response["X-Correlation-ID"] = correlation_id
            logger.info("Request completed", extra={"correlation_id": correlation_id})
        return response
