# Legatio AI — Product Requirements Document (PRD)

> **Version:** 1.0

> **Status:** Approved for development

> **Date:** August 19, 2026

> **Author:** Mauro Vicens

> **Repository:** `mocenslabs/legatio-ai`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision](#2-product-vision)
3. [Problem Statement](#3-problem-statement)
4. [Ideal Customer Profile (ICP)](#4-ideal-customer-profile-icp)
5. [Value Proposition](#5-value-proposition)
6. [What Legatio AI IS](#6-what-legatio-ai-is)
7. [What Legatio AI is NOT](#7-what-legatio-ai-is-not)
8. [MVP Use Cases](#8-mvp-use-cases)
9. [Future Use Cases (Out of MVP Scope)](#9-future-use-cases-out-of-mvp-scope)
10. [High-Level Architecture](#10-high-level-architecture)
11. [Technology Stack](#11-technology-stack)
12. [Success Metrics](#12-success-metrics)
13. [Assumptions & Constraints](#13-assumptions--constraints)
14. [Risks & Mitigations](#14-risks--mitigations)
15. [External Dependencies](#15-external-dependencies)
16. [MVP Acceptance Criteria](#16-mvp-acceptance-criteria)
17. [Glossary](#17-glossary)
18. [Change History](#18-change-history)

---

## 1. Executive Summary

**Legatio AI** is an authorization, policy, and audit infrastructure that enables AI agents to act on behalf of humans while enforcing deterministic rules and requiring human approval for sensitive actions.

**One-liner:**

> *Legatio AI is the trust and control layer between humans and autonomous AI agents.*

**The problem:**
AI agents are gaining autonomy to execute transactions, negotiate, and make decisions on behalf of users. However, there is no standardized layer of control, auditability, and human supervision to guarantee that these actions respect user preferences and do not exceed their delegated authority.

**The solution:**
Legatio AI provides a deterministic **Policy Engine** that evaluates every proposed action from an agent against user-defined rules (their "Constitution"), blocks forbidden actions, and requests human approval when an action exceeds predefined limits.

**Key differentiator:**
Unlike other systems that delegate decision-making to AI, Legatio AI clearly separates:

- **Negotiation Engine (LLM):** Proposes, reasons, negotiates.
- **Policy Engine (Deterministic):** Decides `ALLOW` / `DENY` / `REQUIRE_HUMAN_APPROVAL`.

**Technology stack:**

- **Backend:** Django 5.x + Django REST Framework + Django Channels
- **Frontend:** Vue 3 + Pinia + TanStack Query
- **Database:** PostgreSQL 16
- **Task queue:** Celery + Redis
- **Real-time:** WebSockets (Django Channels)
- **LLM:** OpenAI GPT-4 / Anthropic Claude (via API)

---

## 2. Product Vision

### 2.1 Long-Term Vision (3–5 years)

Legatio AI will become the de facto standard for authorization and governance of autonomous AI agents, enabling humans to delegate complex tasks to agents with the confidence that their preferences, limits, and personal data will be respected.

### 2.2 Mission

To provide a reliable, auditable, and transparent infrastructure that enables safe collaboration between humans and AI agents, guaranteeing that no action exceeds delegated authority.

### 2.3 Design Principles

1. **Security by default:** Every sensitive action requires explicit authorization.
2. **Full transparency:** The user always knows what their agent is doing and why.
3. **Deterministic control:** Policies are applied predictably and auditably.
4. **Separation of concerns:** AI proposes; the Policy Engine decides.
5. **Interoperability:** Compatible with emerging protocols (A2A, MCP).
6. **Privacy first:** User data never leaves their control.

---

## 3. Problem Statement

### 3.1 The Core Problem

In 2026, AI agents are rapidly evolving toward autonomy:

- **Personal agents** buy products, book trips, manage subscriptions.
- **Enterprise agents** negotiate contracts, process payments, manage suppliers.
- **Hybrid agents** interact with each other to coordinate complex tasks.

**The problem:** There is no standardized control layer that guarantees:

1. Agents respect user preferences (budget, privacy, etc.).
2. Sensitive actions require human approval.
3. Every action is audited and explainable.
4. Agreements between agents are verifiable and non-repudiable.

### 3.2 Current Problematic Scenarios

**Scenario 1: Unauthorized spending**

```text
User:      "Find a hotel in Madrid for less than €700."
Agent:     Finds a hotel for €680, but the provider asks for a phone number.
Agent:     Agrees to share the phone number to get a better price.
Result:    User is charged €680 + their phone is in a third-party database.
Problem:   The agent violated a privacy preference without consulting.
```

**Scenario 2: Financial hallucination**

```text
User:      "Negotiate my internet bill."
Agent:     Hallucinates and accepts a 24-month contract with auto-renewal.
Result:    User is locked into a long contract without knowing.
Problem:   No validation of critical terms before signing.
```

**Scenario 3: Lack of auditability**

```text
User:      "Why did my agent buy this?"
System:    No record of why the decision was made.
Result:    User cannot understand or dispute the action.
Problem:   Lack of explainability and audit trail.
```

### 3.3 Impact of the Problem

- **Financial:** Losses from unauthorized or poorly negotiated expenses.
- **Privacy:** Exposure of personal data without informed consent.
- **Trust:** Users hesitate to delegate tasks to agents.
- **Legal:** Unclear liability in case of disputes.
- **Adoption:** Slows adoption of autonomous agents due to lack of control.

---

## 4. Ideal Customer Profile (ICP)

### 4.1 Primary Segment: Technical Early Adopters

**Profile:**

- Developers, software engineers, system architects.
- Age: 25–45.
- Familiar with AI, APIs, and automation concepts.
- Already using or experimenting with AI agents (AutoGPT, LangChain, etc.).
- Value control, transparency, and auditability.

**Pain points:**

- Frustration with lack of control over autonomous agents.
- Concerns about security and privacy.
- Need to demonstrate governance in enterprise projects.
- Desire for tools that respect their technical expertise.

**Behavior:**

- Willing to try beta products.
- Active in technical communities (GitHub, Discord, Reddit).
- Value clear documentation and well-designed APIs.
- Expect open source or at least technical transparency.

### 4.2 Secondary Segment: AI Power Users

**Profile:**

- Professionals using AI for personal productivity.
- Already have agents configured for recurring tasks.
- Not developers, but technically competent.
- Value simplicity and intuitive interfaces.

**Pain points:**

- Fear that their agent will make costly mistakes.
- Difficulty understanding what their agent is doing.
- Need to manually approve every action (decision fatigue).

### 4.3 Tertiary Segment (Future): Enterprises

**Profile:**

- Companies deploying agents to automate processes.
- Need governance, auditing, and compliance.
- Require integration with existing systems.

**Pain points:**

- Regulatory risk from autonomous AI usage.
- Need for audit trails for compliance.
- Difficulty managing policies at scale.

---

## 5. Value Proposition

### 5.1 For the Individual User

**Before Legatio AI:**

- Your agent can spend whatever it wants without consulting you.
- You don't know what data it shares with third parties.
- You can't understand why it made certain decisions.
- There's no way to audit or dispute actions.

**With Legatio AI:**

- You define clear rules (budget, privacy, etc.).
- The agent never exceeds your authority without asking.
- Every action is audited and explainable.
- You have full control over what it can and cannot do.

### 5.2 For the Developer

**Before Legatio AI:**

- You have to build your own authorization system.
- There's no standard for agent policies.
- Integrating human approval is complex.
- Lack of robust audit trails.

**With Legatio AI:**

- Ready-to-use SDK/API.
- Deterministic and testable Policy Engine.
- Out-of-the-box human approval integration.
- Complete and exportable audit trail.
- Compatible with A2A and MCP.

### 5.3 Value Proposition in One Sentence

> *Legatio AI lets you delegate tasks to AI agents with the confidence that your rules will be respected and sensitive actions will require your approval.*

---

## 6. What Legatio AI IS

### 6.1 Main Components

**1. Policy Engine**

- Deterministic engine that evaluates proposed actions against defined rules.
- Returns: `ALLOW`, `DENY`, or `REQUIRE_HUMAN_APPROVAL`.
- 100% auditable and predictable.
- Does NOT use an LLM for authorization decisions.

**2. Constitution**

- Set of rules defining agent limits.
- Examples: max budget, forbidden data, actions requiring approval.
- Configurable via UI or API.
- Versioned (every change creates a new version).

**3. Negotiation Engine**

- LLM that understands proposals, generates counter-offers, summarizes agreements.
- Works WITHIN the limits defined by the Policy Engine.
- Does NOT make authorization decisions.

**4. Audit Trail**

- Complete record of every action, decision, and approval.
- Includes: timestamp, agent, proposed action, applied policy, decision, reason.
- Exportable in standard formats (JSON, CSV, PDF).
- Cryptographic hash for integrity.

**5. Human Approval Interface**

- Dashboard showing actions pending approval.
- Clear explanation of why approval is required.
- Options: Approve, Reject, Modify.
- Real-time notifications (push, email, WebSocket).

**6. Agreement Generator**

- When a negotiation reaches consensus, generates an "Agreement Record".
- Canonical JSON with all terms.
- SHA-256 hash + digital signature.
- Recorded in the audit trail.

### 6.2 Basic Flow

```text
1. User defines their Constitution (rules)
   ↓
2. User starts a negotiation (e.g., "Find a hotel in Madrid")
   ↓
3. User Agent (LLM) receives the instruction
   ↓
4. User Agent connects with External Agent (e.g., Hotel Agent)
   ↓
5. External Agent makes a proposal (e.g., "€680 + share phone number")
   ↓
6. Proposal goes through the Policy Engine
   ↓
7. Policy Engine evaluates:
   - Is €680 <= €700? ✓
   - Is sharing phone allowed? ✗ (NEVER)
   → Decision: DENY (Reason: "Rule #17: phone_number = NEVER")
   ↓
8. User Agent receives DENY and generates a counter-offer
   (e.g., "€680 without sharing phone number")
   ↓
9. External Agent accepts: "€700 without phone"
   ↓
10. Proposal goes through the Policy Engine
    - Is €700 <= €700? ✓
    - Is sharing phone? Not applicable
    → Decision: ALLOW
    ↓
11. Agreement Record is generated with hash and signature
    ↓
12. User receives notification: "Agreement reached. Approve?"
    ↓
13. User reviews details and approves/rejects
    ↓
14. If approved → Agreement is marked as executed
    If rejected → Agreement is voided and External Agent is notified
```

---

## 7. What Legatio AI is NOT

### 7.1 NOT a Chatbot or Conversational Assistant

Legatio AI is not a chatbot for users to chat with. It is infrastructure that sits between agents.

**What we DON'T do:**

- ❌ Customer service chatbot.
- ❌ Personal assistant like Siri/Alexa.
- ❌ Conversational interface for general tasks.

### 7.2 NOT an Agent Marketplace

Legatio AI is not a place where users discover and hire agents.

**What we DON'T do:**

- ❌ App Store-style marketplace for agents.
- ❌ Agent recommendation system.
- ❌ Monetization through agent sales.

### 7.3 NOT an Agent-Building Framework

Legatio AI does not compete with LangChain, CrewAI, AutoGen, etc.

**What we DON'T do:**

- ❌ Framework to build agents from scratch.
- ❌ Multi-agent orchestration.
- ❌ Prompting or fine-tuning tools.

**What we DO:**

- ✅ Authorization layer that integrates WITH those frameworks.
- ✅ SDK for developers to connect their agents to Legatio.

### 7.4 NOT a Blockchain or Smart Contract System

Legatio AI does not use blockchain for agreements (at least not in the MVP).

**What we DON'T do:**

- ❌ Smart contracts on Ethereum/Solana.
- ❌ Tokens or cryptocurrencies.
- ❌ DeFi or decentralized payments.

**What we DO:**

- ✅ SHA-256 hash + digital signature for integrity.
- ✅ Audit trail in PostgreSQL.
- ✅ Possible blockchain integration in future phases if there is demand.

### 7.5 NOT a Legally Binding System

Legatio AI does not guarantee that agreements are legally binding.

**What we DON'T do:**

- ❌ Qualified electronic signatures (eIDAS).
- ❌ Legal advice.
- ❌ Guarantee of legal validity.

**What we DO:**

- ✅ Cryptographic record of user authorization.
- ✅ Complete audit trail.
- ✅ Possible integration with electronic signature services in future phases.

---

## 8. MVP Use Cases

### 8.1 Primary Use Case: "AI Travel Negotiation"

**Scenario:**
User wants to book a hotel in Madrid for 5 nights.

**User Constitution:**

```yaml
financial:
  max_transaction: 700
  currency: EUR
  auto_approve: 200

privacy:
  phone_number: NEVER
  email: ALLOWED
  health_data: NEVER

negotiation:
  maximum_discount: 20%
  minimum_refund: 80%

human_approval:
  - payment > 200
  - contract_creation
  - personal_data_disclosure
```

**Flow:**

1. User starts negotiation: "Find hotel in Madrid, 5 nights, < €700"
2. User Agent connects with Hotel Agent (simulated)
3. Hotel Agent proposes: €820
4. User Agent counter-offers: €650
5. Hotel Agent: "€680 if you share your phone number"
6. Policy Engine evaluates:
   - €680 <= €700 ✓
   - `phone_number = NEVER` ✗
   → **DENY** (Reason: "Rule #17: phone_number = NEVER")
7. User Agent: "€680 without sharing phone number"
8. Hotel Agent: "€700 without phone, 48h cancellation"
9. Policy Engine evaluates:
   - €700 <= €700 ✓
   - `phone_number`: not applicable ✓
   → **ALLOW**
10. Agreement Record is generated
11. User receives notification: "Agreement: €700, 5 nights, no phone"
12. User approves
13. Agreement is marked as executed

**MVP Success:**

- User can define a Constitution.
- Agents can negotiate.
- Policy Engine blocks forbidden actions.
- User can approve/reject agreements.
- Complete audit trail.

### 8.2 Secondary Use Case: "Subscription Negotiation"

**Scenario:**
User wants to negotiate their internet subscription.

**Constitution:**

```yaml
financial:
  max_monthly_spend: 100
  auto_approve: 50

negotiation:
  maximum_contract_length_months: 12
  auto_renewal: REQUIRE_APPROVAL

human_approval:
  - contract_length > 12
  - auto_renewal
  - price_increase > 10%
```

**Flow:**

1. User: "Negotiate my internet bill"
2. User Agent connects with ISP Agent (simulated)
3. ISP Agent: "I offer you €60/month for 24 months with auto-renewal"
4. Policy Engine evaluates:
   - €60 <= €100 ✓
   - 24 months > 12 months ✗
   → **REQUIRE_HUMAN_APPROVAL** (Reason: "Contract length exceeds limit")
5. User receives notification: "ISP offers €60/month for 24 months. Your limit is 12 months. Approve?"
6. User rejects
7. User Agent: "Maximum 12 months, no auto-renewal"
8. ISP Agent: "€70/month for 12 months, no auto-renewal"
9. Policy Engine evaluates:
   - €70 <= €100 ✓
   - 12 months <= 12 months ✓
   - `auto_renewal`: no ✓
   → **ALLOW**
10. User approves agreement

### 8.3 Tertiary Use Case: "Purchase Approval"

**Scenario:**
User wants their agent to buy products under certain conditions.

**Constitution:**

```yaml
financial:
  max_transaction: 50
  max_monthly_spend: 200
  auto_approve: 20

categories:
  allowed:
    - electronics
    - books
    - software
  prohibited:
    - gambling
    - adult_content

human_approval:
  - payment > 20
  - new_vendor
```

**Flow:**

1. User: "Buy book X if it costs less than €30"
2. User Agent searches in Vendor Agent (simulated)
3. Vendor Agent: "Book X costs €25"
4. Policy Engine evaluates:
   - €25 <= €50 ✓
   - category: books ✓
   - €25 > €20 (auto_approve limit)
   → **REQUIRE_HUMAN_APPROVAL**
5. User approves
6. Purchase is executed
7. Audit trail records the transaction

---

## 9. Future Use Cases (Out of MVP Scope)

### 9.1 Enterprise Legatio

**Description:**
Version for companies where multiple employees use agents under corporate policies.

**Features:**

- Policy hierarchy (Global → Department → Employee).
- Corporate SSO integration.
- Compliance dashboard for auditors.
- Reporting and analytics.

**When:** Phase 4+ (after validating MVP with individual users).

### 9.2 Agent Reputation System

**Description:**
Reputation system for external agents based on negotiation history.

**Features:**

- Agent rating (reliability, transparency, results).
- Badges and certifications.
- Alerts about problematic agents.

**When:** Phase 5+ (requires a network of connected agents).

### 9.3 Constitution Marketplace

**Description:**
Library of Constitution templates for common use cases.

**Features:**

- Pre-configured templates (travel, shopping, subscriptions).
- Community-shared constitutions.
- Ratings and comments.

**When:** Phase 3+ (after validating that users understand the concept).

### 9.4 A2A and MCP Integration

**Description:**
Native support for agent interoperability protocols.

**Features:**

- Automatic agent discovery via A2A.
- Integration with external tools via MCP.
- Gateway compatible with emerging standards.

**When:** Phase 4+ (when protocols are more mature).

### 9.5 Blockchain Anchoring

**Description:**
Anchoring agreements on blockchain for greater immutability.

**Features:**

- Agreement hashes on L2 (Polygon, Arbitrum).
- Agreement NFTs (optional).
- On-chain verification.

**When:** Phase 6+ (only if there is explicit demand).

### 9.6 Qualified Electronic Signature

**Description:**
Integration with electronic signature services for legal validity.

**Features:**

- Integration with DocuSign, Firmaprofesional, etc.
- eIDAS compliance.
- Digital certificates.

**When:** Phase 5+ (requires legal advice per jurisdiction).

---

## 10. High-Level Architecture

### 10.1 Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                         HUMAN USER                          │
│         (Defines Constitution, Approves Agreements)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTPS + WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND: VUE 3                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Constitution │  │  Dashboard   │  │   Approval   │      │
│  │   Builder    │  │(Negotiations)│  │  Interface   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  Tech: Vue 3, Pinia, TanStack Query, Tailwind CSS           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ REST API + WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   API GATEWAY (DJANGO)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Django REST Framework (DRF)                         │  │
│  │  - Authentication (JWT + 2FA)                        │  │
│  │  - Rate limiting                                     │  │
│  │  - Request validation                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Django Channels (WebSocket)                         │  │
│  │  - Real-time notifications                           │  │
│  │  - Negotiation updates                               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ CONSTITUTION │  │   POLICY     │  │ NEGOTIATION  │
│   SERVICE    │  │   ENGINE     │  │   SERVICE    │
│              │  │              │  │              │
│ - CRUD rules │  │ - Evaluate   │  │ - Manage     │
│ - Versioning │  │   proposals  │  │   rooms      │
│ - Validation │  │ - ALLOW/DENY │  │ - Messages   │
│              │  │ - Audit      │  │ - LLM calls  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
              ┌─────────────────────┐
              │   AUDIT SERVICE     │
              │                     │
              │ - Log all events    │
              │ - Generate hashes   │
              │ - Export reports    │
              └──────────┬──────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │    Redis     │  │   Celery     │
│              │  │              │  │              │
│ - Users      │  │ - Cache      │  │ - LLM tasks  │
│ - Constitutions│ │ - Queues     │  │ - Audit      │
│ - Negotiations│  │ - Rate limit │  │ - Notifs     │
│ - Audit logs │  │ - Temp state │  │ - Background │
└──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  EXTERNAL AGENTS    │
              │   (via API/SDK)     │
              │                     │
              │ - Hotel Agent       │
              │ - ISP Agent         │
              │ - Vendor Agent      │
              │ - Custom Agents     │
              └─────────────────────┘
```

### 10.2 Separation of Responsibilities

**Negotiation Engine (LLM-based):**

- Understands proposals in natural language.
- Generates counter-offers.
- Summarizes agreements.
- Does NOT decide if an action is allowed.

**Policy Engine (Deterministic):**

- Receives structured proposal (JSON).
- Evaluates against Constitution rules.
- Returns: `ALLOW`, `DENY`, `REQUIRE_HUMAN_APPROVAL`.
- 100% predictable and auditable.
- Does NOT use an LLM.

**Audit Service:**

- Records every event (proposal, decision, approval).
- Generates cryptographic hashes.
- Provides log export.
- Guarantees integrity.

### 10.3 Data Flow

```text
1. User creates Constitution → Constitution Service → PostgreSQL
   ↓
2. User starts negotiation → Negotiation Service → Creates room
   ↓
3. External Agent sends proposal → Negotiation Service
   ↓
4. Proposal goes through Policy Engine → Evaluates rules
   ↓
5. Policy Engine returns decision → Negotiation Service
   ↓
6. If ALLOW → Generates Agreement → Audit Service → Notifies user
   If DENY → Rejects proposal → User Agent generates counter-offer
   If REQUIRE_HUMAN_APPROVAL → Notifies user → Waits for approval
   ↓
7. User approves/rejects → Negotiation Service → Audit Service
   ↓
8. Final Agreement → Hash + Signature → Complete audit trail
```

---

## 11. Technology Stack

### 11.1 Backend: Django 5.x

**Why Django:**

- ✅ Mature and stable framework (15+ years of development).
- ✅ Robust ORM for complex relational data models.
- ✅ Security by default (CSRF, SQL injection, XSS).
- ✅ Rich ecosystem (DRF, Channels, Celery).
- ✅ Excellent for REST APIs.
- ✅ Out-of-the-box admin interface (useful for debugging).
- ✅ Large community and excellent documentation.

**Components:**

- **Django REST Framework (DRF):** REST APIs for frontend and external agents.
- **Django Channels:** WebSockets for real-time notifications.
- **Django Allauth:** Authentication (email, social, 2FA).
- **Django Cryptography:** Encryption of sensitive data.
- **Celery:** Asynchronous task queue (LLM calls, audit processing).
- **Redis:** Broker for Celery, cache, rate limiting.

**Versions:**

- Python: 3.11+
- Django: 5.0+
- DRF: 3.14+
- Django Channels: 4.0+

### 11.2 Frontend: Vue 3

**Why Vue 3:**

- ✅ Composition API for reusable logic.
- ✅ Efficient reactivity.
- ✅ Mature ecosystem (Pinia, Vue Router, TanStack Query).
- ✅ Moderate learning curve.
- ✅ Excellent for interactive dashboards.
- ✅ Native TypeScript support.

**Components:**

- **Vue 3:** Main framework.
- **Pinia:** Global state (Constitution, active negotiations).
- **Vue Router:** Navigation.
- **TanStack Query:** Server data management (cache, refetch, optimistic updates).
- **Socket.io-client:** WebSockets for real-time.
- **Tailwind CSS:** Utility-first CSS.
- **shadcn-vue:** Accessible and customizable UI components.
- **Chart.js:** Metrics visualization.
- **Vue Flow:** Negotiation flow diagrams.

**Versions:**

- Node.js: 20+
- Vue: 3.4+
- Pinia: 2.1+
- Vite: 5.0+

### 11.3 Database: PostgreSQL 16

**Why PostgreSQL:**

- ✅ Robust and scalable relational database.
- ✅ JSONB support for semi-structured data (Constitutions, proposals).
- ✅ ACID transactions critical for auditing.
- ✅ Useful extensions (pgcrypto for encryption, pgvector for future embeddings).
- ✅ Excellent performance with complex queries.
- ✅ Large community and mature tools.

**Usage:**

- Source of truth for all data.
- Storage of Constitutions, negotiations, messages, audit logs.
- Indexes for frequent queries.
- Partitioning for audit logs (future).

**Versions:**

- PostgreSQL: 16+

### 11.4 Task Queue: Celery + Redis

**Why Celery:**

- ✅ Mature and proven asynchronous task queue.
- ✅ Native integration with Django.
- ✅ Support for scheduled tasks (Celery Beat).
- ✅ Robust retry logic and error handling.

**Why Redis:**

- ✅ Fast broker for Celery.
- ✅ Cache for frequent data (active Constitutions).
- ✅ Rate limiting.
- ✅ Temporary state of ongoing negotiations.

**Asynchronous tasks:**

- LLM calls (OpenAI, Anthropic).
- Audit log processing.
- Sending notifications (email, push).
- Generating cryptographic hashes.
- Report export.

**Versions:**

- Celery: 5.3+
- Redis: 7.0+

### 11.5 LLM: OpenAI GPT-4 / Anthropic Claude

**Why external APIs (not self-hosted):**

- ✅ Superior quality for negotiation and summarization.
- ✅ No need to train models.
- ✅ Variable cost based on usage (better for MVP).
- ✅ Less infrastructure to maintain.

**Usage:**

- **Negotiation Engine:** Understand proposals, generate counter-offers, summarize agreements.
- **NOT used for authorization decisions** (that's the Policy Engine's job).

**Models:**

- GPT-4o (OpenAI) or Claude 3.5 Sonnet (Anthropic).
- Fallback between providers if one fails.

**Estimated cost:**

- $0.01 – $0.05 per negotiation (depending on length).
- For MVP: $50–100/month with 1000 negotiations.

**Future alternative:**

- Self-hosted Llama 3.1 70B to reduce costs and increase privacy.
- Requires significant GPU (A100 or equivalent).

### 11.6 Real-time: WebSockets (Django Channels)

**Why WebSockets:**

- ✅ Real-time notifications without polling.
- ✅ Live negotiation updates.
- ✅ Better UX for human approval.

**WebSocket events:**

```javascript
negotiation.started       // New negotiation started
negotiation.updated       // Negotiation state changed
proposal.created          // New proposal received
counterproposal.created   // Counter-offer generated
approval.required         // Human approval required
agreement.signed          // Agreement reached
audit.event               // Audit event
```

### 11.7 Authentication and Security

**Authentication:**

- JWT tokens for API.
- 2FA (TOTP) for sensitive actions.
- Django Allauth for standard flows.

**Security:**

- HTTPS mandatory.
- CSRF protection.
- SQL injection protection (Django ORM).
- XSS protection.
- Rate limiting (Redis).
- Encryption of sensitive data (Constitutions).

### 11.8 Infrastructure

**Development:**

- Docker + Docker Compose.
- SQLite for local development (optional).
- Hot reload for Django and Vue.

**Production (future):**

- Docker containers.
- Nginx as reverse proxy.
- Cloudflare for CDN and DDoS protection.
- AWS/GCP/DigitalOcean for hosting.
- Managed PostgreSQL (RDS, Cloud SQL).
- Managed Redis (ElastiCache, MemoryDB).
- Sentry for error tracking.
- Prometheus + Grafana for metrics.

---

## 12. Success Metrics

### 12.1 Product Metrics (MVP)

**Adoption:**

- ✅ 5 active beta users in the first 2 weeks.
- ✅ 50 completed negotiations in the first month.
- ✅ 80% of users complete onboarding.

**Engagement:**

- ✅ 3+ negotiations per active user per week.
- ✅ 70% of users define at least 5 rules in their Constitution.
- ✅ 90% of pending agreements approved/rejected in < 24h.

**Quality:**

- ✅ 0 critical security incidents.
- ✅ < 1% of negotiations failed due to technical errors.
- ✅ Average negotiation time < 5 minutes.

**Satisfaction:**

- ✅ NPS > 40.
- ✅ 80% of users say "I feel in control of my agent".
- ✅ 70% of users recommend Legatio to colleagues.

### 12.2 Technical Metrics

**Performance:**

- ✅ API response time < 200ms (p95).
- ✅ WebSocket latency < 100ms.
- ✅ Policy Engine evaluation < 50ms.
- ✅ Database query time < 100ms (p95).

**Reliability:**

- ✅ 99.5% uptime.
- ✅ < 0.1% error rate on APIs.
- ✅ 0 data loss in audit trail.

**Scalability:**

- ✅ Supports 100 concurrent negotiations.
- ✅ Supports 1000 registered users.
- ✅ Database handles 1M audit events without degradation.

### 12.3 Business Metrics (Future)

**Revenue:**

- 📈 MRR (Monthly Recurring Revenue).
- 📈 ARPU (Average Revenue Per User).
- 📈 Churn rate < 5% monthly.

**Growth:**

- 📈 MAU (Monthly Active Users).
- 📈 DAU/MAU ratio > 20%.
- 📈 Viral coefficient > 1.2.

---

## 13. Assumptions & Constraints

### 13.1 Assumptions

1. **External agents cooperate:** We assume external agents (Hotel Agent, ISP Agent) follow the protocol and respond in good faith. We do not handle malicious agents in MVP.
2. **Users have agents:** We assume the user already has an agent (or will use our simulated agent for testing). Legatio does not build agents, only authorizes them.
3. **LLMs are reasonably competent:** We assume GPT-4/Claude can understand proposals and generate coherent counter-offers. We do not handle critical hallucinations in MVP.
4. **Users understand the concept:** We assume early adopters understand what a "Constitution" is and can define rules. We do not do extremely guided onboarding.
5. **No strict legal requirements:** We assume that for MVP we do not need qualified electronic signatures or specific regulatory compliance.
6. **A2A/MCP protocols are optional:** We assume that for MVP we can use a simple REST API. Integration with A2A/MCP comes in later phases.

### 13.2 Constraints

1. **We do not process payments:** Legatio does not move money. It only authorizes actions. Payments are made outside Legatio (Stripe, PayPal, etc.).
2. **We do not provide legal advice:** Legatio does not guarantee legal validity of agreements. It only records user authorization.
3. **We are not responsible for agent actions:** Legatio is a control tool, not an agent. The user is responsible for their agent's actions.
4. **We do not store unnecessary sensitive data:** Data minimization. We do not store credit card numbers, passwords, etc.
5. **We do not compete with agent frameworks:** We do not build agents from scratch. We integrate with existing agents.
6. **We do not use blockchain in MVP:** Agreements are recorded in PostgreSQL with cryptographic hash. Blockchain is optional in future phases.

---

## 14. Risks & Mitigations

### 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucinates and accepts incorrect terms | Medium | High | Deterministic Policy Engine validates EVERYTHING. LLM only proposes. Double verification with different models. |
| Prompt injection between agents | Medium | High | Isolated sandbox. Policy Engine blocks forbidden actions. Audit trail detects anomalies. |
| High latency in long negotiations | Medium | Medium | Celery for async tasks. Message pagination. Constitution caching. |
| WebSocket scalability | Low | Medium | Django Channels + Redis. Migrate to pure ASGI if it grows. Load balancing. |
| Audit trail data loss | Low | Critical | ACID transactions in PostgreSQL. Daily backups. Replication. |
| LLM cost spikes | Medium | Medium | Cache frequent responses. Smaller models for simple tasks. Self-hosted in the future. |

### 14.2 Product Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users don't understand the concept | High | High | Guided onboarding. Constitution templates. Clear examples. Extensive documentation. |
| Human approval fatigue | Medium | Medium | Conditional pre-approvals. Auto-approval limits. Clear dashboard. |
| Overwhelming complexity | Medium | High | MVP focused on 3 simple use cases. Don't cover everything from the start. |
| Dependence on external agents | High | High | Free SDK. Clear documentation. Simulated agent for testing. |
| Competition from big players | Medium | High | Move fast. Focus on niche (authorization layer). Open source if necessary. |

### 14.3 Legal Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Liability for agent errors | Medium | High | Clear Terms of Service. Legatio is a facilitator, not responsible. User approves actions. |
| Privacy violation (GDPR) | Medium | Critical | Data minimization. Right to be forgotten. Explicit consent. Designated DPO. |
| Non-binding agreements | High | Medium | Don't promise legal validity. Only record authorization. Integrate electronic signature in the future. |
| AI regulation (EU AI Act) | Medium | High | Legatio is "human-in-the-loop" (meets requirements). Compliance documentation. |

### 14.4 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No real demand | Medium | Critical | Validate with 10 users before building. Minimal MVP. Pivot if necessary. |
| Business model doesn't work | Medium | High | Freemium + API usage-based. Test pricing with beta users. |
| Can't get initial users | Medium | High | Developer community. Open source SDK. Technical content marketing. |

---

## 15. External Dependencies

### 15.1 Third-Party APIs

**LLM Providers:**

- OpenAI API (GPT-4o).
- Anthropic API (Claude 3.5 Sonnet).
- **Fallback:** If one fails, use the other.

**Email/SMS (future):**

- SendGrid or Mailgun for transactional emails.
- Twilio for SMS (critical notifications).

**Payments (future):**

- Stripe for subscriptions.
- We do not process negotiation payments (external agents do that).

### 15.2 Protocols and Standards

**A2A (Agent-to-Agent):**

- Google protocol for agent interoperability.
- **Status in MVP:** Not integrated. Own REST API.
- **Future:** Integration in Phase 4+.

**MCP (Model Context Protocol):**

- Anthropic protocol for tool access.
- **Status in MVP:** Not integrated.
- **Future:** Integration in Phase 4+.

### 15.3 Infrastructure

**Cloud Provider:**

- AWS, GCP, or DigitalOcean (decision in Phase 2).
- Managed PostgreSQL and Redis recommended.

**CDN/Security:**

- Cloudflare for CDN, DDoS protection, SSL.

**Monitoring:**

- Sentry for error tracking.
- Prometheus + Grafana for metrics.
- LogDNA or Datadog for logs.

### 15.4 Legal/Compliance

**Terms of Service:**

- We need a lawyer specialized in AI and e-commerce.
- Jurisdiction: TBD (probably USA or EU).

**Privacy:**

- GDPR compliance if there are European users.
- Clear privacy policy.
- Explicit consent for audit trail.

**Electronic Signature (future):**

- eIDAS compliance if we operate in the EU.
- Integration with DocuSign or similar.

---

## 16. MVP Acceptance Criteria

### 16.1 Core Functionality

- [ ] User can register and log in (email + password + 2FA).
- [ ] User can create a Constitution with at least 5 rules.
- [ ] User can start a negotiation (e.g., "Find hotel in Madrid").
- [ ] User Agent can connect with External Agent (simulated).
- [ ] Policy Engine evaluates proposals and returns `ALLOW` / `DENY` / `REQUIRE_HUMAN_APPROVAL`.
- [ ] Policy Engine blocks forbidden actions (e.g., sharing phone number).
- [ ] User receives notification when approval is required.
- [ ] User can approve or reject pending agreements.
- [ ] Agreement Record is generated with SHA-256 hash.
- [ ] Complete and exportable audit trail (JSON, CSV).
- [ ] Dashboard shows active negotiations and history.

### 16.2 Validated Use Cases

- [ ] **AI Travel Negotiation:** User books a hotel under restrictions.
- [ ] **Subscription Negotiation:** User negotiates internet bill.
- [ ] **Purchase Approval:** User approves purchases under limits.

### 16.3 Technical Quality

- [ ] 0 critical or security bugs.
- [ ] Test coverage > 80% (unit + integration).
- [ ] API response time < 200ms (p95).
- [ ] WebSocket latency < 100ms.
- [ ] Complete API documentation (Swagger/OpenAPI).
- [ ] Clear README with setup instructions.

### 16.4 User Experience

- [ ] Onboarding completed in < 5 minutes.
- [ ] User can create Constitution without help.
- [ ] Approval notifications are clear and actionable.
- [ ] Audit trail is understandable for non-technical users.
- [ ] Responsive UI (desktop + tablet).

### 16.5 User Validation

- [ ] 5 beta users complete at least 3 negotiations each.
- [ ] NPS > 40.
- [ ] 80% of users say "I feel in control of my agent".
- [ ] 0 users report data loss or critical errors.

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI entity that acts on behalf of a user or company. |
| **Agreement Record** | Cryptographic record of an agreement reached between agents, including SHA-256 hash and digital signature. |
| **ALLOW** | Policy Engine decision indicating a proposed action is allowed according to Constitution rules. |
| **Audit Trail** | Complete chronological record of all actions, decisions, and approvals in the system. |
| **Constitution** | Set of user-defined rules that limit agent authority (budget, privacy, etc.). |
| **Counter-proposal** | Counter-offer generated by the User Agent in response to an External Agent's proposal. |
| **DENY** | Policy Engine decision indicating a proposed action violates Constitution rules and must be blocked. |
| **External Agent** | Third-party AI agent (e.g., Hotel Agent, ISP Agent) that the User Agent negotiates with. |
| **Human Approval** | Process by which the user reviews and approves/rejects an action that exceeds auto-approval limits. |
| **Negotiation Room** | Isolated environment where two agents interact to reach an agreement. |
| **Policy Engine** | Deterministic engine that evaluates proposed actions against Constitution rules and returns `ALLOW` / `DENY` / `REQUIRE_HUMAN_APPROVAL`. |
| **Proposal** | Initial offer or counter-offer sent by an agent during a negotiation. |
| **REQUIRE_HUMAN_APPROVAL** | Policy Engine decision indicating a proposed action exceeds auto-approval limits and requires human review. |
| **User Agent** | AI agent acting on behalf of the user, connected to Legatio. |

---

## 18. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-19 | Mauro Vicens | Initial approved version. |

---
