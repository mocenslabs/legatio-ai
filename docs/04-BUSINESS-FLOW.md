# Legatio AI — Business Flow Specification

> **Version:** 1.0
> **Status:** Approved
> **Date:** August 19, 2026
> **Author:** Architecture Team
> **Repository:** `legatio-ai/legatio`
> **Depends on:** `01-PRD.md` (v1.0), `02-ARCHITECTURE.md` (v1.0), `03-DATA-MODEL.md` (v1.0)

---

## Table of Contents

1. [Document Purpose](#1-document-purpose)
2. [Core Flow Principles](#2-core-flow-principles)
3. [System-Wide Sequence: The Golden Path](#3-system-wide-sequence-the-golden-path)
4. [Use Case 1: AI Travel Negotiation (Primary MVP)](#4-use-case-1-ai-travel-negotiation-primary-mvp)
5. [Use Case 2: Subscription Negotiation](#5-use-case-2-subscription-negotiation)
6. [Use Case 3: Purchase Approval](#6-use-case-3-purchase-approval)
7. [Policy Engine Evaluation Algorithm](#7-policy-engine-evaluation-algorithm)
8. [State Machines](#8-state-machines)
9. [Human Approval Workflow](#9-human-approval-workflow)
10. [Agreement Generation and Signing Flow](#10-agreement-generation-and-signing-flow)
11. [Error Handling and Fail-Safe Behaviors](#11-error-handling-and-fail-safe-behaviors)
12. [Timeout and Expiration Handling](#12-timeout-and-expiration-handling)
13. [Concurrency and Race Conditions](#13-concurrency-and-race-conditions)
14. [WebSocket Event Flow](#14-websocket-event-flow)
15. [Audit Event Generation Rules](#15-audit-event-generation-rules)
16. [Onboarding Flow](#16-onboarding-flow)
17. [Change History](#17-change-history)

---

## 1. Document Purpose

This document specifies **how the system behaves over time**. While `03-DATA-MODEL.md` defines what data exists, this document defines:

- The exact sequence of operations for each MVP use case.
- Every state transition and its guards.
- The Policy Engine evaluation algorithm in pseudocode.
- Error handling, timeouts, and fail-safe behaviors.
- Concurrency rules.

**This document must be consulted before:**

- Implementing any service-layer logic.
- Writing integration tests.
- Debugging unexpected state transitions.
- Adding new use cases.

---

## 2. Core Flow Principles

### 2.1 The Inviolable Rule

```text
AI proposes. Policy Engine decides. Human approves when required.
```

No flow in the system may bypass this rule. Any code path that allows an LLM to directly change state without Policy Engine evaluation is a **critical bug**.

### 2.2 Every Action Produces an Audit Event

There are no silent operations. If it changes state, it creates an `AuditEvent`. If it evaluates a policy, it creates a `PolicyDecision`. If it requests approval, it creates an `ApprovalRequest`.

### 2.3 Fail-Safe Defaults

| Failure | System Behavior |
|---------|----------------|
| LLM API unreachable | Negotiation pauses; user notified; no auto-ALLOW |
| Policy Engine exception | Treated as `DENY` with `ERROR` outcome |
| Database write failure | Transaction rollback; no partial state |
| WebSocket disconnect | Client reconnects; missed events fetched via REST |
| External agent timeout | Negotiation marked `EXPIRED` after TTL |
| Approval expires | Proposal marked `REJECTED`; user notified |

### 2.4 Idempotency

All state-changing API endpoints must be idempotent. Clients may retry safely. Idempotency keys are required for:

- `POST /api/v1/proposals/`
- `POST /api/v1/approvals/{id}/approve`
- `POST /api/v1/approvals/{id}/reject`
- `POST /api/v1/agreements/{id}/sign`

### 2.5 Transaction Boundaries

The following operations are **atomic** (single database transaction):

1. Proposal evaluation + PolicyDecision creation + AuditEvent.
2. Approval decision + Proposal status update + Agreement creation (if approved) + AuditEvent.
3. Agreement signing + AgreementSignature + AuditEvent.
4. Constitution activation + previous version archival + AuditEvent.

---

## 3. System-Wide Sequence: The Golden Path

This is the complete happy-path sequence for a negotiation that ends in a signed agreement.

```text
┌──────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  ┌────────────┐  ┌─────────┐  ┌──────────┐
│ User │  │ Vue SPA  │  │ Django  │  │ Negotiation  │  │   Policy   │  │  Human  │  │ External │
│      │  │ Frontend │  │   API   │  │   Service    │  │   Engine   │  │ Approval│  │  Agent   │
└──┬───┘  └────┬─────┘  └────┬────┘  └──────┬───────┘  └─────┬──────┘  └────┬────┘  └────┬─────┘
   │           │             │              │                │              │             │
   │ 1. Define Constitution  │              │                │              │             │
   │──────────>│             │              │                │              │             │
   │           │ POST /constitutions/       │                │              │             │
   │           │────────────>│              │                │              │             │
   │           │             │ Create Constitution + Rules   │              │             │
   │           │             │─────────────>│                │              │             │
   │           │             │              │ AuditEvent     │              │             │
   │           │             │<─────────────│                │              │             │
   │           │<────────────│              │                │              │             │
   │           │  201 Created│              │                │              │             │
   │<──────────│             │              │                │              │             │
   │           │             │              │                │              │             │
   │ 2. Start Negotiation    │              │                │              │             │
   │──────────>│             │              │                │              │             │
   │           │ POST /negotiations/        │                │              │             │
   │           │────────────>│              │                │              │             │
   │           │             │ Create Room  │                │              │             │
   │           │             │─────────────>│                │              │             │
   │           │             │              │ WS: negotiation.started       │             │
   │           │<─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─│                │              │             │
   │           │             │              │                │              │             │
   │           │             │              │ 3. Send instruction to User Agent            │
   │           │             │              │──────────────────────────────────────────────>│
   │           │             │              │                │              │             │
   │           │             │              │ 4. External Agent proposes                    │
   │           │             │              │<──────────────────────────────────────────────│
   │           │             │              │                │              │             │
   │           │             │              │ 5. Evaluate via Policy Engine │             │
   │           │             │              │───────────────>│              │             │
   │           │             │              │                │ ALLOW/DENY/  │             │
   │           │             │              │                │ APPROVAL     │             │
   │           │             │              │<───────────────│              │             │
   │           │             │              │                │              │             │
   │           │             │              │ 6a. If ALLOW → Continue       │             │
   │           │             │              │ 6b. If DENY → Counter-offer   │             │
   │           │             │              │ 6c. If APPROVAL → Notify      │             │
   │           │             │              │──────────────────────────────>│             │
   │           │             │              │                │              │             │
   │           │             │              │                │    7. Human decides         │
   │           │             │              │                │              │─────┐       │
   │           │             │              │                │              │     │       │
   │           │             │              │                │              │<────┘       │
   │           │             │              │<──────────────────────────────│             │
   │           │             │              │                │              │             │
   │           │             │              │ 8. Generate Agreement         │             │
   │           │             │              │───────┐        │              │             │
   │           │             │              │       │        │              │             │
   │           │             │              │<──────┘        │              │             │
   │           │             │              │                │              │             │
   │           │             │              │ 9. Notify user for final approval            │
   │           │<─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─│ WS: agreement.created        │             │
   │           │             │              │                │              │             │
   │ 10. Review & Sign       │              │                │              │             │
   │──────────>│             │              │                │              │             │
   │           │ POST /agreements/{id}/sign │                │              │             │
   │           │────────────>│              │                │              │             │
   │           │             │ Sign + Hash  │                │              │             │
   │           │             │─────────────>│                │              │             │
   │           │             │              │ AuditEvent     │              │             │
   │           │             │<─────────────│                │              │             │
   │           │<────────────│              │                │              │             │
   │           │  200 OK     │              │                │              │             │
   │<──────────│             │              │                │              │             │
```

---

## 4. Use Case 1: AI Travel Negotiation (Primary MVP)

### 4.1 Scenario Definition

**User instruction:**
> "Find me a hotel in Madrid for 5 nights. Don't spend more than €700 and never share my phone number."

**Active Constitution:**

| Rule # | Name | Category | Field | Operator | Value | Action |
|--------|------|----------|-------|----------|-------|--------|
| 1 | Max transaction | FINANCIAL | amount | ≤ | 700 | ALLOW |
| 17 | Never share phone | PRIVACY | phone_number | EQUALS | true | DENY |
| 23 | Large payments | FINANCIAL | amount | > | 200 | REQUIRE_APPROVAL |
| 31 | Email sharing | PRIVACY | email | EQUALS | true | ALLOW |

### 4.2 Detailed Sequence

```text
ROUND 0: SETUP
──────────────
User → Vue SPA: "Find hotel in Madrid, 5 nights, < €700, never share phone"
Vue SPA → Django API: POST /api/v1/negotiations/
  {
    "user_agent_id": "uuid-user-agent",
    "external_agent_id": "uuid-hotel-agent",
    "title": "Hotel Madrid 5 nights",
    "user_instruction": "Find hotel in Madrid for 5 nights. Max €700. Never share phone.",
    "max_rounds": 10
  }

Django API:
  1. Validate user owns user_agent
  2. Load active ConstitutionVersion for user_agent
  3. Create NegotiationRoom (status=PENDING)
  4. Create AuditEvent (negotiation.started)
  5. Emit WS event: negotiation.started
  6. Return 201 with room_id

ROUND 1: INITIAL PROPOSAL
──────────────────────────
Negotiation Service → Hotel Agent (simulated):
  "User wants hotel in Madrid, 5 nights. What's your offer?"

Hotel Agent → Negotiation Service:
  "€820 for 5 nights, breakfast included."

Negotiation Service:
  1. Create NegotiationMessage (sender=hotel_agent, type=PROPOSAL)
  2. Parse into structured Proposal:
     {
       "action_type": "purchase",
       "amount": 820.00,
       "currency": "EUR",
       "data_fields_requested": [],
       "terms": {"nights": 5, "breakfast": true}
     }
  3. Create Proposal record (status=RECEIVED)
  4. Emit WS event: proposal.created

ROUND 2: POLICY EVALUATION
───────────────────────────
Negotiation Service → Policy Engine:
  evaluate(proposal, constitution_version)

Policy Engine:
  Rule 1: amount 820 ≤ 700? NO → does not match ALLOW
  Rule 23: amount 820 > 200? YES → REQUIRE_APPROVAL
  Rule 17: phone_number in data_fields? NO → not triggered

  Result: REQUIRE_HUMAN_APPROVAL
  Reason: "Amount €820 exceeds auto-approve limit of €200"
  Risk: LOW
  Matched rules: [Rule #23]

Negotiation Service:
  1. Create PolicyDecision (outcome=REQUIRE_HUMAN_APPROVAL)
  2. Update Proposal status → PENDING_APPROVAL
  3. Create AuditEvent (proposal.evaluated)
  4. Create ApprovalRequest
  5. Emit WS event: approval.required
  6. Send email notification

ROUND 3: HUMAN DECISION
────────────────────────
User receives notification:
  "⚠️ Approval required. Your agent negotiated €820 for Madrid hotel.
   Exceeds auto-approve limit of €200. [Review] [Approve] [Reject]"

User → Vue SPA: "Reject. Too expensive. Counter with €650."

Vue SPA → Django API: POST /api/v1/approvals/{id}/reject
  {"comment": "Too expensive. Counter with €650."}

Django API (atomic transaction):
  1. Create ApprovalDecision (decision=REJECTED)
  2. Update ApprovalRequest status → REJECTED
  3. Update Proposal status → REJECTED
  4. Create AuditEvent (approval.rejected)
  5. Notify Negotiation Service

ROUND 4: COUNTER-OFFER
──────────────────────
Negotiation Service → LLM (Negotiation Engine):
  "User rejected €820. Generate counter-offer around €650."

LLM → Negotiation Service:
  "Counter-offer: €650 for 5 nights."

Negotiation Service → Hotel Agent:
  "We offer €650 for 5 nights."

Hotel Agent → Negotiation Service:
  "I can do €680, but I need your phone number for the booking."

Negotiation Service:
  1. Create NegotiationMessage
  2. Parse into Proposal:
     {
       "action_type": "purchase",
       "amount": 680.00,
       "currency": "EUR",
       "data_fields_requested": ["phone_number"],
       "terms": {"nights": 5}
     }
  3. Create Proposal (status=RECEIVED)
  4. Emit WS event: proposal.created

ROUND 5: CRITICAL POLICY EVALUATION
────────────────────────────────────
Negotiation Service → Policy Engine:
  evaluate(proposal, constitution_version)

Policy Engine:
  Rule 17: phone_number in data_fields_requested? YES → DENY (IMMEDIATE)

  Result: DENY
  Reason: "Proposal requests phone_number, forbidden by Rule #17 (Never share phone)"
  Risk: CRITICAL
  Matched rules: [Rule #17]

Negotiation Service:
  1. Create PolicyDecision (outcome=DENY, risk=CRITICAL)
  2. Update Proposal status → DENIED
  3. Create AuditEvent (proposal.denied)
  4. DO NOT forward to user. DO NOT ask for approval.
  5. Trigger counter-offer generation.

ROUND 6: AUTO COUNTER-OFFER (NO HUMAN NEEDED)
──────────────────────────────────────────────
Negotiation Service → LLM:
  "Proposal denied: phone sharing forbidden. Generate counter-offer
   without phone sharing, keeping price ≤ €700."

LLM → Negotiation Service:
  "Counter-offer: €680 without phone number sharing."

Negotiation Service → Hotel Agent:
  "€680, but without sharing phone number."

Hotel Agent → Negotiation Service:
  "OK. €700 final price, no phone, 48h cancellation."

ROUND 7: FINAL EVALUATION
──────────────────────────
Negotiation Service:
  1. Create Proposal:
     {
       "action_type": "purchase",
       "amount": 700.00,
       "currency": "EUR",
       "data_fields_requested": [],
       "terms": {"nights": 5, "cancellation": "48h"}
     }

Policy Engine:
  Rule 1: amount 700 ≤ 700? YES → ALLOW
  Rule 17: phone_number in data_fields? NO → not triggered
  Rule 23: amount 700 > 200? YES → REQUIRE_APPROVAL

  Result: REQUIRE_HUMAN_APPROVAL
  Reason: "Amount €700 exceeds auto-approve limit of €200"
  Risk: LOW

ROUND 8: FINAL HUMAN APPROVAL
──────────────────────────────
User receives:
  "✅ Agreement reached: Hotel Madrid, 5 nights, €700, 48h cancellation.
   No phone shared. Requires your approval. [Approve] [Reject]"

User → Approve.

ROUND 9: AGREEMENT GENERATION
──────────────────────────────
Django API (atomic transaction):
  1. Create ApprovalDecision (decision=APPROVED)
  2. Update Proposal status → ACCEPTED
  3. Generate canonical JSON
  4. Compute SHA-256 hash
  5. Create Agreement (status=DRAFT)
  6. Create AuditEvent (agreement.created)
  7. Emit WS event: agreement.created

ROUND 10: SIGNING
──────────────────
User → Vue SPA: "Sign agreement"
Vue SPA → Django API: POST /api/v1/agreements/{id}/sign

Django API (atomic transaction):
  1. Verify canonical_hash matches
  2. Create AgreementSignature
  3. Update Agreement status → SIGNED
  4. Update NegotiationRoom status → COMPLETED
  5. Create AuditEvent (agreement.signed)
  6. Emit WS event: agreement.signed
  7. Send confirmation email
```

### 4.3 Expected Audit Trail

```text
09:42:00  negotiation.started       NEG-2026-000421
09:42:05  proposal.received         PROP-001 (€820)
09:42:06  proposal.evaluated        DECISION-001 → REQUIRE_APPROVAL
09:42:07  approval.requested        APR-001
09:43:15  approval.rejected         APR-001 (user rejected)
09:43:20  counterproposal.created   COUNTER-001 (€650)
09:43:25  proposal.received         PROP-002 (€680 + phone)
09:43:26  proposal.evaluated        DECISION-002 → DENY (Rule #17)
09:43:27  proposal.denied           PROP-002
09:43:30  counterproposal.created   COUNTER-002 (€680 no phone)
09:43:35  proposal.received         PROP-003 (€700 final)
09:43:36  proposal.evaluated        DECISION-003 → REQUIRE_APPROVAL
09:43:37  approval.requested        APR-002
09:44:10  approval.approved         APR-002
09:44:11  agreement.created         AGR-2026-000184
09:44:30  agreement.signed          AGR-2026-000184
09:44:30  negotiation.completed     NEG-2026-000421
```

---

## 5. Use Case 2: Subscription Negotiation

### 5.1 Scenario Definition

**User instruction:**
> "Negotiate my internet bill. I want to pay less than €100/month and I don't want auto-renewal."

**Active Constitution:**

| Rule # | Name | Category | Field | Operator | Value | Action |
|--------|------|----------|-------|----------|-------|--------|
| 1 | Max monthly spend | FINANCIAL | amount | ≤ | 100 | ALLOW |
| 5 | Auto-approve limit | FINANCIAL | amount | ≤ | 50 | ALLOW |
| 12 | Max contract length | NEGOTIATION | contract_length_months | ≤ | 12 | ALLOW |
| 15 | Auto-renewal | NEGOTIATION | auto_renewal | EQUALS | true | REQUIRE_APPROVAL |
| 20 | Price increase | FINANCIAL | price_increase_pct | > | 10 | REQUIRE_APPROVAL |

### 5.2 Flow Summary

```text
1. User starts negotiation
2. ISP Agent offers: €60/month, 24 months, auto-renewal
3. Policy Engine:
   - €60 ≤ €100 ✓
   - 24 months > 12 months → DENY (Rule #12)
   Result: DENY
   Reason: "Contract length 24 months exceeds maximum of 12 months"

4. User Agent counter-offers: "Max 12 months, no auto-renewal"
5. ISP Agent: "€70/month, 12 months, no auto-renewal"
6. Policy Engine:
   - €70 ≤ €100 ✓
   - 12 months ≤ 12 months ✓
   - auto_renewal = false ✓
   - €70 > €50 (auto-approve) → REQUIRE_APPROVAL
   Result: REQUIRE_HUMAN_APPROVAL

7. User approves
8. Agreement generated and signed
```

### 5.3 Key Difference from Use Case 1

This use case demonstrates that **DENY can be triggered by non-financial rules** (contract length). The Policy Engine is not limited to money; it evaluates any typed field.

---

## 6. Use Case 3: Purchase Approval

### 6.1 Scenario Definition

**User instruction:**
> "Buy the book 'Clean Architecture' if it costs less than €30."

**Active Constitution:**

| Rule # | Name | Category | Field | Operator | Value | Action |
|--------|------|----------|-------|----------|-------|--------|
| 1 | Max transaction | FINANCIAL | amount | ≤ | 50 | ALLOW |
| 5 | Auto-approve limit | FINANCIAL | amount | ≤ | 20 | ALLOW |
| 8 | Allowed categories | CUSTOM | category | IN | ["books", "electronics"] | ALLOW |
| 10 | Prohibited categories | CUSTOM | category | IN | ["gambling"] | DENY |
| 15 | New vendor | CUSTOM | is_new_vendor | EQUALS | true | REQUIRE_APPROVAL |

### 6.2 Flow Summary

```text
1. User starts negotiation
2. Vendor Agent: "Clean Architecture costs €25"
3. Policy Engine:
   - €25 ≤ €50 ✓
   - category "books" IN allowed ✓
   - €25 > €20 (auto-approve) → REQUIRE_APPROVAL
   Result: REQUIRE_HUMAN_APPROVAL

4. User receives:
   "📚 Purchase: Clean Architecture, €25.
    Exceeds auto-approve limit of €20. [Approve] [Reject]"

5. User approves
6. Agreement generated (no negotiation needed — direct purchase)
7. Audit trail records purchase
```

### 6.3 Key Difference

This use case demonstrates the **simplest flow**: no back-and-forth negotiation. The Policy Engine still evaluates, and human approval is still required because the amount exceeds the auto-approve threshold.

---

## 7. Policy Engine Evaluation Algorithm

### 7.1 Pseudocode

```python
def evaluate_policy(
    action: ProposedAction,
    constitution_version: ConstitutionVersion,
) -> PolicyDecision:
    """
    Deterministic policy evaluation.
    No LLM. No randomness. Same input → same output.
    """
    start_time = now()
    matched_rules = []
    requires_approval = False
    approval_reasons = []

    # Load rules sorted by priority (lower number = higher priority)
    rules = constitution_version.rules.order_by("priority", "rule_number")

    for rule in rules:
        if not rule.is_active:
            continue

        # Evaluate rule condition against action
        matches = evaluate_condition(rule, action)

        if matches:
            matched_rules.append(rule)

            if rule.action == RuleAction.DENY:
                # DENY is immediate and final. Stop evaluation.
                return PolicyDecision(
                    outcome=PolicyDecisionOutcome.DENY,
                    risk_level=assess_risk(rule, action),
                    reason=f"Blocked by Rule #{rule.rule_number}: {rule.name}",
                    matched_rules=[rule.to_dict()],
                    evaluation_duration_ms=elapsed(start_time),
                    engine_version=ENGINE_VERSION,
                )

            elif rule.action == RuleAction.REQUIRE_APPROVAL:
                requires_approval = True
                approval_reasons.append(
                    f"Rule #{rule.rule_number}: {rule.name}"
                )

    # If we get here, no DENY was triggered

    if requires_approval:
        return PolicyDecision(
            outcome=PolicyDecisionOutcome.REQUIRE_HUMAN_APPROVAL,
            risk_level=assess_risk_from_matched(matched_rules),
            reason="; ".join(approval_reasons),
            matched_rules=[r.to_dict() for r in matched_rules],
            evaluation_duration_ms=elapsed(start_time),
            engine_version=ENGINE_VERSION,
        )

    # No DENY, no REQUIRE_APPROVAL → ALLOW
    return PolicyDecision(
        outcome=PolicyDecisionOutcome.ALLOW,
        risk_level=RiskLevel.LOW,
        reason="All policy checks passed",
        matched_rules=[r.to_dict() for r in matched_rules],
        evaluation_duration_ms=elapsed(start_time),
        engine_version=ENGINE_VERSION,
    )
```

### 7.2 Condition Evaluation

```python
def evaluate_condition(rule: PolicyRule, action: ProposedAction) -> bool:
    """Evaluate a single rule condition against the action."""

    # Extract the field value from the action
    field_value = get_field_value(action, rule.field)

    # If field is not present in action, rule does not apply
    if field_value is None:
        # Special case: privacy rules check for field presence
        if rule.category == RuleCategory.PRIVACY:
            return rule.field in action.data_fields_requested
        return False

    # Apply operator
    match rule.operator:
        case RuleOperator.EQUALS:
            return field_value == rule.value
        case RuleOperator.NOT_EQUALS:
            return field_value != rule.value
        case RuleOperator.GREATER_THAN:
            return field_value > rule.value
        case RuleOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= rule.value
        case RuleOperator.LESS_THAN:
            return field_value < rule.value
        case RuleOperator.LESS_THAN_OR_EQUAL:
            return field_value <= rule.value
        case RuleOperator.CONTAINS:
            return rule.value in field_value
        case RuleOperator.NOT_CONTAINS:
            return rule.value not in field_value
        case RuleOperator.IN:
            return field_value in rule.value
        case RuleOperator.NOT_IN:
            return field_value not in rule.value

    return False
```

### 7.3 Risk Assessment

```python
def assess_risk(rule: PolicyRule, action: ProposedAction) -> RiskLevel:
    """Assign risk level based on rule category and action."""

    if rule.category == RuleCategory.PRIVACY:
        if rule.field in ["health_data", "location", "phone_number"]:
            return RiskLevel.CRITICAL
        return RiskLevel.HIGH

    if rule.category == RuleCategory.FINANCIAL:
        if action.amount and action.amount > 500:
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    if rule.category == RuleCategory.NEGOTIATION:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW
```

### 7.4 Error Handling in Policy Engine

```python
def safe_evaluate(action, constitution_version) -> PolicyDecision:
    """Wrapper that ensures fail-safe behavior."""
    try:
        return evaluate_policy(action, constitution_version)
    except Exception as e:
        # CRITICAL: On any error, default to DENY.
        # Never ALLOW on error.
        logger.critical(f"Policy Engine error: {e}", exc_info=True)
        return PolicyDecision(
            outcome=PolicyDecisionOutcome.ERROR,
            risk_level=RiskLevel.CRITICAL,
            reason=f"Policy evaluation failed: {str(e)}. Action blocked for safety.",
            matched_rules=[],
            evaluation_duration_ms=0,
            engine_version=ENGINE_VERSION,
        )
```

**Invariant:** `PolicyDecisionOutcome.ERROR` is treated identically to `DENY` by all downstream services.

---

## 8. State Machines

### 8.1 NegotiationRoom State Machine

```text
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │ external agent connected
                         ▼
                    ┌──────────┐
          ┌────────│IN_PROGRESS│────────┐
          │        └────┬─────┘        │
          │             │              │
          │    proposal needs          │ max_rounds
          │    approval                │ exceeded
          │             │              │
          │             ▼              ▼
          │     ┌───────────────┐  ┌────────┐
          │     │AWAITING_      │  │ FAILED │
          │     │APPROVAL       │  └────────┘
          │     └───────┬───────┘
          │             │
          │    ┌────────┼────────┐
          │    │        │        │
          │    ▼        ▼        ▼
          │ approved rejected  expired
          │    │        │        │
          │    ▼        ▼        ▼
          │ ┌────────┐ ┌─────────┐ ┌─────────┐
          │ │COMPLETED│ │CANCELLED│ │ EXPIRED │
          │ └────────┘ └─────────┘ └─────────┘
          │
          │ user cancels at any time
          └──────────────────────────> CANCELLED
```

**Transition Guards:**

| From | To | Guard |
|------|----|-------|
| PENDING | IN_PROGRESS | External agent accepted connection |
| IN_PROGRESS | AWAITING_APPROVAL | PolicyDecision = REQUIRE_HUMAN_APPROVAL |
| IN_PROGRESS | FAILED | Unrecoverable error or max_rounds exceeded |
| AWAITING_APPROVAL | COMPLETED | ApprovalDecision = APPROVED + Agreement signed |
| AWAITING_APPROVAL | CANCELLED | ApprovalDecision = REJECTED |
| AWAITING_APPROVAL | EXPIRED | ApprovalRequest.expires_at < now() |
| Any | CANCELLED | User explicitly cancels |

**Side Effects:**

| Transition | Side Effect |
|------------|-------------|
| → IN_PROGRESS | AuditEvent: negotiation.started |
| → AWAITING_APPROVAL | Create ApprovalRequest; WS: approval.required; Email |
| → COMPLETED | AuditEvent: negotiation.completed; Email confirmation |
| → CANCELLED | AuditEvent: negotiation.cancelled; Notify external agent |
| → FAILED | AuditEvent: system.error; Notify user |
| → EXPIRED | AuditEvent: approval.expired; Notify user |

### 8.2 Proposal State Machine

```text
┌──────────┐
│ RECEIVED │
└────┬─────┘
     │ Policy Engine evaluates
     ▼
┌──────────┐
│EVALUATING│
└────┬─────┘
     │
     ├──────────────────┬──────────────────┐
     ▼                  ▼                  ▼
┌─────────┐      ┌──────────┐      ┌─────────────────┐
│ ALLOWED │      │  DENIED  │      │PENDING_APPROVAL │
└────┬────┘      └──────────┘      └────────┬────────┘
     │                                      │
     │ counterparty accepts         ┌───────┼───────┐
     ▼                              ▼       ▼       ▼
┌──────────┐                   approved rejected expired
│ ACCEPTED │                      │       │       │
└──────────┘                      ▼       ▼       ▼
     │                       ┌────────┐ ┌────────┐ ┌────────┐
     │ superseded by newer   │ACCEPTED│ │REJECTED│ │EXPIRED │
     ▼                       └────────┘ └────────┘ └────────┘
┌───────────┐
│ SUPERSEDED│
└───────────┘
```

### 8.3 ApprovalRequest State Machine

```text
┌─────────┐
│ PENDING │
└────┬────┘
     │
     ├──────────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌─────────┐
│ APPROVED ││ REJECTED ││ MODIFIED ││ EXPIRED │
└──────────┘└──────────┘└──────────┘└─────────┘
```

**Guards:**

- APPROVED/REJECTED/MODIFIED: Only the owning user can decide. 2FA required for amounts > €100.
- EXPIRED: Automatic via Celery Beat job scanning `expires_at < now()`.
- Once in a terminal state, no further transitions allowed.

### 8.4 Agreement State Machine

```text
┌───────┐
│ DRAFT │
└───┬───┘
    │ user signs
    ▼
┌────────┐
│ SIGNED │
└───┬────┘
    │ user confirms execution
    ├──────────────────────┐
    ▼                      ▼
┌──────────┐         ┌──────────┐
│ EXECUTED │         │  VOIDED  │
└──────────┘         └──────────┘
```

**Guards:**

- DRAFT → SIGNED: Requires canonical_hash verification + 2FA.
- SIGNED → EXECUTED: User confirms the real-world action happened.
- SIGNED → VOIDED: User revokes within 24h window (configurable).
- EXECUTED and VOIDED are terminal.

### 8.5 Constitution State Machine

```text
┌───────┐
│ DRAFT │
└───┬───┘
    │ user activates
    ▼
┌────────┐
│ ACTIVE │  ← Only ONE per agent
└───┬────┘
    │ new version activated
    ▼
┌──────────┐
│ ARCHIVED │
└──────────┘
```

**Guards:**

- DRAFT → ACTIVE: All rules must be valid. Previous ACTIVE version auto-archives.
- ACTIVE → ARCHIVED: Automatic when new version activates.
- ARCHIVED is terminal.

---

## 9. Human Approval Workflow

### 9.1 Approval Request Creation

Triggered when Policy Engine returns `REQUIRE_HUMAN_APPROVAL`.

```python
def create_approval_request(
    proposal: Proposal,
    policy_decision: PolicyDecision,
    room: NegotiationRoom,
) -> ApprovalRequest:
    """Create approval request within the same transaction as PolicyDecision."""

    request = ApprovalRequest.objects.create(
        proposal=proposal,
        room=room,
        requested_by=room.user_agent,
        policy_decision=policy_decision,
        status=ApprovalStatus.PENDING,
        summary=generate_human_summary(proposal, policy_decision),
        expires_at=now() + timedelta(hours=24),
    )

    # Emit real-time notification
    emit_websocket_event(room.owner, "approval.required", {
        "approval_id": str(request.id),
        "summary": request.summary,
        "risk_level": policy_decision.risk_level,
        "expires_at": request.expires_at.isoformat(),
    })

    # Queue email notification
    send_approval_email.delay(request.id)

    return request
```

### 9.2 Human Summary Generation

The summary must be **human-readable**, not technical. Example:

```text
⚠️ Approval Required

Your agent negotiated a €700 hotel stay in Madrid.

Details:
  Original price:    €820
  Negotiated price:  €700
  Discount:          14.6%
  Your limit:        €700 (Constitution Rule #1)
  Auto-approve:      €200 (Constitution Rule #23)
  Phone shared:      No ✓
  Risk level:        Low

Decision required: Human approval (amount exceeds auto-approve limit)

[Approve]  [Reject]  [Modify]
```

### 9.3 Approval Decision Processing

```python
def process_approval_decision(
    request: ApprovalRequest,
    user: User,
    decision: ApprovalStatus,
    modifications: dict | None = None,
    comment: str | None = None,
) -> ApprovalDecision:
    """Process human decision. Atomic transaction."""

    with transaction.atomic():
        # Lock the approval request to prevent race conditions
        request = ApprovalRequest.objects.select_for_update().get(id=request.id)

        if request.status != ApprovalStatus.PENDING:
            raise ApprovalAlreadyDecidedError()

        if request.expires_at < now():
            request.status = ApprovalStatus.EXPIRED
            request.save()
            raise ApprovalExpiredError()

        # Create decision record
        approval_decision = ApprovalDecision.objects.create(
            request=request,
            decided_by=user,
            decision=decision,
            modifications=modifications,
            comment=comment,
        )

        # Update request status
        request.status = decision
        request.save()

        # Update proposal status
        if decision == ApprovalStatus.APPROVED:
            request.proposal.status = ProposalStatus.ACCEPTED
            request.proposal.save()
            # Trigger agreement generation
            generate_agreement(request.proposal)
        elif decision in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED):
            request.proposal.status = ProposalStatus.REJECTED
            request.proposal.save()
            # Notify negotiation service to continue or terminate
            notify_negotiation_service(request.room, "proposal_rejected")

        # Audit event
        create_audit_event(
            event_type=f"approval.{decision.lower()}",
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="ApprovalRequest",
            entity_id=request.id,
            payload={"decision": decision, "comment": comment},
        )

    return approval_decision
```

### 9.4 Approval Expiration Job

Celery Beat runs every 5 minutes:

```python
@shared_task
def expire_stale_approvals():
    """Expire approvals past their deadline."""
    stale = ApprovalRequest.objects.filter(
        status=ApprovalStatus.PENDING,
        expires_at__lt=now(),
    )

    for request in stale:
        with transaction.atomic():
            request = ApprovalRequest.objects.select_for_update().get(id=request.id)
            if request.status != ApprovalStatus.PENDING:
                continue  # Already decided

            request.status = ApprovalStatus.EXPIRED
            request.save()

            ApprovalDecision.objects.create(
                request=request,
                decided_by=None,  # System decision
                decision=ApprovalStatus.EXPIRED,
            )

            request.proposal.status = ProposalStatus.REJECTED
            request.proposal.save()

            create_audit_event(
                event_type="approval.expired",
                actor_type=ActorType.SYSTEM,
                entity_type="ApprovalRequest",
                entity_id=request.id,
            )

            # Notify user
            send_approval_expired_email.delay(request.id)
```

---

## 10. Agreement Generation and Signing Flow

### 10.1 Canonical JSON Generation

```python
def generate_canonical_json(proposal: Proposal, room: NegotiationRoom) -> dict:
    """Generate canonical JSON for agreement. Deterministic output."""

    canonical = {
        "agreement_id": f"AGR-{now().year}-{generate_sequence():06d}",
        "constitution_version": str(room.constitution_version.id),
        "created_at": now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "negotiation_id": str(room.id),
        "parties": [
            {"id": str(room.user_agent.id), "role": "buyer"},
            {"id": str(room.external_agent.id), "role": "seller"},
        ],
        "terms": {
            "amount": f"{proposal.amount:.2f}",
            "currency": proposal.currency,
            "data_shared": sorted(proposal.data_fields_requested),
            **{k: str(v) for k, v in sorted(proposal.terms.items())},
        },
    }

    return canonical
```

### 10.2 Hash Computation

```python
def compute_canonical_hash(canonical: dict) -> str:
    """Compute SHA-256 hash of canonical JSON."""
    # Serialize with sorted keys, no whitespace
    json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
```

### 10.3 Signing Flow

```python
def sign_agreement(agreement: Agreement, user: User) -> AgreementSignature:
    """Sign agreement. Requires 2FA. Atomic transaction."""

    with transaction.atomic():
        agreement = Agreement.objects.select_for_update().get(id=agreement.id)

        if agreement.status != AgreementStatus.DRAFT:
            raise AgreementNotInDraftError()

        # Verify hash integrity
        recomputed_hash = compute_canonical_hash(agreement.canonical_json)
        if recomputed_hash != agreement.canonical_hash:
            raise HashMismatchError("Agreement has been tampered with")

        # Generate signature (MVP: HMAC-SHA256 with server key)
        signature_value = hmac.new(
            key=SERVER_SIGNING_KEY.encode(),
            msg=agreement.canonical_hash.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        signature = AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            signature_algorithm="HMAC-SHA256",
            signature_value=signature_value,
            signed_payload_hash=agreement.canonical_hash,
            ip_address=get_client_ip(),
            user_agent_string=get_user_agent_string(),
        )

        agreement.status = AgreementStatus.SIGNED
        agreement.signed_at = now()
        agreement.save()

        # Update negotiation room
        agreement.room.status = NegotiationStatus.COMPLETED
        agreement.room.completed_at = now()
        agreement.room.save()

        # Audit
        create_audit_event(
            event_type="agreement.signed",
            actor_type=ActorType.USER,
            actor_id=user.id,
            entity_type="Agreement",
            entity_id=agreement.id,
            payload={"hash": agreement.canonical_hash},
        )

    return signature
```

---

## 11. Error Handling and Fail-Safe Behaviors

### 11.1 Error Classification

| Error Type | Severity | System Response |
|-----------|----------|----------------|
| Policy Engine exception | CRITICAL | Treat as DENY; alert ops; audit |
| LLM API timeout | HIGH | Retry 3x with backoff; pause negotiation |
| LLM API auth failure | CRITICAL | Pause negotiation; notify user |
| Database connection lost | CRITICAL | Retry with backoff; circuit breaker |
| WebSocket disconnect | LOW | Client auto-reconnects |
| External agent timeout | MEDIUM | Mark negotiation EXPIRED after TTL |
| Hash mismatch on signing | CRITICAL | Block signing; alert ops; audit |
| Concurrent approval race | MEDIUM | First decision wins; others rejected |

### 11.2 Circuit Breaker for LLM Calls

```python
# Configuration
LLM_CIRCUIT_BREAKER = {
    "failure_threshold": 5,      # 5 consecutive failures
    "recovery_timeout": 60,      # 60 seconds before retry
    "expected_exceptions": [TimeoutError, APIError],
}
```

When circuit is OPEN:

1. All LLM calls fail immediately (no waiting).
2. Negotiations pause (status remains IN_PROGRESS).
3. Users see: "Negotiation paused due to service issues. We'll resume shortly."
4. Alert sent to ops.

### 11.3 LLM Output Validation

**Critical rule:** LLM output is NEVER trusted directly.

```python
def process_llm_response(response: str, context: NegotiationContext) -> Proposal:
    """Parse and validate LLM output. Never trust raw output."""

    # Step 1: Parse structured output
    try:
        parsed = parse_structured_output(response)
    except ParseError:
        raise LLMOutputInvalidError("Could not parse LLM response")

    # Step 2: Validate against schema
    try:
        validated = ProposalSchema.model_validate(parsed)
    except ValidationError as e:
        raise LLMOutputInvalidError(f"Schema validation failed: {e}")

    # Step 3: Sanity checks
    if validated.amount and validated.amount < 0:
        raise LLMOutputInvalidError("Negative amount")

    if validated.amount and validated.amount > 1_000_000:
        raise LLMOutputInvalidError("Amount exceeds sanity limit")

    # Step 4: Policy Engine will evaluate before any action
    # (This happens in the calling service, not here)

    return validated
```

---

## 12. Timeout and Expiration Handling

### 12.1 Timeout Configuration

| Entity | Timeout | Default | Configurable? |
|--------|---------|---------|---------------|
| NegotiationRoom | `expires_at` | 24 hours | Yes (per negotiation) |
| ApprovalRequest | `expires_at` | 24 hours | Yes (per constitution) |
| External agent response | Per-request timeout | 30 seconds | Yes |
| LLM call | Per-request timeout | 60 seconds | No |
| WebSocket idle | Disconnect | 5 minutes | No |

### 12.2 Negotiation Expiration

Celery Beat runs every 10 minutes:

```python
@shared_task
def expire_stale_negotiations():
    """Expire negotiations past their TTL."""
    stale = NegotiationRoom.objects.filter(
        status__in=[NegotiationStatus.PENDING, NegotiationStatus.IN_PROGRESS],
        expires_at__lt=now(),
    )

    for room in stale:
        room.status = NegotiationStatus.EXPIRED
        room.save()

        create_audit_event(
            event_type="negotiation.expired",
            actor_type=ActorType.SYSTEM,
            entity_type="NegotiationRoom",
            entity_id=room.id,
        )

        notify_user_negotiation_expired.delay(room.id)
```

### 12.3 Max Rounds Protection

To prevent infinite negotiation loops:

```python
def process_incoming_proposal(room: NegotiationRoom, proposal: Proposal):
    """Process proposal with round limit protection."""

    if room.current_round >= room.max_rounds:
        room.status = NegotiationStatus.FAILED
        room.save()

        create_audit_event(
            event_type="negotiation.failed",
            actor_type=ActorType.SYSTEM,
            entity_type="NegotiationRoom",
            entity_id=room.id,
            payload={"reason": "max_rounds_exceeded"},
        )

        notify_user_max_rounds_exceeded.delay(room.id)
        return

    room.current_round += 1
    room.save()

    # Continue with policy evaluation...
```

---

## 13. Concurrency and Race Conditions

### 13.1 Identified Race Conditions

| Scenario | Risk | Mitigation |
|----------|------|-----------|
| Two users approve same proposal | Double approval | `select_for_update()` on ApprovalRequest |
| Proposal evaluated twice | Duplicate PolicyDecision | Idempotency key on evaluation endpoint |
| Constitution activated while negotiation running | Stale rules | Negotiation references specific ConstitutionVersion (immutable) |
| Agreement signed twice | Duplicate signature | Unique constraint on AgreementSignature.agreement |
| Audit hash chain race | Broken chain | Single writer via Redis lock |

### 13.2 Audit Hash Chain Locking

Only one process may append to the audit chain at a time:

```python
AUDIT_CHAIN_LOCK_KEY = "legatio:audit_chain_lock"
AUDIT_CHAIN_LOCK_TTL = 10  # seconds

def create_audit_event(**kwargs) -> AuditEvent:
    """Create audit event with hash chain integrity."""

    with redis_lock(AUDIT_CHAIN_LOCK_KEY, ttl=AUDIT_CHAIN_LOCK_TTL):
        # Get the last event's hash
        last_event = AuditEvent.objects.order_by("-sequence_number").first()
        previous_hash = last_event.event_hash if last_event else None

        # Compute payload hash
        payload_hash = compute_payload_hash(kwargs["payload"])

        # Compute event hash
        event_hash = compute_event_hash(
            event_type=kwargs["event_type"],
            actor_type=kwargs["actor_type"],
            actor_id=kwargs.get("actor_id"),
            entity_type=kwargs["entity_type"],
            entity_id=kwargs["entity_id"],
            previous_hash=previous_hash,
            payload_hash=payload_hash,
        )

        return AuditEvent.objects.create(
            event_hash=event_hash,
            previous_event_hash=previous_hash,
            payload_hash=payload_hash,
            **kwargs,
        )
```

### 13.3 Optimistic Concurrency for Proposals

When updating proposal status, use version checking:

```python
def update_proposal_status(proposal_id: UUID, new_status: ProposalStatus, expected_version: int):
    """Update proposal with optimistic locking."""

    updated = Proposal.objects.filter(
        id=proposal_id,
        version=expected_version,
    ).update(
        status=new_status,
        version=expected_version + 1,
    )

    if updated == 0:
        raise ConcurrentModificationError("Proposal was modified by another process")
```

---

## 14. WebSocket Event Flow

### 14.1 Connection Lifecycle

```text
1. Client connects: wss://api.legatio.ai/ws/?token=<jwt>
2. Django Channels authenticates JWT
3. Client joins rooms:
   - user-{user_id}
   - negotiation-{negotiation_id} (for each active negotiation)
4. Server sends: connection.established
5. Client sends: subscribe {negotiation_ids: [...]}
6. Server confirms: subscription.confirmed
```

### 14.2 Event Sequencing for Use Case 1

```text
Time    Event                       Payload
────────────────────────────────────────────────────────────────
09:42   negotiation.started         {room_id, title}
09:42   proposal.created            {proposal_id, amount: 820}
09:42   proposal.evaluated          {decision: REQUIRE_APPROVAL}
09:42   approval.required           {approval_id, summary}
09:43   approval.rejected           {approval_id}
09:43   counterproposal.created     {counter_id, amount: 650}
09:43   proposal.created            {proposal_id, amount: 680}
09:43   proposal.evaluated          {decision: DENY, risk: CRITICAL}
09:43   proposal.denied             {proposal_id, reason: Rule #17}
09:43   counterproposal.created     {counter_id, amount: 680}
09:43   proposal.created            {proposal_id, amount: 700}
09:43   proposal.evaluated          {decision: REQUIRE_APPROVAL}
09:43   approval.required           {approval_id, summary}
09:44   approval.approved           {approval_id}
09:44   agreement.created           {agreement_id, hash}
09:44   agreement.signed            {agreement_id}
09:44   negotiation.completed       {room_id}
```

### 14.3 Reconnection and Missed Events

```text
1. Client disconnects (network issue)
2. Client reconnects with last_event_timestamp
3. Client calls: GET /api/v1/audit/events?since=<timestamp>&entity_type=NegotiationRoom&entity_id=<room_id>
4. Server returns missed events
5. Client reconciles local state
6. Client resumes WebSocket subscription
```

---

## 15. Audit Event Generation Rules

### 15.1 Mandatory Audit Points

Every operation in this table MUST create an AuditEvent. Missing audit events are a **critical bug**.

| Operation | Event Type | Actor |
|-----------|-----------|-------|
| User registers | user.registered | USER |
| User enables 2FA | user.2fa.enabled | USER |
| Agent created | agent.created | USER |
| Agent credential rotated | agent.credential.rotated | USER |
| Constitution created | constitution.created | USER |
| Constitution version activated | constitution.version.activated | USER |
| Policy rule added | constitution.rule.added | USER |
| Negotiation started | negotiation.started | USER |
| Message received | negotiation.message.created | AGENT |
| Proposal received | proposal.received | AGENT |
| Proposal evaluated | proposal.evaluated | SYSTEM |
| Proposal denied | proposal.denied | SYSTEM |
| Counter-proposal created | counterproposal.created | AGENT |
| Approval requested | approval.requested | SYSTEM |
| Approval approved | approval.approved | USER |
| Approval rejected | approval.rejected | USER |
| Approval expired | approval.expired | SYSTEM |
| Agreement created | agreement.created | SYSTEM |
| Agreement signed | agreement.signed | USER |
| Agreement voided | agreement.voided | USER |
| Negotiation completed | negotiation.completed | SYSTEM |
| Negotiation cancelled | negotiation.cancelled | USER |
| Negotiation expired | negotiation.expired | SYSTEM |
| Policy Engine error | system.policy_error | SYSTEM |
| Hash chain check failed | system.integrity_check.failed | SYSTEM |

### 15.2 Audit Event Payload Standards

Payloads must:

- Include enough information to reconstruct what happened.
- Never include raw PII (phone numbers, emails) — use references.
- Include a `version` key for forward compatibility.
- Be encrypted if containing sensitive data.

Example:

```json
{
  "version": 1,
  "proposal_id": "uuid-here",
  "amount": "700.00",
  "currency": "EUR",
  "data_fields_requested": [],
  "decision": "REQUIRE_HUMAN_APPROVAL",
  "matched_rules": [23],
  "risk_level": "LOW"
}
```

---

## 16. Onboarding Flow

### 16.1 First-Time User Experience

```text
Step 1: Welcome Screen
  "Legatio AI: The trust layer for your AI agents."
  [Get Started]

Step 2: Create Account
  Email + Password + Email verification

Step 3: Create Your First Agent
  "Name your agent:" [My Personal Agent]
  "What will it do?" [Travel bookings] [Shopping] [Subscriptions]

Step 4: Build Your Constitution (Guided)
  "Let's set your rules. Answer these questions:"

  Q1: "What's the maximum amount your agent can spend without asking?"
      [€50] [€100] [€200] [€500] [Custom]

  Q2: "Can your agent share your phone number?"
      [Never] [Only with approval] [Always]

  Q3: "Can your agent share your email?"
      [Never] [Only with approval] [Always]

  Q4: "What's the maximum contract length your agent can agree to?"
      [6 months] [12 months] [24 months] [No limit]

Step 5: Constitution Review
  "Here's your Constitution. You can edit it anytime."
  [Review Rules]  [Activate]

Step 6: First Negotiation (Guided Demo)
  "Let's try it! We'll simulate a hotel booking."
  [Start Demo Negotiation]

Step 7: Demo Complete
  "🎉 You just completed your first Legatio negotiation!
   Your agent negotiated, the Policy Engine protected your rules,
   and you approved the final agreement."
  [View Audit Trail]  [Start Real Negotiation]
```

### 16.2 Onboarding Success Metrics

- User completes constitution in < 3 minutes.
- User completes demo negotiation in < 2 minutes.
- User can explain what the Policy Engine does after onboarding.

---

## 17. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-19 | Architecture Team | Initial approved version. |

---
