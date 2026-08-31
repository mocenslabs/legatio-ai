"""Policy evaluation API view.

This module provides the API endpoint for evaluating proposed actions against policies.
"""

from __future__ import annotations

import uuid
from typing import Any

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.policies.serializers import (
    PolicyEvaluationRequestSerializer,
    PolicyEvaluationResponseSerializer,
)
from apps.policies.services import PolicyEngineService


class PolicyEvaluationView(APIView):
    """API view for evaluating proposed actions against policies.

    This endpoint accepts a POST request with action details and returns
    the deterministic policy decision.

    Permissions:
        - IsAuthenticated: Requires authentication.

    Request:
        POST /api/policies/evaluate/
        {
            "action_type": "CREATE_PROPOSAL",
            "target_resource": "proposals",
            "payload": {"amount": 5000},
            "actor_id": "uuid",
            "constitution_id": "uuid" (optional)
        }

    Response:
        {
            "outcome": "REQUIRE_HUMAN_APPROVAL",
            "risk_level": "MEDIUM",
            "reason": "Action requires human approval",
            "matched_rules": ["uuid1", "uuid2"],
            "requires_approval_from": ["manager", "director"],
            "timestamp": "2026-01-15T10:30:00Z"
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Evaluate a proposed action against active policies.

        Args:
            request: The HTTP request containing action details.

        Returns:
            Response with the policy decision.
        """
        # Validate request data
        serializer = PolicyEvaluationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data: dict[str, Any] = serializer.validated_data

        # Extract action details
        action_type: str = validated_data["action_type"]
        target_resource: str = validated_data["target_resource"]
        payload: dict[str, Any] = validated_data["payload"]
        actor_id: uuid.UUID = validated_data["actor_id"]
        constitution_id: uuid.UUID | None = validated_data.get("constitution_id")

        # Evaluate the action using the service layer
        decision = PolicyEngineService.evaluate_action(
            action_type=action_type,
            target_resource=target_resource,
            payload=payload,
            actor_id=actor_id,
            constitution_id=constitution_id,
        )

        # Format the response
        response_data = PolicyEngineService.get_decision_summary(decision)
        response_serializer = PolicyEvaluationResponseSerializer(data=response_data)
        response_serializer.is_valid()

        return Response(response_serializer.data, status=status.HTTP_200_OK)
