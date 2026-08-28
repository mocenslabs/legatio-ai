# Legatio AI — Architecture Decision Record (ADR)

> **Version:** 1.0

> **Status:** Approved

> **Date:** August 19, 2026

> **Author:** Mauro Vicens

> **Repository:** `mocenslabs/legatio-ai`
> **Depends on:** `01-PRD.md` (v1.0)

---

## Table of Contents

1. [Document Purpose](#1-document-purpose)
2. [Architectural Principles](#2-architectural-principles)
3. [High-Level Architecture Overview](#3-high-level-architecture-overview)
4. [Architecture Decision Records (ADRs)](#4-architecture-decision-records-adrs)
5. [Technology Stack — Detailed Specification](#5-technology-stack--detailed-specification)
6. [Project Structure](#6-project-structure)
7. [Data Model Overview](#7-data-model-overview)
8. [Core Components Deep Dive](#8-core-components-deep-dive)
9. [API Design](#9-api-design)
10. [Real-Time Communication](#10-real-time-communication)
11. [Security Architecture](#11-security-architecture)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Code Conventions](#14-code-conventions)
15. [Performance Considerations](#15-performance-considerations)
16. [Monitoring and Observability](#16-monitoring-and-observability)
17. [Future Architectural Considerations](#17-future-architectural-considerations)
18. [Change History](#18-change-history)

---

## 1. Document Purpose

This document captures the **architectural decisions** made for Legatio AI. It serves as the technical "ground truth" for the project and must be consulted whenever:

- A developer needs to understand why a technology was chosen.
- A new feature is being planned and its architectural impact must be assessed.
- An AI assistant (or new team member) needs context about past decisions.
- A refactor or migration is being considered.

**This document is NOT:**

- A tutorial on Django or Vue.
- A replacement for code-level documentation.
- A final specification (it will evolve with ADR amendments).

**This document IS:**

- The authoritative reference for architectural decisions.
- A map of how the system is organized.
- A contract between the frontend, backend, and infrastructure teams.

---

## 2. Architectural Principles

These principles guide every architectural decision. If a decision conflicts with these principles, it must be explicitly justified via a new ADR.

### 2.1 Separation of Concerns: AI Proposes, Policy Decides

The single most important architectural principle of Legatio AI:

```text
LLM (Negotiation Engine)  →  Proposes actions
Policy Engine (Deterministic)  →  Decides ALLOW / DENY / REQUIRE_APPROVAL
Audit Service  →  Records everything
```

**Rule:** The LLM is NEVER allowed to make authorization decisions. Authorization is always deterministic, auditable, and explainable.

### 2.2 Determinism Where It Matters

Any component that affects:

- User authorization
- Financial limits
- Privacy rules
- Audit integrity

...MUST be deterministic (pure code, no LLM, no probabilistic behavior).

### 2.3 Auditability by Default

Every state change in the system MUST produce an `AuditEvent`. There are no "silent" operations. The audit trail is append-only and cryptographically chained.

### 2.4 Privacy First

User data (especially Constitutions) is encrypted at rest. Logs never contain raw PII. Data minimization is enforced at the schema level.

### 2.5 Fail-Safe Defaults

If any component fails (LLM, Redis, external agent), the system defaults to the most restrictive policy: `DENY` or `REQUIRE_HUMAN_APPROVAL`. Never `ALLOW` by default on failure.

### 2.6 Protocol Agnosticism

Legatio speaks its own internal protocol but is designed to be a gateway for external protocols (A2A, MCP, REST). The core logic must not be coupled to any specific external protocol.

### 2.7 MVP Pragmatism

No blockchain, no distributed consensus, no multi-region deployment in the MVP. Solve the real problem first, scale later.

---

## 3. High-Level Architecture Overview

### 3.1 System Context Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                         ACTORS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Human User   │    │ Developer    │    │ External     │      │
│  │ (via Browser)│    │ (via SDK)    │    │ Agent        │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
└─────────┼───────────────────┼───────────────────┼──────────────┘
          │                   │                   │
          │ HTTPS + WSS       │ REST API          │ REST/WebSocket
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LEGATIO AI PLATFORM                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API GATEWAY                            │  │
│  │  - Authentication (JWT + 2FA)                            │  │
│  │  - Rate limiting                                         │  │
│  │  - Request validation                                    │  │
│  │  - WebSocket handler                                     │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │                    CORE SERVICES                          │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Constitution │  │   Policy     │  │ Negotiation  │   │  │
│  │  │   Service    │  │   Engine     │  │   Service    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │    Audit     │  │  Agreement   │  │ Notification │   │  │
│  │  │   Service    │  │   Service    │  │   Service    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │                   INFRASTRUCTURE                          │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ PostgreSQL   │  │    Redis     │  │   Celery     │   │  │
│  │  │  (Primary)   │  │  (Cache/Q)   │  │  (Workers)   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐                     │  │
│  │  │ Object Store │  │  LLM APIs    │                     │  │
│  │  │   (S3/Minio) │  │ (OpenAI, etc)│                     │  │
│  │  └──────────────┘  └──────────────┘                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

| Component | Responsibility | Deterministic? |
|-----------|---------------|----------------|
| API Gateway | Authentication, routing, rate limiting | Yes |
| Constitution Service | CRUD of user rules, versioning | Yes |
| Policy Engine | Evaluate proposals against rules | **Yes (critical)** |
| Negotiation Service | Manage rooms, messages, LLM calls | No (uses LLM) |
| Audit Service | Append-only event log, hashing | Yes |
| Agreement Service | Generate canonical agreements, signatures | Yes |
| Notification Service | Push, email, WebSocket dispatch | Yes |
| PostgreSQL | Source of truth, ACID transactions | Yes |
| Redis | Cache, queues, ephemeral state | Yes |
| Celery | Async task execution | Yes |

---

## 4. Architecture Decision Records (ADRs)

Each significant architectural decision is recorded as an ADR. These are immutable once approved; changes require a new ADR that supersedes the old one.

### ADR-001: Use Django as the Backend Framework

- **Status:** Approved
- **Context:** We need a mature, secure, batteries-included framework for a system with complex relational data, strong security requirements, and real-time capabilities.
- **Decision:** Use Django 5.x with Django REST Framework and Django Channels.
- **Alternatives considered:**
  - FastAPI: Excellent for async, but weaker ORM and admin.
  - NestJS: Good TypeScript ecosystem, but less mature ORM.
  - Rails: Similar to Django, but smaller Python AI ecosystem integration.
- **Consequences:**
  - ✅ Rapid development with built-in admin, auth, ORM.
  - ✅ Excellent security defaults.
  - ✅ Rich ecosystem (DRF, Channels, Celery).
  - ⚠️ Django's synchronous-by-default nature requires careful async handling via Channels.

### ADR-002: Use Vue 3 as the Frontend Framework

- **Status:** Approved
- **Context:** We need a reactive frontend framework for a complex dashboard with real-time updates, form builders, and data visualization.
- **Decision:** Use Vue 3 with Composition API, Pinia, and TanStack Query.
- **Alternatives considered:**
  - React: Larger ecosystem, but more boilerplate for this use case.
  - Svelte: Smaller bundle, but smaller ecosystem for enterprise dashboards.
  - Angular: Too heavy for our needs.
- **Consequences:**
  - ✅ Composition API enables reusable logic.
  - ✅ Excellent TypeScript support.
  - ✅ Moderate learning curve.
  - ⚠️ Smaller talent pool than React (acceptable for our team size).

### ADR-003: Deterministic Policy Engine (No LLM for Authorization)

- **Status:** Approved
- **Context:** Authorization decisions must be 100% predictable, auditable, and explainable.
- **Decision:** The Policy Engine is a pure Python module that evaluates proposals against rules. It NEVER uses an LLM.
- **Alternatives considered:**
  - LLM-based authorization: Rejected due to non-determinism and hallucination risk.
  - Hybrid (LLM + rules): Rejected for MVP; adds complexity without clear benefit.
- **Consequences:**
  - ✅ 100% testable and predictable.
  - ✅ Easy to explain to users ("Rule #17 blocked this").
  - ✅ No LLM cost for authorization.
  - ⚠️ Rules must be explicitly defined; no "fuzzy" authorization.

### ADR-004: No Blockchain in MVP

- **Status:** Approved
- **Context:** The original vision included blockchain anchoring for agreements.
- **Decision:** Use SHA-256 hashing + digital signatures + PostgreSQL audit trail. No blockchain in MVP.
- **Alternatives considered:**
  - Ethereum L2: Rejected due to cost, complexity, and UX friction.
  - Private blockchain: Rejected due to operational overhead.
- **Consequences:**
  - ✅ Fast to implement.
  - ✅ No external dependencies.
  - ✅ Sufficient integrity for MVP.
  - ⚠️ Not "trustless" in the cryptographic sense; relies on PostgreSQL integrity.
  - 📌 Future: Can add L2 anchoring in Phase 6+ if needed.

### ADR-005: PostgreSQL as Primary Database

- **Status:** Approved
- **Context:** The domain is highly relational (Users → Constitutions → Policies → Negotiations → Proposals → Decisions → Agreements → AuditEvents).
- **Decision:** Use PostgreSQL 16 as the single source of truth.
- **Alternatives considered:**
  - MongoDB: Rejected due to need for ACID transactions and complex joins.
  - MySQL: Rejected due to weaker JSON support and extensions.
- **Consequences:**
  - ✅ ACID transactions for audit integrity.
  - ✅ JSONB for semi-structured data (Constitutions, proposals).
  - ✅ pgcrypto for encryption.
  - ✅ pgvector available for future embeddings.

### ADR-006: Celery + Redis for Async Processing

- **Status:** Approved
- **Context:** LLM calls, audit processing, and notifications must not block the main request cycle.
- **Decision:** Use Celery with Redis as the broker.
- **Alternatives considered:**
  - Django-Q: Simpler but less feature-rich.
  - RQ: Lighter but less mature.
  - AWS SQS: Adds cloud dependency.
- **Consequences:**
  - ✅ Mature, proven, well-documented.
  - ✅ Retry logic, scheduling (Celery Beat), monitoring.
  - ⚠️ Requires Redis infrastructure.

### ADR-007: WebSockets via Django Channels

- **Status:** Approved
- **Context:** Real-time notifications for negotiation updates and approval requests.
- **Decision:** Use Django Channels with Daphne/Uvicorn as the ASGI server.
- **Alternatives considered:**
  - Socket.IO: Requires separate server; less Django-native.
  - Server-Sent Events (SSE): Simpler but unidirectional.
  - Polling: Rejected due to latency and resource waste.
- **Consequences:**
  - ✅ Native Django integration.
  - ✅ Bidirectional communication.
  - ⚠️ Requires ASGI deployment (not WSGI).

### ADR-008: External LLM APIs (Not Self-Hosted) for MVP

- **Status:** Approved
- **Context:** The Negotiation Engine requires high-quality LLM capabilities.
- **Decision:** Use OpenAI GPT-4o and Anthropic Claude 3.5 Sonnet via API.
- **Alternatives considered:**
  - Self-hosted Llama 3.1 70B: Rejected for MVP due to GPU cost and ops overhead.
  - Smaller models (Mistral 7B): Rejected due to quality concerns for negotiation.
- **Consequences:**
  - ✅ Best quality for negotiation.
  - ✅ No GPU infrastructure.
  - ⚠️ Variable cost per negotiation.
  - ⚠️ Data leaves our infrastructure (mitigated by not sending PII).
  - 📌 Future: Consider self-hosted for privacy-sensitive deployments.

### ADR-009: Monolithic Backend with Modular Apps (Not Microservices)

- **Status:** Approved
- **Context:** Team size is small (1–3 developers). Microservices would add operational overhead.
- **Decision:** Use a Django monolith with clearly separated apps (modules). Each app has its own models, views, and services.
- **Alternatives considered:**
  - Microservices: Rejected due to ops complexity.
  - Serverless: Rejected due to cold starts and WebSocket limitations.
- **Consequences:**
  - ✅ Simple deployment.
  - ✅ Easy to test and debug.
  - ✅ Can extract services later if needed.
  - ⚠️ Single deployment unit; scaling requires vertical scaling or replication.

### ADR-010: API Versioning via URL Path

- **Status:** Approved
- **Context:** We need a clear API versioning strategy.
- **Decision:** Use URL path versioning: `/api/v1/...`, `/api/v2/...`.
- **Alternatives considered:**
  - Header versioning: Rejected due to poor discoverability.
  - Query param versioning: Rejected due to caching issues.
- **Consequences:**
  - ✅ Clear and explicit.
  - ✅ Easy to document and cache.
  - ⚠️ URL changes between versions.

---

## 5. Technology Stack — Detailed Specification

### 5.1 Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Runtime |
| Django | 5.0+ | Web framework |
| Django REST Framework | 3.14+ | REST APIs |
| Django Channels | 4.0+ | WebSockets |
| Django Allauth | 0.60+ | Authentication (email, social, 2FA) |
| Application-level encryption | Phase 0 foundation; implementation defined before sensitive data is persisted | Encryption at rest |
| Celery | 5.3+ | Async task queue |
| Redis | 7.0+ | Cache, broker, rate limiting |
| PostgreSQL | 16+ | Primary database |
| Pydantic | 2.5+ | Data validation |
| pytest | 7.4+ | Testing framework |
| pytest-django | 4.7+ | Django test integration |
| ruff | 0.1+ | Linting and formatting |
| mypy | 1.8+ | Type checking |
| uvicorn | 0.27+ | ASGI server |
| daphne | 4.0+ | ASGI server (WebSocket) |

### 5.2 Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 20+ | Runtime |
| Vue | 3.4+ | UI framework |
| Pinia | 2.1+ | State management |
| Vue Router | 4.2+ | Routing |
| TanStack Query | 5.0+ | Server state management |
| TypeScript | 5.3+ | Type safety |
| Vite | 5.0+ | Build tool |
| Tailwind CSS | 3.4+ | Utility-first CSS |
| shadcn-vue | 0.1+ | UI component library |
| Socket.io-client | 4.7+ | WebSocket client |
| Chart.js | 4.4+ | Data visualization |
| Vue Flow | 1.3+ | Graph/flow visualization |
| Vitest | 1.0+ | Unit testing |
| Vue Test Utils | 2.4+ | Component testing |
| Playwright | 1.40+ | E2E testing |

### 5.3 Infrastructure Stack

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Local development |
| Nginx | Reverse proxy (production) |
| Cloudflare | CDN, DDoS protection, SSL |
| Sentry | Error tracking |
| Prometheus + Grafana | Metrics |
| GitHub Actions | CI/CD |

### 5.4 External Services

| Service | Purpose | Fallback |
|---------|---------|----------|
| OpenAI API (GPT-4o) | Negotiation Engine | Anthropic Claude |
| Anthropic API (Claude 3.5) | Negotiation Engine fallback | OpenAI |
| SendGrid (future) | Transactional email | Mailgun |
| Stripe (future) | Subscription billing | — |

---

## 6. Project Structure

### 6.1 Repository Layout

```text
legatio/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── docs/
│   ├── 00-INDEX.md
│   ├── 01-PRD.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-DATA-MODEL.md
│   ├── 04-BUSINESS-FLOW.md
│   ├── 05-ROADMAP.md
│   └── decisions/
│       └── ADR-*.md
├── backend/
│   ├── legatio/                  # Django project
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/             # User management
│   │   ├── agents/               # Agent identities
│   │   ├── constitutions/        # Constitution CRUD
│   │   ├── policies/             # Policy rules
│   │   ├── negotiations/         # Negotiation rooms
│   │   ├── proposals/            # Proposals & counter-proposals
│   │   ├── approvals/            # Human approval workflow
│   │   ├── agreements/           # Agreement generation
│   │   ├── audit/                # Audit trail
│   │   └── notifications/        # Push, email, WebSocket
│   ├── services/
│   │   ├── policy_engine/        # Deterministic policy evaluator
│   │   ├── negotiation_engine/   # LLM-based negotiation
│   │   ├── audit_service/        # Audit event creation
│   │   └── agreement_service/    # Agreement generation & signing
│   ├── core/
│   │   ├── exceptions.py
│   │   ├── permissions.py
│   │   ├── pagination.py
│   │   └── middleware.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                  # API client (TanStack Query)
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── ui/               # shadcn-vue components
│   │   │   ├── constitution/
│   │   │   ├── negotiation/
│   │   │   └── approval/
│   │   ├── composables/          # Reusable logic
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── router/
│   │   ├── stores/               # Pinia stores
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   ├── tests/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── terraform/                # Future: IaC
├── scripts/
│   ├── setup.sh
│   └── seed.sh
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

### 6.2 Django Apps Responsibility Matrix

| App | Models | Key Responsibility |
|-----|--------|-------------------|
| `accounts` | User, UserProfile | Authentication, 2FA, profile |
| `agents` | Agent, AgentIdentity, Credential | Agent registration, identity |
| `constitutions` | Constitution, ConstitutionVersion | Rule definitions, versioning |
| `policies` | PolicyRule | Individual rules within a Constitution |
| `negotiations` | NegotiationRoom, NegotiationMessage | Room lifecycle, message history |
| `proposals` | Proposal, CounterProposal | Structured offers |
| `approvals` | ApprovalRequest, ApprovalDecision | Human-in-the-loop workflow |
| `agreements` | Agreement, AgreementSignature | Final agreement records |
| `audit` | AuditEvent | Append-only event log |
| `notifications` | Notification, NotificationChannel | Multi-channel notifications |

---

## 7. Data Model Overview

> **Note:** A full data model specification is in `03-DATA-MODEL.md`. This section provides a high-level overview.

### 7.1 Core Entities

```text
User (1) ──< (N) Agent
  │
  └──< (N) Constitution (versioned)
         │
         └──< (N) PolicyRule

Agent (1) ──< (N) NegotiationRoom
                  │
                  ├──< (N) NegotiationMessage
                  │
                  ├──< (N) Proposal
                  │      │
                  │      └──< (N) CounterProposal
                  │
                  ├──< (N) ApprovalRequest
                  │      │
                  │      └──< (N) ApprovalDecision
                  │
                  └──< (0..1) Agreement
                         │
                         └──< (1) AgreementSignature

AuditEvent (append-only, references any entity via generic relation)
```

### 7.2 Key Design Decisions

- **Constitutions are versioned.** Every change creates a new version. Negotiations reference the specific Constitution version active at the time.
- **AuditEvents are append-only.** Never updated or deleted. Cryptographically chained via `previous_event_hash`.
- **Agreements are canonical JSON.** The exact JSON representation is hashed and signed. Any modification invalidates the signature.
- **PolicyRules are typed.** Each rule has a `rule_type` (financial, privacy, negotiation, custom) and a `condition` (JSON).

---

## 8. Core Components Deep Dive

### 8.1 Policy Engine

The Policy Engine is the heart of Legatio AI. It is a **pure Python module** with no external dependencies beyond the Constitution data.

**Input:**

```python
@dataclass
class ProposedAction:
    action_type: str              # e.g., "purchase", "share_data"
    amount: Optional[Decimal]
    currency: Optional[str]
    data_fields: List[str]        # e.g., ["phone_number", "email"]
    contract_length_months: Optional[int]
    auto_renewal: bool
    metadata: Dict[str, Any]
```

**Output:**

```python
@dataclass
class PolicyDecision:
    decision: Literal["ALLOW", "DENY", "REQUIRE_HUMAN_APPROVAL"]
    reason: str
    matched_rules: List[str]      # e.g., ["Rule #17: phone_number = NEVER"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    timestamp: datetime
```

**Evaluation Algorithm:**

```text
1. Load active Constitution for the user/agent
2. For each rule in Constitution:
   a. Evaluate rule condition against ProposedAction
   b. If rule matches:
      - If rule.action = "DENY" → return DENY immediately
      - If rule.action = "REQUIRE_APPROVAL" → mark for approval
3. If no DENY triggered and no approval required → return ALLOW
4. If approval required → return REQUIRE_HUMAN_APPROVAL
```

**Critical Properties:**

- **Deterministic:** Same input + same Constitution = same output, always.
- **Fast:** Evaluation must complete in < 50ms.
- **Testable:** 100% unit test coverage required.
- **Explainable:** Every decision includes the exact rules that triggered it.

### 8.2 Negotiation Engine

The Negotiation Engine uses LLMs to understand proposals, generate counter-offers, and summarize agreements. It is **strictly separated** from the Policy Engine.

**Responsibilities:**

- Parse natural language proposals into structured `Proposal` objects.
- Generate context-aware counter-offers.
- Summarize negotiation state for human review.
- Detect negotiation anomalies (e.g., circular offers).

**LLM Usage:**

```text
User receives proposal → Negotiation Engine (LLM) parses it
                              ↓
                     Structured Proposal
                              ↓
                     Policy Engine evaluates
                              ↓
                     Decision (ALLOW/DENY/APPROVAL)
                              ↓
                     If DENY → Negotiation Engine (LLM) generates counter-offer
```

**Prompt Isolation:**

- LLM prompts NEVER include authorization logic.
- LLM output is ALWAYS validated by the Policy Engine before execution.
- LLM calls are sandboxed; they cannot modify state directly.

### 8.3 Audit Service

The Audit Service is responsible for recording every state change in the system.

**AuditEvent Schema:**

```python
class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=50)  # e.g., "proposal.created"
    actor_type = models.CharField(max_length=20)  # "user", "agent", "system"
    actor_id = models.UUIDField()
    entity_type = models.CharField(max_length=50)  # e.g., "Proposal"
    entity_id = models.UUIDField()
    previous_event_hash = models.CharField(max_length=64, null=True)
    event_hash = models.CharField(max_length=64)  # SHA-256
    payload_hash = models.CharField(max_length=64)
    payload = models.JSONField()  # Encrypted if sensitive
    metadata = models.JSONField(default=dict)
```

**Hash Chain:**

```text
event_hash = SHA256(
    timestamp +
    event_type +
    actor_id +
    entity_id +
    previous_event_hash +
    payload_hash
)
```

This creates a tamper-evident chain. If any event is modified, all subsequent hashes become invalid.

### 8.4 Agreement Service

When a negotiation reaches consensus, the Agreement Service generates a canonical agreement record.

**Process:**

```text
1. Collect all accepted terms from NegotiationRoom
2. Generate canonical JSON (sorted keys, normalized values)
3. Compute SHA-256 hash of canonical JSON
4. Sign hash with user's private key (or HMAC with server key for MVP)
5. Store Agreement + AgreementSignature
6. Create AuditEvent for agreement creation
7. Notify user for final approval
```

**Canonical JSON Example:**

```json
{
  "agreement_id": "AGR-2026-000184",
  "negotiation_id": "NEG-2026-000421",
  "parties": ["user-agent-42", "hotel-agent-17"],
  "terms": {
    "destination": "Madrid",
    "nights": 5,
    "price": {"amount": "700.00", "currency": "EUR"},
    "cancellation": "48h",
    "data_shared": []
  },
  "constitution_version": "CON-v3",
  "created_at": "2026-08-19T14:32:00Z"
}
```

---

## 9. API Design

### 9.1 API Conventions

- **Base URL:** `/api/v1/`
- **Format:** JSON
- **Authentication:** JWT Bearer token (via `Authorization: Bearer <token>`)
- **Pagination:** Cursor-based for large collections, offset for small ones
- **Error format:**

```json
{
  "error": {
    "code": "POLICY_DENIED",
    "message": "Action blocked by Constitution rule",
    "details": {
      "rule_id": "rule_17",
      "rule_description": "phone_number = NEVER"
    }
  }
}
```

### 9.2 Core Endpoints

**Authentication:**

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/2fa/enable
POST   /api/v1/auth/2fa/verify
```

**Agents:**

```text
GET    /api/v1/agents/
POST   /api/v1/agents/
GET    /api/v1/agents/{id}/
PATCH  /api/v1/agents/{id}/
DELETE /api/v1/agents/{id}/
```

**Constitutions:**

```text
GET    /api/v1/constitutions/
POST   /api/v1/constitutions/
GET    /api/v1/constitutions/{id}/
PATCH  /api/v1/constitutions/{id}/
POST   /api/v1/constitutions/{id}/activate
GET    /api/v1/constitutions/{id}/versions
```

**Policy Rules:**

```text
GET    /api/v1/constitutions/{id}/rules/
POST   /api/v1/constitutions/{id}/rules/
PATCH  /api/v1/rules/{id}/
DELETE /api/v1/rules/{id}/
POST   /api/v1/rules/{id}/evaluate    # Test a rule against a proposal
```

**Negotiations:**

```text
GET    /api/v1/negotiations/
POST   /api/v1/negotiations/
GET    /api/v1/negotiations/{id}/
POST   /api/v1/negotiations/{id}/messages
GET    /api/v1/negotiations/{id}/messages
POST   /api/v1/negotiations/{id}/cancel
```

**Proposals:**

```text
POST   /api/v1/proposals/
GET    /api/v1/proposals/{id}/
POST   /api/v1/proposals/{id}/counter
GET    /api/v1/proposals/{id}/policy-decision
```

**Approvals:**

```text
GET    /api/v1/approvals/pending
GET    /api/v1/approvals/{id}/
POST   /api/v1/approvals/{id}/approve
POST   /api/v1/approvals/{id}/reject
POST   /api/v1/approvals/{id}/modify
```

**Agreements:**

```text
GET    /api/v1/agreements/
GET    /api/v1/agreements/{id}/
GET    /api/v1/agreements/{id}/canonical
GET    /api/v1/agreements/{id}/signature
POST   /api/v1/agreements/{id}/export   # JSON, CSV, PDF
```

**Audit:**

```text
GET    /api/v1/audit/events
GET    /api/v1/audit/events/{id}/
GET    /api/v1/audit/entities/{entity_type}/{entity_id}/
POST   /api/v1/audit/verify             # Verify hash chain integrity
```

### 9.3 External Agent API

External agents connect via a dedicated API:

```text
POST   /api/v1/external/agents/register
POST   /api/v1/external/negotiations/{id}/propose
GET    /api/v1/external/negotiations/{id}/status
POST   /api/v1/external/negotiations/{id}/accept
POST   /api/v1/external/negotiations/{id}/reject
```

Authentication: API key + signature (HMAC-SHA256).

---

## 10. Real-Time Communication

### 10.1 WebSocket Architecture

**Connection lifecycle:**

```text
Client connects → wss://api.legatio.ai/ws/?token=<jwt>
       ↓
Django Channels authenticates JWT
       ↓
Client joins rooms:
  - user-{user_id}            (personal notifications)
  - negotiation-{neg_id}      (negotiation updates)
  - approval-{user_id}        (approval requests)
```

### 10.2 Event Types

```text
# Negotiation events
negotiation.started
negotiation.updated
negotiation.completed
negotiation.cancelled

# Proposal events
proposal.created
proposal.evaluated
counterproposal.created

# Approval events
approval.required
approval.approved
approval.rejected
approval.expired

# Agreement events
agreement.created
agreement.signed
agreement.executed

# System events
system.error
system.maintenance
```

### 10.3 Message Format

```json
{
  "type": "approval.required",
  "payload": {
    "approval_id": "apr_abc123",
    "negotiation_id": "neg_xyz789",
    "summary": "Your agent negotiated a €700 hotel stay. Exceeds auto-approve limit of €200.",
    "risk_level": "LOW",
    "expires_at": "2026-08-20T14:32:00Z"
  },
  "timestamp": "2026-08-19T14:32:00Z"
}
```

### 10.4 Reconnection Strategy

- Client uses exponential backoff (1s, 2s, 4s, 8s, max 30s).
- On reconnect, client requests missed events via `GET /api/v1/audit/events?since=<timestamp>`.
- Server maintains a short-lived event buffer in Redis (5 minutes).

---

## 11. Security Architecture

### 11.1 Authentication

- **JWT access tokens:** Short-lived (15 minutes).
- **JWT refresh tokens:** Long-lived (7 days), stored in httpOnly cookie.
- **2FA:** TOTP (RFC 6238) required for sensitive actions.
- **API keys:** For external agents, HMAC-signed requests.

### 11.2 Authorization

- **RBAC (Role-Based Access Control):** User, Admin, Agent.
- **Object-level permissions:** Users can only access their own resources.
- **Policy Engine enforcement:** Every action goes through policy evaluation.

### 11.3 Data Protection

- **Encryption at rest:** Constitution data encrypted with AES-256-GCM via `django-cryptography`.
- **Encryption in transit:** TLS 1.3 mandatory.
- **PII minimization:** Logs never contain raw PII. Phone numbers, emails, etc. are masked.
- **Key management:** Encryption keys stored in environment variables (future: AWS KMS, Vault).

### 11.4 Input Validation

- **Pydantic schemas** for all API inputs.
- **Django ORM** prevents SQL injection.
- **DRF throttling** prevents abuse.
- **CSP headers** prevent XSS.
- **CSRF tokens** for all state-changing requests.

### 11.5 Audit Integrity

- **Append-only audit log.** No UPDATE or DELETE on AuditEvent.
- **Hash chaining.** Each event references the previous event's hash.
- **Periodic integrity checks.** Celery Beat job verifies hash chain daily.
- **Export capability.** Users can export their full audit trail.

### 11.6 Threat Model

| Threat | Mitigation |
|--------|-----------|
| Prompt injection between agents | Sandbox isolation; Policy Engine blocks forbidden actions regardless of LLM output |
| JWT theft | Short-lived tokens; refresh token rotation; 2FA for sensitive actions |
| Database breach | Encryption at rest; minimal PII storage; regular backups |
| DDoS | Cloudflare; rate limiting per user and per IP |
| Malicious external agent | API key authentication; reputation system (future); sandbox isolation |
| LLM hallucination | Policy Engine validates all actions; LLM cannot bypass rules |
| Insider threat | Audit trail for all admin actions; role separation |

---

## 12. Testing Strategy

### 12.1 Testing Pyramid

```text
        ╱╲
       ╱  ╲       E2E Tests (Playwright)
      ╱    ╲      ~10 critical flows
     ╱──────╲
    ╱        ╲    Integration Tests (pytest-django)
   ╱          ╲   ~100 API + service tests
  ╱────────────╲
 ╱              ╲ Unit Tests (pytest)
╱                ╲ ~500+ tests, focus on Policy Engine
╱──────────────────╲
```

### 12.2 Test Categories

**Unit Tests:**

- Policy Engine: 100% coverage required.
- Services: All business logic.
- Utils: Hashing, canonicalization, etc.

**Integration Tests:**

- API endpoints: Request/response validation.
- Database: Transaction behavior.
- Celery tasks: Async processing.

**E2E Tests:**

- User registration → Constitution creation → Negotiation → Approval.
- External agent integration flow.
- WebSocket real-time updates.

### 12.3 Test Data

- **Factories** (via `factory_boy`) for all models.
- **Fixtures** for common scenarios (e.g., "hotel negotiation").
- **Seeds** for development environment.

### 12.4 CI Pipeline

```text
push → lint (ruff, mypy) + format (ruff)
     → unit tests
     → integration tests
     → build Docker images
     → (on main) → E2E tests
     → (on main) → deploy to staging
```

---

## 13. Deployment Architecture

### 13.1 Development Environment

```text
docker-compose up → spins up:
  - Django (with hot reload)
  - Vue (with Vite HMR)
  - PostgreSQL
  - Redis
  - Celery worker
  - Celery beat
```

### 13.2 Production Architecture (Target)

```text
                    ┌──────────────┐
                    │  Cloudflare  │
                    │  (CDN + WAF) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    Nginx     │
                    │ (Reverse Proxy)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼────┐ ┌─────▼─────┐
       │ Django ASGI │ │ Vue   │ │ WebSocket │
       │ (Uvicorn)   │ │ Static│ │ (Daphne)  │
       └──────┬──────┘ └───────┘ └─────┬─────┘
              │                         │
              └────────────┬────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼────┐ ┌─────▼─────┐
       │ PostgreSQL  │ │ Redis │ │  Celery   │
       │ (Managed)   │ │(Managed)│ │  Workers  │
       └─────────────┘ └───────┘ └───────────┘
```

### 13.3 Environment Strategy

| Environment | Purpose | URL |
|-------------|---------|-----|
| `local` | Developer machines | `localhost:8000` |
| `development` | Shared dev environment | `dev.legatio.ai` |
| `staging` | Pre-production testing | `staging.legatio.ai` |
| `production` | Live system | `legatio.ai` |

### 13.4 CI/CD Pipeline

```text
GitHub push
    ↓
GitHub Actions
    ↓
Lint + Test + Build
    ↓
Docker images pushed to registry
    ↓
Deploy to staging (automatic)
    ↓
E2E tests on staging
    ↓
Manual approval
    ↓
Deploy to production (blue/green)
```

---

## 14. Code Conventions

### 14.1 Python (Backend)

- **Style:** PEP 8, enforced by `ruff check` and `ruff format`.
- **Type hints:** Mandatory for all function signatures.
- **Docstrings:** Google-style for all public functions.
- **Imports:** Absolute imports; grouped (stdlib, third-party, local).
- **Naming:**
  - `snake_case` for functions, variables, modules.
  - `PascalCase` for classes.
  - `UPPER_CASE` for constants.

**Example:**

```python
def evaluate_policy(
    action: ProposedAction,
    constitution: Constitution,
) -> PolicyDecision:
    """Evaluate a proposed action against a constitution.

    Args:
        action: The proposed action to evaluate.
        constitution: The active constitution for the user.

    Returns:
        A PolicyDecision indicating ALLOW, DENY, or REQUIRE_HUMAN_APPROVAL.

    Raises:
        ConstitutionNotFoundError: If the constitution does not exist.
    """
    ...
```

### 14.2 TypeScript (Frontend)

- **Style:** Enforced by ESLint + Prettier.
- **TypeScript:** Strict mode enabled. No `any`.
- **Components:** Composition API with `<script setup>`.
- **Naming:**
  - `PascalCase` for components.
  - `camelCase` for functions, variables.
  - `kebab-case` for file names.

**Example:**

```typescript
// composables/useNegotiation.ts
export function useNegotiation(negotiationId: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['negotiation', negotiationId],
    queryFn: () => api.getNegotiation(negotiationId),
  });

  return { negotiation: data, isLoading, error };
}
```

### 14.3 Git Conventions

- **Branch naming:** `feature/leg-123-add-policy-engine`, `bugfix/leg-456-fix-hash`, `hotfix/leg-789-security`.
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- **PR process:**
  - 1 approval required.
  - All CI checks must pass.
  - Squash and merge.

---

## 15. Performance Considerations

### 15.1 Performance Targets

| Metric | Target |
|--------|--------|
| API response time (p95) | < 200ms |
| WebSocket latency | < 100ms |
| Policy Engine evaluation | < 50ms |
| Database query time (p95) | < 100ms |
| LLM call latency | < 5s (async) |
| Page load time | < 2s |

### 15.2 Optimization Strategies

**Backend:**

- **Database indexing:** Indexes on foreign keys, timestamps, and frequent query fields.
- **Query optimization:** Use `select_related` and `prefetch_related` to avoid N+1 queries.
- **Caching:** Redis cache for Constitutions, agent identities, rate limiting.
- **Async processing:** Celery for LLM calls, audit processing, notifications.
- **Pagination:** Cursor-based for large collections.

**Frontend:**

- **Code splitting:** Lazy load routes and heavy components.
- **Image optimization:** WebP, lazy loading.
- **Bundle size:** Tree shaking, minification.
- **State management:** TanStack Query for server state caching.

**Database:**

- **Connection pooling:** Via `django-db-geventpool` or managed service.
- **Read replicas:** For read-heavy workloads (future).
- **Partitioning:** Audit logs partitioned by month (future).

### 15.3 Load Testing

- **Tool:** Locust or k6.
- **Targets:**
  - 100 concurrent negotiations.
  - 1000 registered users.
  - 1M audit events without degradation.

---

## 16. Monitoring and Observability

### 16.1 Logging

- **Structured logging:** JSON format via `python-json-logger`.
- **Log levels:** DEBUG (dev), INFO (prod), WARNING/ERROR for issues.
- **Correlation IDs:** Every request gets a unique ID propagated through logs.
- **PII masking:** Sensitive data masked before logging.

### 16.2 Metrics

- **Prometheus metrics:**
  - Request rate, latency, error rate.
  - Policy Engine evaluation time.
  - LLM call latency and cost.
  - WebSocket connections.
  - Celery task queue length.
- **Grafana dashboards:**
  - System health.
  - API performance.
  - Business metrics (negotiations, approvals).

### 16.3 Error Tracking

- **Sentry:** Captures exceptions, performance issues.
- **Alerts:** Critical errors trigger Slack/email notifications.

### 16.4 Tracing (Future)

- **OpenTelemetry:** Distributed tracing across services.
- **Jaeger or Zipkin:** Trace visualization.

---

## 17. Future Architectural Considerations

These are NOT part of the MVP but are documented for future reference.

### 17.1 A2A Protocol Integration

- **When:** Phase 4+.
- **Approach:** Implement A2A gateway that translates A2A messages to internal format.
- **Impact:** New `integrations/a2a` app; no changes to core services.

### 17.2 MCP Protocol Integration

- **When:** Phase 4+.
- **Approach:** MCP adapter for tool access.
- **Impact:** New `integrations/mcp` app.

### 17.3 Self-Hosted LLM

- **When:** Phase 5+ (if privacy requirements demand it).
- **Approach:** Deploy Llama 3.1 70B on GPU instances; swap via provider abstraction.
- **Impact:** New `services/llm_provider` abstraction layer.

### 17.4 Blockchain Anchoring

- **When:** Phase 6+ (if explicit demand).
- **Approach:** Anchor agreement hashes to L2 (Polygon, Arbitrum).
- **Impact:** New `services/blockchain` module; optional feature.

### 17.5 Enterprise Multi-Tenancy

- **When:** Phase 4+.
- **Approach:** Organization model with hierarchical policies.
- **Impact:** Major schema changes; new `organizations` app.

### 17.6 Horizontal Scaling

- **When:** When hitting vertical scaling limits.
- **Approach:** Extract Policy Engine and Audit Service into separate services.
- **Impact:** Move from monolith to microservices; requires service mesh.

---

## 18. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-19 | Mauro Vicens | Initial approved version. |

---
