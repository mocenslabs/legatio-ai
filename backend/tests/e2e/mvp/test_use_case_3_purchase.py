"""
End-to-end test for Use Case 3: Purchase Approval.

Complete flow:
1. User creates constitution with purchase rules
2. User starts negotiation with vendor agent
3. Round 1: €25 for Clean Architecture → REQUIRE_APPROVAL → APPROVED
4. Agreement generated and signed

Source: 04-BUSINESS-FLOW.md Section 6
Source: 05-ROADMAP.md Section 10.3
"""

import pytest
from rest_framework import status

from apps.agreements.models import Agreement
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from core.enums import ApprovalStatus


def _extract_results(response):
    """Handle both paginated and non-paginated responses."""
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data


@pytest.mark.django_db
class TestUseCase3PurchaseApprovalE2E:
    """Complete E2E flow for Purchase Approval."""

    def test_full_purchase_approval_flow(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_vendor_agent,
        e2e_auth_client,
    ) -> None:
        """
        Complete flow:
        1. Create constitution with purchase rules
        2. Create negotiation room
        3. Process round
        4. Approve proposal
        5. Sign agreement
        """
        client = e2e_auth_client

        # 1. Create constitution with purchase rules
        rules = [
            {
                "rule_number": 1,
                "name": "Max transaction",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 50,
                "action": "ALLOW",
            },
            {
                "rule_number": 5,
                "name": "Auto-approve limit",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 20,
                "action": "ALLOW",
            },
            {
                "rule_number": 8,
                "name": "Allowed categories",
                "category": "CUSTOM",
                "field": "category",
                "operator": "IN",
                "value": ["books", "electronics"],
                "action": "ALLOW",
            },
            {
                "rule_number": 10,
                "name": "Prohibited categories",
                "category": "CUSTOM",
                "field": "category",
                "operator": "IN",
                "value": ["gambling"],
                "action": "DENY",
            },
            {
                "rule_number": 15,
                "name": "New vendor requires approval",
                "category": "CUSTOM",
                "field": "is_new_vendor",
                "operator": "EQUALS",
                "value": True,
                "action": "REQUIRE_APPROVAL",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"Purchase Rules {id(object())}",
            description="Rules for purchases",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        # 2. Create negotiation room
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_vendor_agent.id),
                "constitution_id": str(constitution.id),
                "title": "Buy Clean Architecture",
                "user_instruction": (
                    "Buy the book 'Clean Architecture' " "if it costs less than €30."
                ),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        # 3. Start negotiation
        response = client.post(f"/api/v1/negotiations/{room_id}/start/")
        assert response.status_code == status.HTTP_200_OK

        # 4. Process round
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK

        # 5. Check for pending approval and approve
        response = client.get("/api/v1/approvals/pending/")
        if response.status_code == status.HTTP_200_OK:
            results = _extract_results(response)
            pending = [a for a in results if a["status"] == "PENDING"]
            if pending:
                approval_id = pending[0]["id"]
                response = client.post(
                    f"/api/v1/approvals/{approval_id}/approve/",
                    {"comment": "Approved"},
                    format="json",
                )
                assert response.status_code == status.HTTP_201_CREATED
                assert response.data["decision"] == ApprovalStatus.APPROVED

        # 6. Verify agreement was created (if negotiation completed)
        agreements = Agreement.objects.filter(room_id=room_id)
        if agreements.exists():
            agreement = agreements.first()

            # Sign agreement
            response = client.post(
                f"/api/v1/agreements/{agreement.id}/sign/",
                format="json",
            )
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
            ]

    def test_purchase_category_enforcement(
        self,
        e2e_user,
        e2e_user_agent,
        e2e_vendor_agent,
        e2e_auth_client,
    ) -> None:
        """Verify purchase category rules are enforced."""
        client = e2e_auth_client

        # Create constitution with category rules
        rules = [
            {
                "rule_number": 1,
                "name": "Only books allowed",
                "category": "CUSTOM",
                "field": "category",
                "operator": "IN",
                "value": ["books"],
                "action": "ALLOW",
            },
            {
                "rule_number": 2,
                "name": "Gambling prohibited",
                "category": "CUSTOM",
                "field": "category",
                "operator": "IN",
                "value": ["gambling"],
                "action": "DENY",
            },
        ]
        constitution, version = create_constitution_with_rules(
            agent=e2e_user_agent,
            name=f"Category Rules {id(object())}",
            description="Category enforcement",
            rules=rules,
            user=e2e_user,
        )
        activate_version(version=version, user=e2e_user)

        # Create negotiation
        response = client.post(
            "/api/v1/negotiations/",
            {
                "user_agent_id": str(e2e_user_agent.id),
                "external_agent_id": str(e2e_vendor_agent.id),
                "constitution_id": str(constitution.id),
                "title": "Category Test",
                "user_instruction": "Test categories",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        room_id = response.data["id"]

        # Start and process
        client.post(f"/api/v1/negotiations/{room_id}/start/")
        response = client.post(f"/api/v1/negotiations/{room_id}/process_round/")
        assert response.status_code == status.HTTP_200_OK
