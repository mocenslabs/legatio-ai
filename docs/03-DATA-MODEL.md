# Legatio AI — Data Model Specification

> **Version:** 1.0
> **Status:** Approved
> **Date:** August 19, 2026
> **Author:** Architecture Team
> **Repository:** `legatio-ai/legatio`
> **Depends on:** `01-PRD.md` (v1.0), `02-ARCHITECTURE.md` (v1.0)

---

## Table of Contents

1. [Document Purpose](#1-document-purpose)
2. [Data Model Design Principles](#2-data-model-design-principles)
3. [Entity-Relationship Overview](#3-entity-relationship-overview)
4. [Global Conventions](#4-global-conventions)
5. [Enums and Constants](#5-enums-and-constants)
6. [App: accounts](#6-app-accounts)
7. [App: agents](#7-app-agents)
8. [App: constitutions](#8-app-constitutions)
9. [App: negotiations](#9-app-negotiations)
10. [App: proposals](#10-app-proposals)
11. [App: approvals](#11-app-approvals)
12. [App: agreements](#12-app-agreements)
13. [App: audit](#13-app-audit)
14. [App: notifications](#14-app-notifications)
15. [Indexing Strategy](#15-indexing-strategy)
16. [Data Encryption](#16-data-encryption)
17. [Integrity Rules and Constraints](#17-integrity-rules-and-constraints)
18. [Migration Strategy](#18-migration-strategy)
19. [Seed Data and Examples](#19-seed-data-and-examples)
20. [Data Retention and Privacy](#20-data-retention-and-privacy)
21. [Future Schema Considerations](#21-future-schema-considerations)
22. [Change History](#22-change-history)

---

## 1. Document Purpose

This document is the **authoritative specification** for the Legatio AI data model. It defines:

- Every entity (Django model) in the system.
- Every field, its type, constraints, and default value.
- Every relationship and its cardinality.
- Every enum and its allowed values.
- Indexing, encryption, and integrity strategies.

**This document must be consulted before:**

- Creating or modifying any Django model.
- Writing a migration.
- Designing a new API endpoint that touches these entities.
- Debugging data integrity issues.

**Relationship to other documents:**

- `01-PRD.md` defines **what** the product does.
- `02-ARCHITECTURE.md` defines **how** the system is structured.
- `03-DATA-MODEL.md` (this document) defines **how data is stored and related**.

---

## 2. Data Model Design Principles

### 2.1 Relational First

The domain is inherently relational (Users → Agents → Constitutions → Negotiations → Proposals → Decisions → Agreements). PostgreSQL is the single source of truth. JSONB is used **only** for semi-structured payloads (rule conditions, proposal terms, audit payloads), never for data that needs to be queried relationally.

### 2.2 Immutability Where It Matters

The following entities are **append-only** or **versioned** and must never be updated in place:

- `AuditEvent` — strictly append-only.
- `ConstitutionVersion` — immutable once activated.
- `Agreement` — immutable once signed.
- `AgreementSignature` — immutable once created.

Mutable entities (`User`, `Agent`, `Constitution`, `NegotiationRoom`) track changes via `AuditEvent` records.

### 2.3 UUID Primary Keys

All entities use UUIDv4 primary keys. Rationale:

- No information leakage via sequential IDs.
- Safe for distributed ID generation (future microservices).
- Stable references across environments (dev/staging/prod).

### 2.4 Soft Deletes for User-Facing Entities

User-facing entities (`Agent`, `Constitution`, `NegotiationRoom`) use soft deletes (`deleted_at` timestamp). Hard deletes are reserved for GDPR "right to be forgotten" requests, executed via a dedicated anonymization process (see Section 20).

### 2.5 Explicit State Machines

Every entity with a lifecycle has an explicit `status` field with a defined enum. State transitions are validated at the service layer, never implicitly.

### 2.6 Generic Audit References

`AuditEvent` uses a generic reference pattern (`entity_type` + `entity_id`) instead of foreign keys to every auditable entity. This keeps the audit schema stable as new entities are added.

### 2.7 Fail-Safe Defaults

Default values always favor the most restrictive state:

- New `PolicyRule` defaults to `action = DENY` if unspecified.
- New `NegotiationRoom` defaults to `status = PENDING`.
- New `Proposal` defaults to `status = RECEIVED` (not evaluated).

---

## 3. Entity-Relationship Overview

### 3.1 Full ER Diagram

```text
┌────────────────────────────────────────────────────────────────────────┐
│                            ACCOUNTS                                    │
│                                                                        │
│   ┌──────────┐ 1       1 ┌──────────────┐                              │
│   │   User   │───────────│ UserProfile  │                              │
│   └────┬─────┘           └──────────────┘                              │
│        │ 1                                                           │
└────────┼───────────────────────────────────────────────────────────────┘
         │
         │ N
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             AGENTS                                     │
│                                                                        │
│   ┌──────────┐ 1       N ┌──────────────────┐                          │
│   │  Agent   │───────────│    Credential    │                          │
│   └────┬─────┘           └──────────────────┘                          │
│        │ 1                                                           │
│        │ N                                                           │
│        ▼                                                             │
│   ┌──────────────┐                                                   │
│   │ Constitution │                                                   │
│   └────┬─────────┘                                                   │
│        │ 1                                                           │
│        │ N                                                           │
│        ▼                                                             │
│   ┌─────────────────────┐ 1       N ┌──────────────┐                 │
│   │ ConstitutionVersion │───────────│  PolicyRule  │                 │
│   └─────────────────────┘           └──────────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
         │
         │ (referenced by NegotiationRoom)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          NEGOTIATIONS                                  │
│                                                                        │
│   ┌──────────────────┐ 1       N ┌────────────────────┐                │
│   │ NegotiationRoom  │───────────│ NegotiationMessage │                │
│   └────┬─────────────┘           └────────────────────┘                │
│        │ 1                                                           │
│        │ N                                                           │
│        ▼                                                             │
│   ┌──────────┐ 1       N ┌──────────────────┐                          │
│   │ Proposal │───────────│ CounterProposal  │                          │
│   └────┬─────┘           └──────────────────┘                          │
│        │ 1                                                           │
│        │ 0..1                                                        │
│        ▼                                                             │
│   ┌──────────────────┐ 1       N ┌──────────────────┐                  │
│   │ ApprovalRequest  │───────────│ ApprovalDecision │                  │
│   └──────────────────┘           └──────────────────┘                  │
│        │                                                             │
│        │ (on approval)                                               │
│        ▼                                                             │
│   ┌──────────┐ 1       1 ┌─────────────────────┐                       │
│   │ Agreement│───────────│ AgreementSignature  │                       │
│   └──────────┘           └─────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────┘
         │
         │ (every state change produces)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              AUDIT                                     │
│                                                                        │
│   ┌────────────┐  (append-only, hash-chained, generic references)      │
│   │ AuditEvent │                                                       │
│   └────────────┘                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Entity Inventory

| # | Entity | App | Mutable? | Soft Delete? |
|---|--------|-----|----------|--------------|
| 1 | `User` | accounts | Yes | No (anonymized) |
| 2 | `UserProfile` | accounts | Yes | No |
| 3 | `Agent` | agents | Yes | Yes |
| 4 | `Credential` | agents | Yes (rotation) | No |
| 5 | `Constitution` | constitutions | Yes | Yes |
| 6 | `ConstitutionVersion` | constitutions | **No** | No |
| 7 | `PolicyRule` | constitutions | **No** | No |
| 8 | `NegotiationRoom` | negotiations | Yes (state only) | Yes |
| 9 | `NegotiationMessage` | negotiations | **No** | No |
| 10 | `Proposal` | proposals | Yes (state only) | No |
| 11 | `CounterProposal` | proposals | **No** | No |
| 12 | `PolicyDecision` | proposals | **No** | No |
| 13 | `ApprovalRequest` | approvals | Yes (state only) | No |
| 14 | `ApprovalDecision` | approvals | **No** | No |
| 15 | `Agreement` | agreements | **No** | No |
| 16 | `AgreementSignature` | agreements | **No** | No |
| 17 | `AuditEvent` | audit | **No** | No |
| 18 | `Notification` | notifications | Yes (state only) | No |

---

## 4. Global Conventions

### 4.1 Primary Keys

```python
id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False,
)
```

### 4.2 Timestamps

Every entity includes:

```python
created_at = models.DateTimeField(auto_now_add=True, db_index=True)
updated_at = models.DateTimeField(auto_now=True)
```

Append-only entities (`AuditEvent`, `NegotiationMessage`, `PolicyDecision`, `ApprovalDecision`, `AgreementSignature`) include **only** `created_at`.

### 4.3 Soft Deletes

```python
deleted_at = models.DateTimeField(null=True, blank=True, default=None)
```

A custom manager `SoftDeleteManager` filters out soft-deleted records by default.

### 4.4 Naming Conventions

- Table names: `legatio_<app>_<model>` (via `db_table` in Meta).
- Index names: `idx_<table>_<columns>`.
- Constraint names: `chk_<table>_<description>`, `uniq_<table>_<columns>`.
- Enum values: `UPPER_SNAKE_CASE`.

### 4.5 JSONB Fields

All JSONB fields must have:

- A Pydantic schema defined in `core/schemas/`.
- Validation at the service layer before persistence.
- A `version` key inside the JSON for forward compatibility.

Example:

```json
{
  "version": 1,
  "data": { ... }
}
```

---

## 5. Enums and Constants

All enums are defined in `core/enums.py` as `models.TextChoices` subclasses.

### 5.1 AgentType

```text
USER_AGENT      # Acts on behalf of a Legatio user
EXTERNAL_AGENT  # Third-party agent (hotel, ISP, vendor, etc.)
SIMULATED       # Built-in test agent for MVP demos
```

### 5.2 AgentStatus

```text
ACTIVE
SUSPENDED
REVOKED
```

### 5.3 ConstitutionStatus

```text
DRAFT       # Being edited, not enforceable
ACTIVE      # Currently enforced (max 1 per agent)
ARCHIVED    # Superseded by a newer version
```

### 5.4 RuleCategory

```text
FINANCIAL     # Budgets, amounts, auto-approve limits
PRIVACY       # Data sharing rules (phone, email, health, etc.)
NEGOTIATION   # Discount limits, contract length, refunds
CUSTOM        # User-defined rules
```

### 5.5 RuleAction

```text
ALLOW                # Action is permitted
DENY                 # Action is blocked
REQUIRE_APPROVAL     # Action requires human approval
```

### 5.6 RuleOperator

```text
EQUALS
NOT_EQUALS
GREATER_THAN
GREATER_THAN_OR_EQUAL
LESS_THAN
LESS_THAN_OR_EQUAL
CONTAINS
NOT_CONTAINS
IN
NOT_IN
```

### 5.7 NegotiationStatus

```text
PENDING        # Created, waiting for external agent
IN_PROGRESS    # Agents are exchanging proposals
AWAITING_APPROVAL  # Waiting for human decision
COMPLETED      # Agreement reached and approved
CANCELLED      # Cancelled by user or system
FAILED         # Terminated due to error or timeout
EXPIRED        # No activity within TTL
```

### 5.8 ProposalStatus

```text
RECEIVED       # Received, not yet evaluated
EVALUATING     # Policy Engine processing
ALLOWED        # Policy Engine returned ALLOW
DENIED         # Policy Engine returned DENY
PENDING_APPROVAL  # Policy Engine returned REQUIRE_HUMAN_APPROVAL
ACCEPTED       # Accepted by counterparty
REJECTED       # Rejected by counterparty
SUPERSEDED     # Replaced by a newer proposal
```

### 5.9 PolicyDecisionOutcome

```text
ALLOW
DENY
REQUIRE_HUMAN_APPROVAL
ERROR          # Evaluation failed (fail-safe: treated as DENY)
```

### 5.10 RiskLevel

```text
LOW
MEDIUM
HIGH
CRITICAL
```

### 5.11 ApprovalStatus

```text
PENDING
APPROVED
REJECTED
MODIFIED       # Approved with changes
EXPIRED
```

### 5.12 AgreementStatus

```text
DRAFT          # Generated, awaiting user signature
SIGNED         # Cryptographically signed
EXECUTED       # Confirmed as executed by user
VOIDED         # Rejected or revoked
```

### 5.13 NotificationChannel

```text
WEBSOCKET
EMAIL
PUSH           # Future
```

### 5.14 NotificationStatus

```text
PENDING
DELIVERED
READ
FAILED
```

### 5.15 ActorType (Audit)

```text
USER
AGENT
SYSTEM
ADMIN
EXTERNAL_AGENT
```

### 5.16 EventType (Audit)

```text
# Account events
user.registered
user.login
user.2fa.enabled

# Agent events
agent.created
agent.suspended
agent.credential.rotated

# Constitution events
constitution.created
constitution.version.activated
constitution.rule.added

# Negotiation events
negotiation.started
negotiation.message.created
negotiation.completed
negotiation.cancelled

# Proposal events
proposal.received
proposal.evaluated
proposal.denied
counterproposal.created

# Approval events
approval.requested
approval.approved
approval.rejected
approval.expired

# Agreement events
agreement.created
agreement.signed
agreement.executed
agreement.voided

# System events
system.policy_error
system.integrity_check.failed
```

---

## 6. App: accounts

### 6.1 User

Extends `AbstractBaseUser` and `PermissionsMixin`.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `email` | EmailField | unique, max 255 | Login identifier |
| `password` | CharField | max 128 | Hashed via Django |
| `first_name` | CharField | max 100 | |
| `last_name` | CharField | max 100 | |
| `is_active` | BooleanField | default True | |
| `is_staff` | BooleanField | default False | |
| `is_verified` | BooleanField | default False | Email verified |
| `two_factor_enabled` | BooleanField | default False | |
| `totp_secret` | CharField | max 32, null | Encrypted |
| `preferred_language` | CharField | max 10, default "en" | |
| `preferred_timezone` | CharField | max 50, default "UTC" | |
| `last_login` | DateTimeField | null | |
| `date_joined` | DateTimeField | auto_now_add | |

**Indexes:**

- `idx_user_email` on `email` (unique).

### 6.2 UserProfile

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `user` | OneToOne → User | on_delete CASCADE | |
| `display_name` | CharField | max 100, null | |
| `avatar_url` | URLField | null | |
| `notification_preferences` | JSONField | default dict | Channels config |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |

**`notification_preferences` schema:**

```json
{
  "version": 1,
  "websocket": true,
  "email": {
    "approval_required": true,
    "agreement_signed": true,
    "daily_digest": false
  }
}
```

---

## 7. App: agents

### 7.1 Agent

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `owner` | FK → User | on_delete CASCADE, null for external | Null for external agents |
| `agent_type` | CharField | choices AgentType | |
| `name` | CharField | max 100 | |
| `description` | TextField | null | |
| `status` | CharField | choices AgentStatus, default ACTIVE | |
| `external_endpoint_url` | URLField | null | For external agents |
| `capabilities` | JSONField | default list | Advertised capabilities |
| `protocol_version` | CharField | max 20, default "1.0" | |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |
| `deleted_at` | DateTimeField | null | Soft delete |

**Constraints:**

- `uniq_agent_owner_name`: unique (`owner`, `name`) where `deleted_at IS NULL`.

**Indexes:**

- `idx_agent_owner` on `owner`.
- `idx_agent_type` on `agent_type`.
- `idx_agent_status` on `status`.

### 7.2 Credential

API credentials for agent authentication.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `agent` | FK → Agent | on_delete CASCADE | |
| `name` | CharField | max 100 | E.g. "production-key" |
| `key_prefix` | CharField | max 8, unique | Visible prefix, e.g. "lgat_4f2" |
| `key_hash` | CharField | max 128, unique | SHA-256 of full key |
| `scopes` | JSONField | default list | E.g. ["negotiate", "propose"] |
| `last_used_at` | DateTimeField | null | |
| `expires_at` | DateTimeField | null | Null = never expires |
| `revoked_at` | DateTimeField | null | |
| `created_at` | DateTimeField | auto_now_add | |

**Security rules:**

- The full key is shown **once** at creation, never stored.
- Only `key_hash` is persisted.
- Rotation = revoke old + create new (both audited).

---

## 8. App: constitutions

This is the heart of Legatio. A `Constitution` is the mutable container; a `ConstitutionVersion` is an immutable snapshot of rules.

### 8.1 Constitution

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `agent` | FK → Agent | on_delete CASCADE | |
| `name` | CharField | max 100 | E.g. "Travel Constitution" |
| `description` | TextField | null | |
| `status` | CharField | choices ConstitutionStatus, default DRAFT | |
| `active_version` | FK → ConstitutionVersion | null, on_delete SET_NULL | Currently enforced version |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |
| `deleted_at` | DateTimeField | null | Soft delete |

**Constraints:**

- `uniq_constitution_agent_name`: unique (`agent`, `name`) where `deleted_at IS NULL`.

**Business rule:** An agent may have multiple constitutions, but only **one** can have `status = ACTIVE` at a time (enforced at service layer + partial unique index).

**Partial unique index:**

```sql
CREATE UNIQUE INDEX uniq_constitution_active
ON legatio_constitutions_constitution (agent_id)
WHERE status = 'ACTIVE' AND deleted_at IS NULL;
```

### 8.2 ConstitutionVersion

Immutable snapshot. Once activated, **never modified**.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `constitution` | FK → Constitution | on_delete CASCADE | |
| `version_number` | PositiveIntegerField | | Sequential per constitution |
| `status` | CharField | choices ConstitutionStatus | DRAFT → ACTIVE → ARCHIVED |
| `rules_snapshot` | JSONField | | Full serialized rules for fast load |
| `created_by` | FK → User | on_delete PROTECT | |
| `activated_at` | DateTimeField | null | |
| `archived_at` | DateTimeField | null | |
| `created_at` | DateTimeField | auto_now_add | |

**Constraints:**

- `uniq_version_number`: unique (`constitution`, `version_number`).

**Immutability rule:** Once `status = ACTIVE` or `ARCHIVED`, no field may be modified. Edits create a new `ConstitutionVersion` with `version_number + 1`.

### 8.3 PolicyRule

Individual rule within a version. **Immutable** — belongs to a version, not to the mutable constitution.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `version` | FK → ConstitutionVersion | on_delete CASCADE | |
| `rule_number` | PositiveIntegerField | | Display: "Rule #17" |
| `name` | CharField | max 100 | E.g. "Never share phone" |
| `description` | TextField | null | Human-readable explanation |
| `category` | CharField | choices RuleCategory | |
| `field` | CharField | max 100 | E.g. "phone_number", "amount" |
| `operator` | CharField | choices RuleOperator | |
| `value` | JSONField | | Typed value (number, string, list) |
| `action` | CharField | choices RuleAction, default DENY | Fail-safe default |
| `priority` | PositiveIntegerField | default 100 | Lower = evaluated first |
| `is_active` | BooleanField | default True | |
| `created_at` | DateTimeField | auto_now_add | |

**Constraints:**

- `uniq_rule_number`: unique (`version`, `rule_number`).

**Indexes:**

- `idx_policyrule_version_priority` on (`version`, `priority`).

**Example rows:**

| rule_number | name | category | field | operator | value | action |
|-------------|------|----------|-------|----------|-------|--------|
| 1 | Max transaction | FINANCIAL | amount | LESS_THAN_OR_EQUAL | 700 | ALLOW |
| 17 | Never share phone | PRIVACY | phone_number | EQUALS | true | DENY |
| 23 | Large payments | FINANCIAL | amount | GREATER_THAN | 200 | REQUIRE_APPROVAL |

---

## 9. App: negotiations

### 9.1 NegotiationRoom

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `reference_code` | CharField | max 20, unique | E.g. "NEG-2026-000421" |
| `user_agent` | FK → Agent | on_delete PROTECT, related_name="user_negotiations" | |
| `external_agent` | FK → Agent | on_delete PROTECT, related_name="external_negotiations" | |
| `constitution_version` | FK → ConstitutionVersion | on_delete PROTECT | Version active at start |
| `title` | CharField | max 200 | E.g. "Hotel Madrid 5 nights" |
| `user_instruction` | TextField | | Original user request |
| `status` | CharField | choices NegotiationStatus, default PENDING | |
| `max_rounds` | PositiveIntegerField | default 10 | Anti-loop protection |
| `current_round` | PositiveIntegerField | default 0 | |
| `expires_at` | DateTimeField | null | TTL for the negotiation |
| `started_at` | DateTimeField | null | |
| `completed_at` | DateTimeField | null | |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |
| `deleted_at` | DateTimeField | null | Soft delete |

**Constraints:**

- `chk_negotiation_agents_differ`: CHECK (`user_agent_id != external_agent_id`).
- `chk_negotiation_rounds`: CHECK (`current_round <= max_rounds`).

**Indexes:**

- `idx_negotiation_user_agent` on `user_agent`.
- `idx_negotiation_status` on `status`.
- `idx_negotiation_created` on `created_at` DESC.

**State machine:**

```text
PENDING → IN_PROGRESS → AWAITING_APPROVAL → COMPLETED
                ↓               ↓
            CANCELLED       CANCELLED
                ↓
            FAILED / EXPIRED
```

### 9.2 NegotiationMessage

Append-only log of every message exchanged in the room.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `room` | FK → NegotiationRoom | on_delete CASCADE | |
| `sender` | FK → Agent | on_delete PROTECT | |
| `message_type` | CharField | choices: TEXT, PROPOSAL, COUNTERPROPOSAL, SYSTEM | |
| `content` | TextField | | Natural language content |
| `structured_payload` | JSONField | null | Parsed structure if applicable |
| `round_number` | PositiveIntegerField | | |
| `created_at` | DateTimeField | auto_now_add, db_index | |

**Indexes:**

- `idx_message_room_created` on (`room`, `created_at`).

---

## 10. App: proposals

### 10.1 Proposal

A structured offer from an agent.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `room` | FK → NegotiationRoom | on_delete CASCADE | |
| `sender` | FK → Agent | on_delete PROTECT | |
| `action_type` | CharField | max 50 | E.g. "purchase", "share_data", "subscribe" |
| `amount` | DecimalField | max_digits 12, decimal_places 2, null | |
| `currency` | CharField | max 3, null | ISO 4217 |
| `data_fields_requested` | JSONField | default list | E.g. ["phone_number"] |
| `contract_length_months` | PositiveIntegerField | null | |
| `auto_renewal` | BooleanField | default False | |
| `terms` | JSONField | default dict | Full structured terms |
| `status` | CharField | choices ProposalStatus, default RECEIVED | |
| `round_number` | PositiveIntegerField | | |
| `superseded_by` | FK → Proposal | null, on_delete SET_NULL | |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |

**Indexes:**

- `idx_proposal_room` on `room`.
- `idx_proposal_status` on `status`.

**`terms` schema example:**

```json
{
  "version": 1,
  "destination": "Madrid",
  "nights": 5,
  "cancellation_policy": "48h",
  "extras": ["breakfast"]
}
```

### 10.2 CounterProposal

Append-only record of a counter-offer generated in response to a proposal.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `proposal` | FK → Proposal | on_delete CASCADE | The proposal being countered |
| `sender` | FK → Agent | on_delete PROTECT | |
| `adjustments` | JSONField | | What changed vs. original |
| `reasoning` | TextField | null | LLM-generated explanation |
| `created_at` | DateTimeField | auto_now_add | |

### 10.3 PolicyDecision

**The most critical append-only entity.** Records every Policy Engine evaluation.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `proposal` | FK → Proposal | on_delete CASCADE | |
| `constitution_version` | FK → ConstitutionVersion | on_delete PROTECT | Version used for evaluation |
| `outcome` | CharField | choices PolicyDecisionOutcome | |
| `risk_level` | CharField | choices RiskLevel | |
| `reason` | TextField | | Human-readable explanation |
| `matched_rules` | JSONField | default list | Rule IDs + descriptions |
| `evaluation_duration_ms` | PositiveIntegerField | | Performance tracking |
| `engine_version` | CharField | max 20 | E.g. "1.0.0" |
| `created_at` | DateTimeField | auto_now_add | |

**Indexes:**

- `idx_policydecision_proposal` on `proposal`.
- `idx_policydecision_outcome` on `outcome`.

**`matched_rules` example:**

```json
[
  {
    "rule_id": "uuid-here",
    "rule_number": 17,
    "name": "Never share phone",
    "action": "DENY",
    "triggered_by": "data_fields_requested contains 'phone_number'"
  }
]
```

**Invariant:** Every `Proposal` that leaves `RECEIVED` status MUST have at least one `PolicyDecision` record. Enforced at service layer.

---

## 11. App: approvals

### 11.1 ApprovalRequest

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `proposal` | FK → Proposal | on_delete CASCADE | |
| `room` | FK → NegotiationRoom | on_delete CASCADE | Denormalized for fast queries |
| `requested_by` | FK → Agent | on_delete PROTECT | The user's agent |
| `policy_decision` | FK → PolicyDecision | on_delete PROTECT | Why approval is needed |
| `status` | CharField | choices ApprovalStatus, default PENDING | |
| `summary` | TextField | | Human-readable summary |
| `expires_at` | DateTimeField | | Default: +24h from creation |
| `created_at` | DateTimeField | auto_now_add | |
| `updated_at` | DateTimeField | auto_now | |

**Constraints:**

- `uniq_approval_proposal`: unique on `proposal` (one active request per proposal).

**Indexes:**

- `idx_approval_status_expires` on (`status`, `expires_at`).

### 11.2 ApprovalDecision

Append-only record of the human's decision.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `request` | FK → ApprovalRequest | on_delete CASCADE | |
| `decided_by` | FK → User | on_delete PROTECT | |
| `decision` | CharField | choices ApprovalStatus | APPROVED / REJECTED / MODIFIED |
| `modifications` | JSONField | null | If decision = MODIFIED |
| `comment` | TextField | null | Optional user comment |
| `created_at` | DateTimeField | auto_now_add | |

**Invariant:** An `ApprovalRequest` may have multiple `ApprovalDecision` records (e.g., expired then re-requested), but only one terminal decision.

---

## 12. App: agreements

### 12.1 Agreement

Immutable once signed.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `reference_code` | CharField | max 20, unique | E.g. "AGR-2026-000184" |
| `room` | OneToOne → NegotiationRoom | on_delete PROTECT | One agreement per room |
| `proposal` | FK → Proposal | on_delete PROTECT | The accepted proposal |
| `constitution_version` | FK → ConstitutionVersion | on_delete PROTECT | Version at signing time |
| `status` | CharField | choices AgreementStatus, default DRAFT | |
| `canonical_json` | JSONField | | The exact signed representation |
| `canonical_hash` | CharField | max 64, unique | SHA-256 of canonical JSON |
| `parties` | JSONField | | Agent IDs + roles |
| `terms_summary` | TextField | | Human-readable summary |
| `signed_at` | DateTimeField | null | |
| `executed_at` | DateTimeField | null | |
| `voided_at` | DateTimeField | null | |
| `created_at` | DateTimeField | auto_now_add | |

**Indexes:**

- `idx_agreement_hash` on `canonical_hash` (unique).
- `idx_agreement_status` on `status`.

**Canonical JSON rules:**

- Keys sorted alphabetically at every level.
- Numbers serialized as strings with fixed decimal places.
- Timestamps in ISO 8601 UTC.
- No whitespace outside strings.

**Example:**

```json
{
  "agreement_id": "AGR-2026-000184",
  "constitution_version": "uuid-here",
  "created_at": "2026-08-19T14:32:00Z",
  "negotiation_id": "uuid-here",
  "parties": [
    {"id": "uuid-user-agent", "role": "buyer"},
    {"id": "uuid-hotel-agent", "role": "seller"}
  ],
  "terms": {
    "amount": "700.00",
    "cancellation_policy": "48h",
    "currency": "EUR",
    "data_shared": [],
    "destination": "Madrid",
    "nights": 5
  }
}
```

### 12.2 AgreementSignature

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `agreement` | OneToOne → Agreement | on_delete CASCADE | |
| `signer` | FK → User | on_delete PROTECT | |
| `signature_algorithm` | CharField | max 20 | E.g. "HMAC-SHA256" (MVP) |
| `signature_value` | CharField | max 128 | |
| `signed_payload_hash` | CharField | max 64 | Must match `canonical_hash` |
| `ip_address` | GenericIPAddressField | null | |
| `user_agent_string` | CharField | max 255, null | |
| `created_at` | DateTimeField | auto_now_add | |

**Invariant:** `signed_payload_hash` MUST equal `agreement.canonical_hash`. Enforced at service layer before persistence.

---

## 13. App: audit

### 13.1 AuditEvent

**Append-only. Hash-chained. Never updated. Never deleted.**

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `sequence_number` | BigAutoField | unique | Global ordering |
| `event_type` | CharField | max 50, choices EventType | |
| `actor_type` | CharField | max 20, choices ActorType | |
| `actor_id` | UUIDField | null | Null for system events |
| `entity_type` | CharField | max 50 | E.g. "Proposal" |
| `entity_id` | UUIDField | | Generic reference |
| `room` | FK → NegotiationRoom | null, on_delete SET_NULL | For negotiation-scoped queries |
| `payload` | JSONField | | Event-specific data (encrypted if sensitive) |
| `payload_hash` | CharField | max 64 | SHA-256 of canonical payload |
| `previous_event_hash` | CharField | max 64, null | Null for genesis event |
| `event_hash` | CharField | max 64, unique | Chain hash |
| `correlation_id` | UUIDField | null | Request tracing |
| `created_at` | DateTimeField | auto_now_add, db_index | |

**Indexes:**

- `idx_audit_entity` on (`entity_type`, `entity_id`).
- `idx_audit_room_created` on (`room`, `created_at`).
- `idx_audit_event_type` on `event_type`.
- `idx_audit_actor` on (`actor_type`, `actor_id`).

**Hash computation:**

```python
event_hash = sha256(
    f"{sequence_number}|{created_at.isoformat()}|{event_type}|"
    f"{actor_type}|{actor_id}|{entity_type}|{entity_id}|"
    f"{previous_event_hash}|{payload_hash}"
).hexdigest()
```

**Invariants:**

- No `UPDATE` or `DELETE` operations, ever. Enforced via:
  - Database trigger (PostgreSQL) that raises on UPDATE/DELETE.
  - Django model override of `save()` and `delete()` that raises for existing instances.
- `previous_event_hash` of event N+1 MUST equal `event_hash` of event N.
- A Celery Beat job (`audit.verify_chain`) runs daily to verify integrity.

**Database trigger (PostgreSQL):**

```sql
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'AuditEvent records are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_no_update
BEFORE UPDATE ON legatio_audit_auditevent
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER audit_no_delete
BEFORE DELETE ON legatio_audit_auditevent
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
```

---

## 14. App: notifications

### 14.1 Notification

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUIDField | PK | |
| `user` | FK → User | on_delete CASCADE | |
| `channel` | CharField | choices NotificationChannel | |
| `event_type` | CharField | max 50 | Links to audit event type |
| `title` | CharField | max 200 | |
| `body` | TextField | | |
| `action_url` | CharField | max 500, null | Deep link |
| `related_entity_type` | CharField | max 50, null | |
| `related_entity_id` | UUIDField | null | |
| `status` | CharField | choices NotificationStatus, default PENDING | |
| `delivered_at` | DateTimeField | null | |
| `read_at` | DateTimeField | null | |
| `created_at` | DateTimeField | auto_now_add, db_index | |

**Indexes:**

- `idx_notification_user_status` on (`user`, `status`).
- `idx_notification_user_created` on (`user`, `created_at` DESC).

---

## 15. Indexing Strategy

### 15.1 Principles

- Index every foreign key used in JOINs.
- Index every field used in `WHERE` clauses on hot paths.
- Composite indexes ordered by selectivity (most selective first).
- Partial indexes for status-filtered queries (e.g., "active only").
- Review `EXPLAIN ANALYZE` monthly as data grows.

### 15.2 Hot Query Paths

| Query | Index Used |
|-------|-----------|
| Load active constitution for agent | `uniq_constitution_active` (partial) |
| Load rules for evaluation | `idx_policyrule_version_priority` |
| List pending approvals for user | `idx_approval_status_expires` + join |
| List user's negotiations | `idx_negotiation_user_agent` |
| Load audit trail for entity | `idx_audit_entity` |
| Verify hash chain | `sequence_number` (unique) |
| List user's unread notifications | `idx_notification_user_status` |

### 15.3 Partitioning (Future)

When `AuditEvent` exceeds ~10M rows, partition by month on `created_at`:

```sql
CREATE TABLE legatio_audit_auditevent (
    ...
) PARTITION BY RANGE (created_at);
```

This is explicitly **out of MVP scope** but the schema is designed to allow it without breaking changes.

---

## 16. Data Encryption

### 16.1 Encryption at Rest

| Data | Encryption | Method |
|------|-----------|--------|
| `User.totp_secret` | AES-256-GCM | django-cryptography |
| `Constitution.rules_snapshot` (if contains PII) | AES-256-GCM | django-cryptography |
| `AuditEvent.payload` (sensitive fields) | Field-level AES-256-GCM | django-cryptography |
| Full database | Disk-level encryption | Cloud provider (RDS/Cloud SQL) |

### 16.2 Encryption in Transit

- TLS 1.3 mandatory for all connections.
- Internal service-to-service communication over private network.

### 16.3 Key Management

- **MVP:** Encryption keys in environment variables, rotated quarterly.
- **Future:** AWS KMS or HashiCorp Vault with automatic rotation.

### 16.4 What Is Never Stored

- Credit card numbers.
- Passwords in plain text (always hashed via PBKDF2/argon2).
- Full API keys (only SHA-256 hashes).
- Raw LLM prompts containing PII (sanitized before logging).

---

## 17. Integrity Rules and Constraints

### 17.1 Referential Integrity

| Relationship | on_delete | Rationale |
|--------------|-----------|-----------|
| User → Agent | CASCADE | Agents belong to user |
| Agent → Constitution | CASCADE | Constitutions belong to agent |
| Constitution → ConstitutionVersion | CASCADE | Versions belong to constitution |
| ConstitutionVersion → PolicyRule | CASCADE | Rules belong to version |
| NegotiationRoom → ConstitutionVersion | PROTECT | Audit history must survive |
| Proposal → NegotiationRoom | CASCADE | Proposals belong to room |
| PolicyDecision → Proposal | CASCADE | Decisions belong to proposal |
| PolicyDecision → ConstitutionVersion | PROTECT | Audit history must survive |
| Agreement → NegotiationRoom | PROTECT | Agreements are permanent records |
| Agreement → ConstitutionVersion | PROTECT | Audit history must survive |
| ApprovalDecision → User | PROTECT | Audit history must survive |
| AuditEvent → NegotiationRoom | SET_NULL | Audit survives room deletion |

### 17.2 Business Invariants

1. **One active constitution per agent.** (Partial unique index.)
2. **ConstitutionVersion immutability.** (Service layer + no update API.)
3. **Every evaluated proposal has a PolicyDecision.** (Service layer.)
4. **ApprovalRequest requires PolicyDecision with outcome REQUIRE_HUMAN_APPROVAL.** (Service layer + DB check.)
5. **Agreement canonical_hash matches signature payload hash.** (Service layer.)
6. **AuditEvent hash chain continuity.** (Service layer + daily verification job.)
7. **NegotiationRoom agents must differ.** (CHECK constraint.)
8. **Current round never exceeds max rounds.** (CHECK constraint.)

### 17.3 Transaction Boundaries

The following operations MUST execute in a single database transaction:

- Proposal evaluation + PolicyDecision creation + AuditEvent creation.
- Approval decision + Proposal status update + Agreement creation (if approved) + AuditEvent.
- Agreement signing + AgreementSignature creation + AuditEvent.
- Constitution activation + previous version archival + AuditEvent.

---

## 18. Migration Strategy

### 18.1 Principles

- Every schema change goes through a Django migration.
- Migrations are reviewed in PRs like code.
- Destructive migrations (column drops, table drops) require two-phase deployment:
  1. Phase 1: Stop writing to the column.
  2. Phase 2: Drop the column in a later release.
- Data migrations are idempotent and reversible where possible.

### 18.2 Migration Naming

```text
0001_initial.py
0002_add_policy_decision.py
0003_backfill_audit_events.py
```

### 18.3 Pre-Deployment Checklist

- [ ] Migration tested against a copy of production data.
- [ ] Rollback migration written and tested.
- [ ] No full-table locks on tables > 1M rows (use `CREATE INDEX CONCURRENTLY`).
- [ ] Data migration batched for large tables.

---

## 19. Seed Data and Examples

### 19.1 Development Seed Script

`scripts/seed.sh` populates the development database with:

- 2 users (alice@example.com, bob@example.com).
- 3 agents (1 user agent, 1 simulated hotel agent, 1 simulated ISP agent).
- 1 active constitution with 5 rules (the "Madrid travel" scenario).
- 1 completed negotiation with full audit trail.

### 19.2 Example: Madrid Travel Constitution

```json
{
  "version": 1,
  "rules": [
    {
      "rule_number": 1,
      "name": "Max transaction amount",
      "category": "FINANCIAL",
      "field": "amount",
      "operator": "LESS_THAN_OR_EQUAL",
      "value": 700,
      "action": "ALLOW"
    },
    {
      "rule_number": 17,
      "name": "Never share phone number",
      "category": "PRIVACY",
      "field": "phone_number",
      "operator": "EQUALS",
      "value": true,
      "action": "DENY"
    },
    {
      "rule_number": 23,
      "name": "Large payments need approval",
      "category": "FINANCIAL",
      "field": "amount",
      "operator": "GREATER_THAN",
      "value": 200,
      "action": "REQUIRE_APPROVAL"
    }
  ]
}
```

### 19.3 Example: PolicyDecision Record

```json
{
  "id": "uuid-here",
  "proposal": "uuid-here",
  "constitution_version": "uuid-here",
  "outcome": "DENY",
  "risk_level": "CRITICAL",
  "reason": "Proposal requests phone_number, which is forbidden by Rule #17 (Never share phone number).",
  "matched_rules": [
    {
      "rule_id": "uuid-here",
      "rule_number": 17,
      "name": "Never share phone number",
      "action": "DENY",
      "triggered_by": "data_fields_requested contains 'phone_number'"
    }
  ],
  "evaluation_duration_ms": 12,
  "engine_version": "1.0.0",
  "created_at": "2026-08-19T14:32:00Z"
}
```

---

## 20. Data Retention and Privacy

### 20.1 Retention Policy

| Data | Retention | Rationale |
|------|-----------|-----------|
| Active user data | Account lifetime | |
| Soft-deleted entities | 30 days, then hard delete | Recovery window |
| AuditEvent | 7 years (configurable) | Legal/compliance |
| Notifications | 90 days | Low value after read |
| Failed login attempts | 30 days | Security monitoring |

### 20.2 GDPR Right to Be Forgotten

When a user requests account deletion:

1. **Anonymize** (not delete) `AuditEvent` records: replace `actor_id` with a random UUID, strip PII from `payload`. Rationale: audit integrity for other parties' records.
2. **Hard delete** `User`, `UserProfile`, `Agent`, `Constitution`, and related entities.
3. **Retain** `Agreement` records with anonymized user references (legal obligation for counterparty records).
4. Log the anonymization itself as a final `AuditEvent`.

This process runs as a Celery task with manual admin approval.

### 20.3 Data Minimization

- `NegotiationMessage.content` stores only what's necessary for the negotiation.
- PII in `AuditEvent.payload` is encrypted at the field level.
- Logs never contain raw PII (enforced by logging filters).

---

## 21. Future Schema Considerations

These entities are **NOT** in the MVP but are documented to ensure current schema decisions don't block them.

### 21.1 Organization (Enterprise, Phase 4+)

```text
Organization
├── members (User, with roles)
├── global_constitution
├── department_policies
└── agents
```

**Impact on current schema:** `Agent.owner` becomes nullable FK to either `User` or `Organization` (polymorphic). Designed with this in mind.

### 21.2 AgentReputation (Phase 5+)

```text
AgentReputation
├── agent (FK)
├── score
├── total_negotiations
├── successful_negotiations
├── disputes
└── updated_at
```

**Impact:** None on current schema. New app.

### 21.3 BlockchainAnchor (Phase 6+)

```text
BlockchainAnchor
├── agreement (FK)
├── chain (e.g., "polygon")
├── tx_hash
├── block_number
└── anchored_at
```

**Impact:** None. `Agreement.canonical_hash` is already designed to be anchorable.

### 21.4 A2A/MCP Integration Tables (Phase 4+)

```text
ExternalProtocolBinding
├── agent (FK)
├── protocol ("A2A" | "MCP" | "REST")
├── endpoint_config (JSONB)
└── status
```

**Impact:** None. `Agent.protocol_version` already预留 room.

---

## 22. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-19 | Architecture Team | Initial approved version. |

---
