"""
Custom middleware for Legatio AI.
"""

import logging
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Middleware to add correlation ID to requests for tracing.
    """

    def process_request(self, request):
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID", str(uuid.uuid4()))
        request.correlation_id = correlation_id
        logger.info("Request started", extra={"correlation_id": correlation_id})

    def process_response(self, request, response):
        if hasattr(request, "correlation_id"):
            response["X-Correlation-ID"] = request.correlation_id
            logger.info("Request completed", extra={"correlation_id": request.correlation_id})
        return response
