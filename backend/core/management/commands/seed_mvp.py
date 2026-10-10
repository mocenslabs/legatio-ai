"""
Management command to seed the database with MVP demo data.

Creates:
- 2 demo users (alice, bob)
- 3 agents (1 user agent, 2 simulated)
- 1 active constitution with 5 rules (Madrid travel scenario)
- 1 completed negotiation with full audit trail
- 1 signed agreement

Aligned with real models:
- NegotiationRoom.constitution (FK Constitution)
- NegotiationMessage.sender_type + sender_id, content=JSONField
- CounterProposal.sender (FK Agent)
- PolicyDecision.constitution_version

Source: 03-DATA-MODEL.md Section 19.1 / DEL-036
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.agents.models import Agent
from apps.agreements.models import Agreement
from apps.agreements.services import (
    create_agreement_from_proposal,
    sign_agreement,
)
from apps.approvals.services import (
    create_approval_request,
    process_approval_decision,
)
from apps.constitutions.models import Constitution, ConstitutionVersion
from apps.constitutions.services import (
    activate_version,
    create_constitution_with_rules,
)
from apps.negotiations.models import NegotiationMessage, NegotiationRoom
from apps.proposals.models import CounterProposal, PolicyDecision, Proposal
from core.enums import (
    ActorType,
    AgentStatus,
    AgentType,
    ApprovalStatus,
    NegotiationMessageType,
    NegotiationStatus,
    PolicyDecisionOutcome,
    ProposalStatus,
    RiskLevel,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with MVP demo data"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-seed even if data already exists",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("=" * 60)
        self.stdout.write("Legatio AI — Seed MVP Data")
        self.stdout.write("=" * 60)

        force: bool = bool(options["force"])

        if User.objects.filter(email="alice@example.com").exists() and not force:
            self.stdout.write(self.style.WARNING("\n⚠️  Database already contains seed data."))
            self.stdout.write("   Run with --force to re-seed, or skip this step.")
            return

        with transaction.atomic():
            if force:
                self._cleanup_existing_data()

            alice, bob = self._seed_users()
            user_agent, hotel_agent, _isp_agent = self._seed_agents(alice)
            constitution, _version = self._seed_constitution(alice, user_agent)
            room, agreement = self._seed_negotiation(alice, user_agent, hotel_agent, constitution)

        self._print_summary(alice, bob, room, agreement)

    def _cleanup_existing_data(self) -> None:
        """Remove existing seed data (best-effort cascade)."""
        self.stdout.write("\n🧹 Cleaning up existing seed data...")
        User.objects.filter(email__in=["alice@example.com", "bob@example.com"]).delete()
        Agent.objects.filter(name__in=["Hotel Agent", "ISP Agent"]).delete()
        self.stdout.write(self.style.SUCCESS("  ✓ Cleanup complete"))

    def _seed_users(self) -> tuple[Any, Any]:
        """Create demo users."""
        self.stdout.write("\n👤 Creating users...")

        alice, created = User.objects.get_or_create(
            email="alice@example.com",
            defaults={
                "first_name": "Alice",
                "last_name": "Demo",
                "is_verified": True,
            },
        )
        if created:
            alice.set_password("alice1234")
            alice.save()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {alice.email}"))
        else:
            self.stdout.write(f"  - Exists: {alice.email}")

        bob, created = User.objects.get_or_create(
            email="bob@example.com",
            defaults={
                "first_name": "Bob",
                "last_name": "Demo",
                "is_verified": True,
            },
        )
        if created:
            bob.set_password("bob1234")
            bob.save()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {bob.email}"))
        else:
            self.stdout.write(f"  - Exists: {bob.email}")

        return alice, bob

    def _seed_agents(self, alice: Any) -> tuple[Agent, Agent, Agent]:
        """Create demo agents."""
        self.stdout.write("\n🤖 Creating agents...")

        user_agent, created = Agent.objects.get_or_create(
            owner=alice,
            agent_type=AgentType.USER_AGENT,
            name="Alice's Travel Agent",
            defaults={
                "description": "Personal travel assistant",
                "status": AgentStatus.ACTIVE,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ User agent: {user_agent.name}")
            if created
            else f"  - Exists: {user_agent.name}"
        )

        hotel_agent, created = Agent.objects.get_or_create(
            agent_type=AgentType.SIMULATED,
            name="Hotel Agent",
            defaults={
                "owner": None,
                "description": "Simulated hotel booking agent",
                "status": AgentStatus.ACTIVE,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Simulated: {hotel_agent.name}")
            if created
            else f"  - Exists: {hotel_agent.name}"
        )

        isp_agent, created = Agent.objects.get_or_create(
            agent_type=AgentType.SIMULATED,
            name="ISP Agent",
            defaults={
                "owner": None,
                "description": "Simulated ISP negotiation agent",
                "status": AgentStatus.ACTIVE,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Simulated: {isp_agent.name}")
            if created
            else f"  - Exists: {isp_agent.name}"
        )

        return user_agent, hotel_agent, isp_agent

    def _seed_constitution(
        self, alice: Any, user_agent: Agent
    ) -> tuple[Constitution, ConstitutionVersion]:
        """Create Madrid travel constitution with 5 rules."""
        self.stdout.write("\n📜 Creating constitution...")

        rules: list[dict[str, Any]] = [
            {
                "rule_number": 1,
                "name": "Max transaction amount",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 700,
                "action": "ALLOW",
                "priority": 10,
            },
            {
                "rule_number": 17,
                "name": "Never share phone number",
                "category": "PRIVACY",
                "field": "phone_number",
                "operator": "EQUALS",
                "value": True,
                "action": "DENY",
                "priority": 1,
            },
            {
                "rule_number": 23,
                "name": "Large payments need approval",
                "category": "FINANCIAL",
                "field": "amount",
                "operator": "GREATER_THAN",
                "value": 200,
                "action": "REQUIRE_APPROVAL",
                "priority": 20,
            },
            {
                "rule_number": 31,
                "name": "Email sharing allowed",
                "category": "PRIVACY",
                "field": "email",
                "operator": "EQUALS",
                "value": True,
                "action": "ALLOW",
                "priority": 30,
            },
            {
                "rule_number": 45,
                "name": "Max contract length",
                "category": "NEGOTIATION",
                "field": "contract_length_months",
                "operator": "LESS_THAN_OR_EQUAL",
                "value": 12,
                "action": "DENY",
                "priority": 15,
            },
        ]

        constitution, version = create_constitution_with_rules(
            agent=user_agent,
            name="Madrid Travel Constitution",
            description="Rules for hotel booking in Madrid",
            rules=rules,
            user=alice,
        )
        activate_version(version=version, user=alice)

        self.stdout.write(self.style.SUCCESS(f"  ✓ Constitution: {constitution.name}"))
        self.stdout.write(self.style.SUCCESS(f"  ✓ Version: v{version.version_number}"))
        self.stdout.write(self.style.SUCCESS(f"  ✓ Rules: {version.rules.count()} active"))
        return constitution, version

    def _seed_negotiation(
        self,
        alice: Any,
        user_agent: Agent,
        hotel_agent: Agent,
        constitution: Constitution,
    ) -> tuple[NegotiationRoom, Agreement]:
        """Create a completed negotiation with full audit trail (3 rounds)."""
        self.stdout.write("\n🤝 Creating negotiation...")

        now = timezone.now()
        room = NegotiationRoom.objects.create(
            user_agent=user_agent,
            external_agent=hotel_agent,
            constitution=constitution,
            reference_code="NEG-2026-000001",
            title="Hotel Madrid 5 nights",
            user_instruction=("Find hotel in Madrid for 5 nights. " "Max €700. Never share phone."),
            status=NegotiationStatus.COMPLETED,
            max_rounds=10,
            current_round=3,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1),
        )
        self.stdout.write(self.style.SUCCESS(f"  ✓ Room: {room.reference_code}"))

        constitution.refresh_from_db()
        active_version = constitution.active_version

        # Round 1: €820 → REQUIRE_APPROVAL → REJECTED
        proposal1 = Proposal.objects.create(
            room=room,
            sender=hotel_agent,
            action_type="purchase",
            amount=Decimal("820.00"),
            currency="EUR",
            data_fields_requested=[],
            terms={"nights": 5, "breakfast": True, "destination": "Madrid"},
            status=ProposalStatus.EVALUATING,
            round_number=1,
        )
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.EXTERNAL_AGENT,
            sender_id=hotel_agent.id,
            message_type=NegotiationMessageType.PROPOSAL,
            content={"text": "I offer €820 for 5 nights in Madrid, breakfast included."},
            round_number=1,
        )
        decision1 = PolicyDecision.objects.create(
            proposal=proposal1,
            constitution_version=active_version,
            outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=RiskLevel.LOW,
            reason="Amount €820 exceeds auto-approve limit of €200",
            matched_rules=[
                {
                    "rule_id": "rule-23",
                    "rule_number": 23,
                    "name": "Large payments need approval",
                    "action": "REQUIRE_APPROVAL",
                    "triggered_by": "amount > 200",
                }
            ],
            evaluation_duration_ms=12,
            engine_version="1.0.0",
        )
        approval1 = create_approval_request(
            proposal=proposal1,
            policy_decision=decision1,
            room=room,
        )
        process_approval_decision(
            request=approval1,
            user=alice,
            decision=ApprovalStatus.REJECTED,
            comment="Too expensive. Counter with €650.",
        )
        self.stdout.write(self.style.SUCCESS("  ✓ Round 1: €820 → REQUIRE_APPROVAL → REJECTED"))

        # Round 2: €680 + phone → DENY → counter-offer
        proposal2 = Proposal.objects.create(
            room=room,
            sender=hotel_agent,
            action_type="purchase",
            amount=Decimal("680.00"),
            currency="EUR",
            data_fields_requested=["phone_number"],
            terms={"nights": 5, "destination": "Madrid"},
            status=ProposalStatus.EVALUATING,
            round_number=2,
        )
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.EXTERNAL_AGENT,
            sender_id=hotel_agent.id,
            message_type=NegotiationMessageType.PROPOSAL,
            content={"text": ("I can do €680, but I need your phone number for the booking.")},
            round_number=2,
        )
        PolicyDecision.objects.create(
            proposal=proposal2,
            constitution_version=active_version,
            outcome=PolicyDecisionOutcome.DENY,
            risk_level=RiskLevel.CRITICAL,
            reason=(
                "Proposal requests phone_number, forbidden by Rule #17 "
                "(Never share phone number)"
            ),
            matched_rules=[
                {
                    "rule_id": "rule-17",
                    "rule_number": 17,
                    "name": "Never share phone number",
                    "action": "DENY",
                    "triggered_by": "data_fields_requested contains 'phone_number'",
                }
            ],
            evaluation_duration_ms=8,
            engine_version="1.0.0",
        )
        Proposal.objects.filter(id=proposal2.id).update(status=ProposalStatus.DENIED)
        CounterProposal.objects.create(
            proposal=proposal2,
            sender=user_agent,
            adjustments={"data_fields_requested": []},
            reasoning="Counter-offer without phone number sharing",
        )
        self.stdout.write(self.style.SUCCESS("  ✓ Round 2: €680 + phone → DENY → counter-offer"))

        # Round 3: €700, no phone → REQUIRE_APPROVAL → APPROVED → Agreement
        proposal3 = Proposal.objects.create(
            room=room,
            sender=hotel_agent,
            action_type="purchase",
            amount=Decimal("700.00"),
            currency="EUR",
            data_fields_requested=[],
            terms={
                "nights": 5,
                "cancellation": "48h",
                "destination": "Madrid",
            },
            status=ProposalStatus.EVALUATING,
            round_number=3,
        )
        NegotiationMessage.objects.create(
            room=room,
            sender_type=ActorType.EXTERNAL_AGENT,
            sender_id=hotel_agent.id,
            message_type=NegotiationMessageType.PROPOSAL,
            content={"text": "OK. €700 final price, no phone, 48h cancellation."},
            round_number=3,
        )
        decision3 = PolicyDecision.objects.create(
            proposal=proposal3,
            constitution_version=active_version,
            outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=RiskLevel.LOW,
            reason="Amount €700 exceeds auto-approve limit of €200",
            matched_rules=[
                {
                    "rule_id": "rule-23",
                    "rule_number": 23,
                    "name": "Large payments need approval",
                    "action": "REQUIRE_APPROVAL",
                    "triggered_by": "amount > 200",
                }
            ],
            evaluation_duration_ms=10,
            engine_version="1.0.0",
        )
        approval3 = create_approval_request(
            proposal=proposal3,
            policy_decision=decision3,
            room=room,
        )
        process_approval_decision(
            request=approval3,
            user=alice,
            decision=ApprovalStatus.APPROVED,
            comment="Approved",
        )
        proposal3.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS("  ✓ Round 3: €700, no phone → REQUIRE_APPROVAL → APPROVED")
        )

        agreement = create_agreement_from_proposal(
            proposal=proposal3,
            user=alice,
        )
        sign_agreement(
            agreement=agreement,
            user=alice,
            ip_address="127.0.0.1",
            user_agent_string="Seed Script",
        )
        self.stdout.write(self.style.SUCCESS(f"  ✓ Agreement signed: {agreement.reference_code}"))

        return room, agreement

    def _print_summary(
        self,
        alice: Any,
        bob: Any,
        room: NegotiationRoom,
        agreement: Agreement,
    ) -> None:
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Seed data created successfully!"))
        self.stdout.write("=" * 60)
        self.stdout.write("\n🔑 Demo credentials:")
        self.stdout.write("  Email: alice@example.com")
        self.stdout.write("  Password: alice1234")
        self.stdout.write("\n  Email: bob@example.com")
        self.stdout.write("  Password: bob1234")
        self.stdout.write("\n📊 Demo data:")
        self.stdout.write("  - 2 users")
        self.stdout.write("  - 3 agents (1 user, 2 simulated)")
        self.stdout.write("  - 1 constitution with 5 rules")
        self.stdout.write("  - 1 completed negotiation (3 rounds)")
        self.stdout.write("  - 1 signed agreement")
        self.stdout.write("  - Full audit trail")
        self.stdout.write("\n🌐 API endpoints:")
        self.stdout.write("  GET /api/v1/constitutions/")
        self.stdout.write(f"  GET /api/v1/negotiations/{room.id}/")
        self.stdout.write(f"  GET /api/v1/agreements/{agreement.id}/")
        self.stdout.write(f"  GET /api/v1/audit/entities/NegotiationRoom/{room.id}/")
        self.stdout.write("=" * 60)
