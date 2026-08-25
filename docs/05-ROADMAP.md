# Legatio AI — Development Roadmap

> **Version:** 1.0

> **Status:** Approved

> **Date:** August 19, 2026

> **Author:** Mauro Vicens

> **Repository:** `mocenslabs/legatio-ai`

> **Depends on:** `01-PRD.md` (v1.0), `02-ARCHITECTURE.md` (v1.0), `03-DATA-MODEL.md` (v1.0), `04-BUSINESS-FLOW.md` (v1.0)

---

## Table of Contents

1. [Document Purpose](#1-document-purpose)
2. [Roadmap Philosophy](#2-roadmap-philosophy)
3. [Phase Overview](#3-phase-overview)
4. [Phase 0: Foundation](#4-phase-0-foundation)
5. [Phase 1: Policy Engine (The Heart)](#5-phase-1-policy-engine-the-heart)
6. [Phase 2: Constitution & Rules](#6-phase-2-constitution--rules)
7. [Phase 3: Negotiation Simulator](#7-phase-3-negotiation-simulator)
8. [Phase 4: Human Approval Workflow](#8-phase-4-human-approval-workflow)
9. [Phase 5: Audit Trail & Agreement](#9-phase-5-audit-trail--agreement)
10. [MVP Release Gate](#10-mvp-release-gate)
11. [Phase 6: Real LLM Integration](#11-phase-6-real-llm-integration)
12. [Phase 7: A2A Protocol Integration](#12-phase-7-a2a-protocol-integration)
13. [Phase 8: MCP Protocol Integration](#13-phase-8-mcp-protocol-integration)
14. [Phase 9: Agent Identity & Credentials](#14-phase-9-agent-identity--credentials)
15. [Phase 10: Reputation System](#15-phase-10-reputation-system)
16. [Future Horizons (Not Scheduled)](#16-future-horizons-not-scheduled)
17. [Dependency Graph](#17-dependency-graph)
18. [Risk Checkpoints](#18-risk-checkpoints)
19. [Resource Estimates](#19-resource-estimates)
20. [Definition of Done (Global)](#20-definition-of-done-global)
21. [Change History](#21-change-history)

---

## 1. Document Purpose

This document defines the **incremental development plan** for Legatio AI. It answers:

- What do we build first, and why?
- What does "done" mean for each phase?
- What are the dependencies between phases?
- Where are the risk checkpoints?
- How long should each phase take?

**Critical rule:** No phase begins until the previous phase's acceptance criteria are met. This prevents building on unstable foundations.

**This document is NOT:**

- A Gantt chart with fixed dates.
- A commitment to external stakeholders.
- A replacement for sprint planning.

**This document IS:**

- A sequencing guide.
- A scope control mechanism.
- A risk management tool.
- The answer to "what should we work on next?"

---

## 2. Roadmap Philosophy

### 2.1 Start with the Policy Engine. Not LangGraph. Not Blockchain. Not Two Agents Talking.

The single most important decision in this roadmap:

> **The first thing we build is the deterministic Policy Engine.**

Rationale:

- If the Policy Engine works, everything else can be built around it.
- If the Policy Engine doesn't work, nothing else matters.
- The Policy Engine is the core differentiator. It's what makes Legatio not just another chatbot.
- It's fully testable with zero external dependencies.
- It proves the architectural principle: "AI proposes, Policy Engine decides."

### 2.2 Incremental, Not Big-Bang

Each phase produces a **working, demonstrable increment**. At no point should we have 3 months of code that doesn't run.

```text
Phase 1: Policy Engine evaluates a proposal → returns ALLOW/DENY
Phase 2: User defines rules → Policy Engine uses them
Phase 3: Simulated agents exchange proposals → Policy Engine evaluates
Phase 4: Human sees approval request → approves/rejects
Phase 5: Agreement is generated, signed, hashed → audit trail complete
```

Each phase is independently valuable and independently testable.

### 2.3 Simulated Before Real

We use **simulated agents** (hardcoded responses, scripted negotiations) before integrating real LLMs. This:

- Eliminates LLM variability during core development.
- Makes tests deterministic.
- Reduces cost during development.
- Allows us to test the Policy Engine without worrying about LLM hallucinations.

Real LLMs come in Phase 6, after the core infrastructure is proven.

### 2.4 No Blockchain. No Marketplace. No Reputation. Not Yet.

These are explicitly **out of scope** for the MVP. Adding them early would:

- Distract from the core problem.
- Add operational complexity.
- Delay the MVP.
- Create features nobody has asked for.

They may be added later if there is real demand.

### 2.5 Portfolio-Driven Development

Every phase should produce something that can be shown in a portfolio:

- A working demo.
- A clear code example.
- A testable assertion.
- A visual artifact (dashboard, audit trail, approval flow).

If a phase doesn't produce something demonstrable, it's not done.

---

## 3. Phase Overview

| Phase | Name | Duration | Cumulative | Key Deliverable |
|-------|------|----------|------------|-----------------|
| 0 | Foundation | 1 week | Week 1 | Project scaffold, CI/CD, docs |
| 1 | Policy Engine | 2 weeks | Week 3 | Deterministic evaluator + tests |
| 2 | Constitution & Rules | 1.5 weeks | Week 4.5 | Rule CRUD + versioning |
| 3 | Negotiation Simulator | 2 weeks | Week 6.5 | Simulated agents + rooms |
| 4 | Human Approval | 1.5 weeks | Week 8 | Approval workflow + UI |
| 5 | Audit & Agreement | 2 weeks | Week 10 | Hash chain + signing |
| **MVP** | **Legatio v0.1** | **~10 weeks** | **Week 10** | **Working end-to-end demo** |
| 6 | Real LLM Integration | 2 weeks | Week 12 | LLM-powered negotiation |
| 7 | A2A Integration | 2 weeks | Week 14 | A2A gateway |
| 8 | MCP Integration | 1.5 weeks | Week 15.5 | MCP adapter |
| 9 | Agent Identity | 1.5 weeks | Week 17 | Credentials + auth |
| 10 | Reputation | 2 weeks | Week 19 | Agent scoring |

**Total estimated duration: ~19 weeks (4.5 months) for full roadmap.**

**MVP delivery: ~10 weeks (2.5 months).**

---

## 4. Phase 0: Foundation

### 4.1 Objective

Set up the project infrastructure so that all subsequent phases can focus on business logic, not boilerplate.

### 4.2 Duration

**1 week**

### 4.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 0.1 | Repository structure | Complete folder layout per `02-ARCHITECTURE.md` |
| 0.2 | Django project scaffold | Settings split (base/dev/prod), apps created |
| 0.3 | Vue 3 project scaffold | Vite + TypeScript + Tailwind + shadcn-vue |
| 0.4 | Docker Compose | Django + Vue + PostgreSQL + Redis + Celery |
| 0.5 | CI/CD pipeline | GitHub Actions: lint → test → build |
| 0.6 | Documentation structure | `/docs` folder with all 5 documents |
| 0.7 | Development environment script | `scripts/setup.sh` for one-command setup |
| 0.8 | Seed script skeleton | `scripts/seed.sh` placeholder |
| 0.9 | Pre-commit hooks | black, ruff, mypy, eslint |
| 0.10 | README | Project overview, setup instructions, badges |

### 4.4 Acceptance Criteria

- [x] `docker-compose up` starts all services successfully.
- [ ] Django admin accessible at `localhost:8000/admin`.
- [ ] Vue dev server accessible at `localhost:5173`.
- [ ] `pytest` runs with 0 tests (but framework configured).
- [ ] `npm run build` produces production bundle without errors.
- [ ] GitHub Actions pipeline passes on first push.
- [x] All 5 documentation files exist in `/docs`.
- [ ] A new developer can set up the project in < 10 minutes using README.

### 4.5 Dependencies

None. This is the starting point.

### 4.6 Risks

| Risk | Mitigation |
|------|-----------|
| Docker networking issues | Test on clean machine before committing |
| Version conflicts | Pin all versions in requirements.txt and package.json |

---

## 5. Phase 1: Policy Engine (The Heart)

### 5.1 Objective

Build the deterministic Policy Engine that evaluates proposed actions against rules. This is the core of Legatio. No LLM. No UI. Pure logic.

### 5.2 Duration

**2 weeks**

### 5.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 1.1 | `PolicyRule` model | Per `03-DATA-MODEL.md` Section 8.3 |
| 1.2 | `ProposedAction` dataclass | Input schema for evaluation |
| 1.3 | `PolicyDecision` dataclass | Output schema with outcome, reason, matched rules |
| 1.4 | `evaluate_policy()` function | Core evaluation algorithm per `04-BUSINESS-FLOW.md` Section 7 |
| 1.5 | `evaluate_condition()` function | Rule condition evaluator |
| 1.6 | `safe_evaluate()` wrapper | Fail-safe error handling (ERROR → DENY) |
| 1.7 | Risk assessment logic | `assess_risk()` function |
| 1.8 | Unit tests | 100% coverage of Policy Engine |
| 1.9 | Integration test | Evaluate a full proposal against a rule set |
| 1.10 | Performance test | Verify < 50ms evaluation time |

### 5.4 Acceptance Criteria

- [ ] `evaluate_policy()` returns `ALLOW` for compliant actions.
- [ ] `evaluate_policy()` returns `DENY` for forbidden actions (immediate, no further evaluation).
- [ ] `evaluate_policy()` returns `REQUIRE_HUMAN_APPROVAL` for threshold-exceeding actions.
- [ ] DENY is evaluated first (priority order respected).
- [ ] Same input + same rules = same output (determinism verified).
- [ ] Exception in evaluation → outcome is `ERROR` (treated as DENY).
- [ ] Evaluation completes in < 50ms for 100 rules.
- [ ] 100% unit test coverage on `services/policy_engine/`.
- [ ] All 3 MVP use cases from `04-BUSINESS-FLOW.md` pass as test cases.
- [ ] No LLM dependency in Policy Engine code.

### 5.5 Key Test Cases

```text
Test 1: ALLOW
  Input: amount=€50, rules=[amount ≤ €700 → ALLOW]
  Expected: ALLOW

Test 2: DENY (privacy)
  Input: data_fields=["phone_number"], rules=[phone_number = NEVER → DENY]
  Expected: DENY, matched_rule=Rule #17

Test 3: REQUIRE_APPROVAL
  Input: amount=€820, rules=[amount > €200 → REQUIRE_APPROVAL]
  Expected: REQUIRE_HUMAN_APPROVAL

Test 4: DENY takes priority
  Input: amount=€820, rules=[amount ≤ €700 → ALLOW, amount > €800 → DENY]
  Expected: DENY (not ALLOW)

Test 5: Empty rules
  Input: any action, rules=[]
  Expected: ALLOW (no rules to block)

Test 6: Exception handling
  Input: malformed rule
  Expected: ERROR outcome (treated as DENY)
```

### 5.6 Dependencies

- Phase 0 complete (project scaffold exists).

### 5.7 Risks

| Risk | Mitigation |
|------|-----------|
| Rule evaluation logic too complex | Start with 5 operators; add more incrementally |
| Performance issues with many rules | Index by priority; benchmark early |
| Edge cases in condition evaluation | Property-based testing with Hypothesis |

### 5.8 Definition of Done

The Policy Engine is a standalone, tested Python module that can evaluate any `ProposedAction` against any set of `PolicyRule` records and return a deterministic `PolicyDecision`. It has no dependencies on LLMs, WebSockets, or external services.

---

## 6. Phase 2: Constitution & Rules

### 6.1 Objective

Build the Constitution management system: users can create, edit, version, and activate Constitutions with rules. The Policy Engine consumes these rules.

### 6.2 Duration

**1.5 weeks**

### 6.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 2.1 | `Constitution` model | Per `03-DATA-MODEL.md` Section 8.1 |
| 2.2 | `ConstitutionVersion` model | Immutable versioned snapshot |
| 2.3 | Constitution CRUD API | REST endpoints for create/read/update |
| 2.4 | Rule CRUD API | Add/edit/delete rules within a constitution |
| 2.5 | Version activation logic | Activate new version, archive previous |
| 2.6 | Rule validation | Pydantic schemas for rule conditions |
| 2.7 | Constitution builder API | Endpoint to create constitution with rules in one call |
| 2.8 | Integration with Policy Engine | `evaluate_policy()` loads rules from active version |
| 2.9 | Unit tests | Constitution CRUD, versioning, activation |
| 2.10 | API documentation | OpenAPI/Swagger for all endpoints |

### 6.4 Acceptance Criteria

- [ ] User can create a Constitution with name and description.
- [ ] User can add rules to a Constitution (all categories: FINANCIAL, PRIVACY, NEGOTIATION, CUSTOM).
- [ ] User can activate a Constitution version.
- [ ] Only ONE Constitution can be ACTIVE per agent (enforced).
- [ ] Activating a new version archives the previous one.
- [ ] ConstitutionVersion is immutable once activated (no update API).
- [ ] Policy Engine can evaluate using the active ConstitutionVersion.
- [ ] API returns proper validation errors for malformed rules.
- [ ] All state changes produce AuditEvents.
- [ ] Swagger documentation auto-generated and accessible.

### 6.5 API Endpoints

```text
POST   /api/v1/constitutions/
GET    /api/v1/constitutions/
GET    /api/v1/constitutions/{id}/
PATCH  /api/v1/constitutions/{id}/
POST   /api/v1/constitutions/{id}/activate
GET    /api/v1/constitutions/{id}/versions
POST   /api/v1/constitutions/{id}/rules/
PATCH  /api/v1/rules/{id}/
DELETE /api/v1/rules/{id}/
POST   /api/v1/rules/{id}/evaluate    # Test a rule against a proposal
```

### 6.6 Dependencies

- Phase 1 complete (Policy Engine exists and is tested).

### 6.7 Risks

| Risk | Mitigation |
|------|-----------|
| Version management complexity | Keep it simple: sequential version numbers, no branching |
| Race condition on activation | Use `select_for_update()` in activation transaction |

---

## 7. Phase 3: Negotiation Simulator

### 7.1 Objective

Build the negotiation infrastructure with **simulated agents** (no LLM). Prove that proposals flow through the system and get evaluated by the Policy Engine.

### 7.2 Duration

**2 weeks**

### 7.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 3.1 | `Agent` model | Per `03-DATA-MODEL.md` Section 7.1 |
| 3.2 | `NegotiationRoom` model | Per `03-DATA-MODEL.md` Section 9.1 |
| 3.3 | `NegotiationMessage` model | Append-only message log |
| 3.4 | `Proposal` model | Per `03-DATA-MODEL.md` Section 10.1 |
| 3.5 | Negotiation CRUD API | Create room, list rooms, get room details |
| 3.6 | Simulated Hotel Agent | Hardcoded responses for "AI Travel Negotiation" |
| 3.7 | Simulated ISP Agent | Hardcoded responses for "Subscription Negotiation" |
| 3.8 | Simulated Vendor Agent | Hardcoded responses for "Purchase Approval" |
| 3.9 | Negotiation orchestrator | Manages rounds, calls Policy Engine, handles state |
| 3.10 | Policy Engine integration | Every proposal goes through `evaluate_policy()` |
| 3.11 | Counter-offer logic (rule-based) | Simple counter-offer generation (no LLM yet) |
| 3.12 | Unit tests | Orchestrator, state transitions, simulated agents |
| 3.13 | Integration test | Full "AI Travel Negotiation" scenario end-to-end |

### 7.4 Acceptance Criteria

- [ ] User can create a NegotiationRoom with user_agent and external_agent.
- [ ] Simulated Hotel Agent responds to negotiation start.
- [ ] Proposals are created and stored in database.
- [ ] Every proposal is evaluated by Policy Engine before proceeding.
- [ ] DENY decisions block the proposal and trigger counter-offer.
- [ ] ALLOW decisions allow the proposal to proceed.
- [ ] REQUIRE_HUMAN_APPROVAL decisions pause the negotiation (placeholder for Phase 4).
- [ ] NegotiationRoom state machine transitions correctly.
- [ ] Max rounds protection works (negotiation fails after N rounds).
- [ ] Full "AI Travel Negotiation" scenario passes end-to-end with simulated agents.
- [ ] All state changes produce AuditEvents.

### 7.5 Simulated Agent Behavior (Hotel Agent)

```python
class SimulatedHotelAgent:
    """Hardcoded responses for the Madrid hotel scenario."""

    RESPONSES = [
        # Round 1: Initial offer
        {
            "action_type": "purchase",
            "amount": 820.00,
            "currency": "EUR",
            "data_fields_requested": [],
            "terms": {"nights": 5, "breakfast": True},
        },
        # Round 2: Counter with phone request
        {
            "action_type": "purchase",
            "amount": 680.00,
            "currency": "EUR",
            "data_fields_requested": ["phone_number"],
            "terms": {"nights": 5},
        },
        # Round 3: Final offer without phone
        {
            "action_type": "purchase",
            "amount": 700.00,
            "currency": "EUR",
            "data_fields_requested": [],
            "terms": {"nights": 5, "cancellation": "48h"},
        },
    ]
```

### 7.6 Dependencies

- Phase 1 complete (Policy Engine).
- Phase 2 complete (Constitution & Rules).

### 7.7 Risks

| Risk | Mitigation |
|------|-----------|
| Orchestrator logic becomes spaghetti | Use explicit state machine pattern |
| Simulated agents too rigid | Design interface so LLM agents can replace them in Phase 6 |
| Test fragility | Use factories for test data; avoid hardcoded IDs |

---

## 8. Phase 4: Human Approval Workflow

### 8.1 Objective

Build the complete human-in-the-loop approval flow: when the Policy Engine returns `REQUIRE_HUMAN_APPROVAL`, the user is notified, can review, and can approve/reject/modify.

### 8.2 Duration

**1.5 weeks**

### 8.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 4.1 | `ApprovalRequest` model | Per `03-DATA-MODEL.md` Section 11.1 |
| 4.2 | `ApprovalDecision` model | Append-only decision record |
| 4.3 | Approval creation logic | Triggered by Policy Engine REQUIRE_HUMAN_APPROVAL |
| 4.4 | Approval decision API | Approve, reject, modify endpoints |
| 4.5 | Approval expiration job | Celery Beat task to expire stale approvals |
| 4.6 | WebSocket notifications | Real-time `approval.required` events |
| 4.7 | Email notifications | Async email via Celery |
| 4.8 | Human summary generation | Readable explanation of why approval is needed |
| 4.9 | Approval dashboard API | List pending approvals for user |
| 4.10 | Unit tests | Approval creation, decision processing, expiration |
| 4.11 | Integration test | Full approval flow within negotiation |

### 8.4 Acceptance Criteria

- [ ] When Policy Engine returns REQUIRE_HUMAN_APPROVAL, an ApprovalRequest is created.
- [ ] ApprovalRequest includes human-readable summary.
- [ ] User receives WebSocket notification in real-time.
- [ ] User receives email notification (async).
- [ ] User can approve via API.
- [ ] User can reject via API.
- [ ] Approval decisions are append-only (ApprovalDecision records).
- [ ] Approved proposals proceed to agreement generation (Phase 5).
- [ ] Rejected proposals trigger counter-offer or negotiation termination.
- [ ] Expired approvals are automatically marked EXPIRED by Celery Beat.
- [ ] Concurrent approval attempts are handled (first decision wins).
- [ ] All approval events produce AuditEvents.
- [ ] 2FA required for approvals involving amounts > €100.

### 8.5 API Endpoints

```text
GET    /api/v1/approvals/pending
GET    /api/v1/approvals/{id}/
POST   /api/v1/approvals/{id}/approve
POST   /api/v1/approvals/{id}/reject
POST   /api/v1/approvals/{id}/modify
```

### 8.6 Dependencies

- Phase 3 complete (Negotiation Simulator with Policy Engine integration).

### 8.7 Risks

| Risk | Mitigation |
|------|-----------|
| Approval fatigue (too many requests) | Configurable auto-approve limits in Constitution |
| Race condition on concurrent decisions | `select_for_update()` on ApprovalRequest |
| Email delivery failures | Retry logic; WebSocket as primary channel |

---

## 9. Phase 5: Audit Trail & Agreement

### 9.1 Objective

Build the complete audit trail (hash-chained, append-only) and the agreement generation/signing flow. This completes the MVP.

### 9.2 Duration

**2 weeks**

### 9.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 5.1 | `AuditEvent` model | Per `03-DATA-MODEL.md` Section 13.1 |
| 5.2 | Hash chain implementation | SHA-256 chain with previous_event_hash |
| 5.3 | Audit event creation service | `create_audit_event()` with Redis lock |
| 5.4 | PostgreSQL trigger | Prevent UPDATE/DELETE on AuditEvent |
| 5.5 | Hash chain verification job | Celery Beat daily integrity check |
| 5.6 | `Agreement` model | Per `03-DATA-MODEL.md` Section 12.1 |
| 5.7 | `AgreementSignature` model | Per `03-DATA-MODEL.md` Section 12.2 |
| 5.8 | Canonical JSON generation | Deterministic serialization |
| 5.9 | Agreement signing flow | HMAC-SHA256 signature + hash verification |
| 5.10 | Agreement export API | JSON, CSV export |
| 5.11 | Audit trail API | Query events by entity, by time range |
| 5.12 | Audit trail verification API | Verify hash chain integrity |
| 5.13 | Unit tests | Hash chain, canonical JSON, signing |
| 5.14 | Integration test | Full negotiation → approval → agreement → signing |

### 9.4 Acceptance Criteria

- [ ] Every state change in the system creates an AuditEvent.
- [ ] AuditEvents are hash-chained (each references previous hash).
- [ ] AuditEvents cannot be updated or deleted (DB trigger enforced).
- [ ] Hash chain verification detects tampering.
- [ ] Canonical JSON is deterministic (same data → same hash).
- [ ] Agreement signing produces HMAC-SHA256 signature.
- [ ] Hash mismatch on signing blocks the operation.
- [ ] User can export their full audit trail as JSON.
- [ ] User can export agreements as JSON and CSV.
- [ ] Full "AI Travel Negotiation" scenario produces complete audit trail.
- [ ] Audit trail matches expected sequence from `04-BUSINESS-FLOW.md` Section 4.3.

### 9.5 API Endpoints

```text
GET    /api/v1/audit/events
GET    /api/v1/audit/events/{id}/
GET    /api/v1/audit/entities/{entity_type}/{entity_id}/
POST   /api/v1/audit/verify

GET    /api/v1/agreements/
GET    /api/v1/agreements/{id}/
GET    /api/v1/agreements/{id}/canonical
GET    /api/v1/agreements/{id}/signature
POST   /api/v1/agreements/{id}/sign
POST   /api/v1/agreements/{id}/export
```

### 9.6 Dependencies

- Phase 4 complete (Human Approval Workflow).

### 9.7 Risks

| Risk | Mitigation |
|------|-----------|
| Hash chain performance under load | Redis lock; benchmark at 1000 events/second |
| Canonical JSON non-determinism | Strict serialization rules; property-based tests |
| Audit table growth | Plan partitioning strategy (not implemented in MVP) |

---

## 10. MVP Release Gate

### 10.1 MVP Definition

**Legatio v0.1** is complete when a user can:

1. ✅ Create an agent.
2. ✅ Create their Constitution.
3. ✅ Define rules (financial, privacy, negotiation).
4. ✅ Start a negotiation.
5. ✅ Connect to a simulated agent.
6. ✅ See proposals and counter-proposals.
7. ✅ Have each proposal evaluated by the Policy Engine.
8. ✅ See forbidden actions blocked automatically.
9. ✅ Receive approval requests for threshold-exceeding actions.
10. ✅ Approve or reject pending actions.
11. ✅ Generate a signed agreement.
12. ✅ View the complete audit trail.

### 10.2 MVP Exclusions

The following are explicitly **NOT** in the MVP:

- ❌ Blockchain anchoring.
- ❌ Real LLM-powered negotiation (simulated agents only).
- ❌ A2A protocol integration.
- ❌ MCP protocol integration.
- ❌ Agent reputation system.
- ❌ Marketplace.
- ❌ Enterprise features.
- ❌ Multi-user organizations.
- ❌ Payment processing.

### 10.3 MVP Demo Script

```text
1. User registers and creates account
2. User creates "My Travel Agent"
3. User builds Constitution:
   - Max transaction: €700
   - Auto-approve: €200
   - Phone number: NEVER
   - Email: ALLOWED
4. User activates Constitution
5. User starts negotiation: "Hotel Madrid, 5 nights"
6. Simulated Hotel Agent offers €820
7. Policy Engine: REQUIRE_APPROVAL (exceeds €200 auto-approve)
8. User rejects: "Too expensive"
9. User Agent counters: €650
10. Hotel Agent: "€680 + phone number"
11. Policy Engine: DENY (Rule #17: phone = NEVER)
12. User Agent counters: "€680 without phone"
13. Hotel Agent: "€700, no phone, 48h cancellation"
14. Policy Engine: REQUIRE_APPROVAL (exceeds €200)
15. User approves
16. Agreement generated: hash computed, signed
17. User views audit trail: 15 events, hash chain verified
18. DEMO COMPLETE
```

### 10.4 MVP Quality Gates

Before releasing MVP:

- [ ] All 3 use cases pass end-to-end.
- [ ] Test coverage > 80% (unit + integration).
- [ ] 0 critical or security bugs.
- [ ] API response time < 200ms (p95).
- [ ] Policy Engine evaluation < 50ms.
- [ ] WebSocket notifications delivered in < 100ms.
- [ ] Documentation complete (README, API docs, architecture docs).
- [ ] 5 beta users complete the demo successfully.
- [ ] NPS > 40 from beta users.

---

## 11. Phase 6: Real LLM Integration

### 11.1 Objective

Replace simulated agents with real LLM-powered negotiation. The Negotiation Engine (LLM) proposes; the Policy Engine (deterministic) still decides.

### 11.2 Duration

**2 weeks**

### 11.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 6.1 | LLM provider abstraction | Interface for OpenAI/Anthropic |
| 6.2 | OpenAI integration | GPT-4o for negotiation |
| 6.3 | Anthropic integration | Claude 3.5 Sonnet as fallback |
| 6.4 | Prompt templates | Structured prompts for negotiation |
| 6.5 | LLM output parser | Parse structured proposals from LLM response |
| 6.6 | LLM output validator | Pydantic validation + sanity checks |
| 6.7 | Circuit breaker | Handle LLM API failures gracefully |
| 6.8 | Cost tracking | Log token usage per negotiation |
| 6.9 | Replace simulated agents | LLM-powered User Agent |
| 6.10 | Keep simulated External Agents | For testing; LLM external agents optional |
| 6.11 | Unit tests | Parser, validator, circuit breaker |
| 6.12 | Integration test | Full negotiation with real LLM |

### 11.4 Acceptance Criteria

- [ ] LLM can parse natural language proposals into structured Proposals.
- [ ] LLM can generate context-aware counter-offers.
- [ ] LLM output is ALWAYS validated before use.
- [ ] LLM cannot bypass Policy Engine (architectural invariant).
- [ ] Circuit breaker opens after 5 consecutive failures.
- [ ] Fallback from OpenAI to Anthropic works.
- [ ] Token usage is logged per negotiation.
- [ ] Full "AI Travel Negotiation" works with LLM-powered User Agent.
- [ ] Policy Engine still blocks forbidden actions regardless of LLM output.

### 11.5 Dependencies

- Phase 5 complete (MVP released).

### 11.6 Risks

| Risk | Mitigation |
|------|-----------|
| LLM hallucination | Output validation; Policy Engine as safety net |
| API cost overrun | Token budget per negotiation; cost alerts |
| Prompt injection from external agents | Input sanitization; sandbox isolation |
| Latency spikes | Async processing; timeout handling |

---

## 12. Phase 7: A2A Protocol Integration

### 12.1 Objective

Implement the A2A (Agent-to-Agent) protocol gateway so Legatio can communicate with external agents that speak A2A.

### 12.2 Duration

**2 weeks**

### 12.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 7.1 | A2A protocol research | Study Google A2A specification |
| 7.2 | A2A message adapter | Translate A2A messages to internal format |
| 7.3 | A2A discovery endpoint | Allow A2A agents to discover Legatio |
| 7.4 | A2A task management | Handle long-running A2A tasks |
| 7.5 | A2A agent registration | External A2A agents can register |
| 7.6 | Protocol translation layer | A2A ↔ Legatio internal protocol |
| 7.7 | Integration tests | A2A agent connects and negotiates |

### 12.4 Acceptance Criteria

- [ ] External A2A agent can discover Legatio.
- [ ] External A2A agent can send proposals.
- [ ] Proposals are evaluated by Policy Engine.
- [ ] A2A task states map to NegotiationRoom states.
- [ ] Human intervention during A2A tasks works (approval flow).
- [ ] Protocol translation is lossless (no data lost).

### 12.5 Dependencies

- Phase 6 complete (Real LLM Integration).

### 12.6 Risks

| Risk | Mitigation |
|------|-----------|
| A2A spec changes | Abstract protocol behind interface; easy to update |
| Compatibility issues | Test against reference A2A implementation |

---

## 13. Phase 8: MCP Protocol Integration

### 13.1 Objective

Implement MCP (Model Context Protocol) adapter so Legatio agents can access external tools and data via MCP.

### 13.2 Duration

**1.5 weeks**

### 13.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 8.1 | MCP protocol research | Study MCP specification (July 2026 version) |
| 8.2 | MCP client adapter | Connect to MCP servers |
| 8.3 | MCP tool registration | Register available tools |
| 8.4 | MCP authorization layer | Apply Constitution rules to MCP tool access |
| 8.5 | MCP task integration | Handle MCP tasks within negotiations |
| 8.6 | Integration tests | Agent accesses tool via MCP with policy enforcement |

### 13.4 Acceptance Criteria

- [ ] Legatio agent can connect to MCP server.
- [ ] Tool access is subject to Policy Engine evaluation.
- [ ] Forbidden tools are blocked by Constitution rules.
- [ ] MCP authorization improvements (July 2026 spec) are supported.
- [ ] Tool access is logged in audit trail.

### 13.5 Dependencies

- Phase 7 complete (A2A Integration).

### 13.6 Risks

| Risk | Mitigation |
|------|-----------|
| MCP spec still evolving | Follow specification closely; abstract behind interface |
| Security of external tools | Sandbox tool execution; Policy Engine gates all access |

---

## 14. Phase 9: Agent Identity & Credentials

### 14.1 Objective

Build robust agent identity management: credentials, API keys, scopes, and authentication for external agents.

### 14.2 Duration

**1.5 weeks**

### 14.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 9.1 | `Credential` model | Per `03-DATA-MODEL.md` Section 7.2 |
| 9.2 | API key generation | Secure key generation with prefix |
| 9.3 | Key rotation | Revoke old, issue new |
| 9.4 | Scope-based access | Limit what each credential can do |
| 9.5 | HMAC request signing | External agents sign requests |
| 9.6 | Credential management UI | User can create/revoke credentials |
| 9.7 | Rate limiting per credential | Prevent abuse |
| 9.8 | Unit tests | Key generation, signing, verification |

### 14.4 Acceptance Criteria

- [ ] User can create API credentials for their agents.
- [ ] Full key is shown only once at creation.
- [ ] Only hash is stored (never the full key).
- [ ] Credentials can be revoked.
- [ ] Scopes limit what actions a credential can perform.
- [ ] HMAC-signed requests are verified.
- [ ] Rate limiting works per credential.
- [ ] Credential rotation is audited.

### 14.5 Dependencies

- Phase 8 complete (MCP Integration).

### 14.6 Risks

| Risk | Mitigation |
|------|-----------|
| Key leakage | Hash-only storage; short-lived keys; rotation |
| Scope escalation | Validate scopes on every request |

---

## 15. Phase 10: Reputation System

### 15.1 Objective

Build a basic reputation system for external agents based on their negotiation history.

### 15.2 Duration

**2 weeks**

### 15.3 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 10.1 | `AgentReputation` model | Score, totals, disputes |
| 10.2 | Reputation calculation | Based on successful/failed negotiations |
| 10.3 | Reputation display | Show score in negotiation UI |
| 10.4 | Dispute mechanism | User can flag problematic agents |
| 10.5 | Reputation-based warnings | Warn user before negotiating with low-rep agents |
| 10.6 | Unit tests | Score calculation, edge cases |

### 15.4 Acceptance Criteria

- [ ] Agent reputation is calculated after each negotiation.
- [ ] Reputation score is visible to users.
- [ ] Users can dispute an agent's behavior.
- [ ] Low-reputation agents trigger warnings.
- [ ] Reputation cannot be gamed (anti-manipulation measures).

### 15.5 Dependencies

- Phase 9 complete (Agent Identity).

### 15.6 Risks

| Risk | Mitigation |
|------|-----------|
| Reputation gaming | Require minimum interactions; weight by recency |
| Cold start problem | Default to neutral score; build history over time |

---

## 16. Future Horizons (Not Scheduled)

These are documented for awareness but are **not scheduled** and should not influence current development decisions.

### 16.1 Enterprise Legatio

- Organization model with hierarchical policies.
- Global → Department → Employee policy inheritance.
- SSO integration.
- Compliance dashboard.

### 16.2 Blockchain Anchoring

- Anchor agreement hashes to L2 (Polygon, Arbitrum).
- Only if explicit demand exists.
- Not before Phase 10.

### 16.3 Qualified Electronic Signature

- Integration with DocuSign, Firmaprofesional.
- eIDAS compliance.
- Requires legal research per jurisdiction.

### 16.4 Constitution Marketplace

- Community-shared constitution templates.
- Ratings and reviews.
- Monetization opportunity.

### 16.5 Multi-Agent Orchestration

- Multiple agents collaborating on a single negotiation.
- Agent teams with different specializations.
- Requires significant architecture extension.

### 16.6 Self-Hosted LLM

- Deploy Llama 3.1 70B for privacy-sensitive deployments.
- GPU infrastructure required.
- Consider for enterprise tier.

---

## 17. Dependency Graph

```text
Phase 0: Foundation
    │
    ▼
Phase 1: Policy Engine ◄─────────────────────────────────────┐
    │                                                        │
    ▼                                                        │
Phase 2: Constitution & Rules                                │
    │                                                        │
    ▼                                                        │
Phase 3: Negotiation Simulator                               │
    │                                                        │
    ▼                                                        │
Phase 4: Human Approval                                      │
    │                                                        │
    ▼                                                        │
Phase 5: Audit & Agreement                                   │
    │                                                        │
    ▼                                                        │
┌─────────────────┐                                          │
│  MVP RELEASE    │                                          │
│  (Legatio v0.1) │                                          │
└────────┬────────┘                                          │
         │                                                   │
         ▼                                                   │
Phase 6: Real LLM Integration                                │
         │                                                   │
         ▼                                                   │
Phase 7: A2A Integration                                     │
         │                                                   │
         ▼                                                   │
Phase 8: MCP Integration                                     │
         │                                                   │
         ▼                                                   │
Phase 9: Agent Identity                                      │
         │                                                   │
         ▼                                                   │
Phase 10: Reputation                                         │
         │                                                   │
         ▼                                                   │
┌─────────────────┐                                          │
│ Future Horizons │──────────────────────────────────────────┘
│ (Not Scheduled) │   (All future phases depend on stable core)
└─────────────────┘
```

**Critical path:** Phase 0 → 1 → 2 → 3 → 4 → 5 → MVP.

**No phase can be skipped.** Each phase builds on the previous one.

---

## 18. Risk Checkpoints

At the end of each phase, conduct a risk review:

### 18.1 Checkpoint Questions

1. Did we meet all acceptance criteria?
2. Are there any unresolved bugs?
3. Is test coverage adequate?
4. Are there any architectural concerns?
5. Is the next phase's scope still realistic?
6. Have any external dependencies changed?
7. Do we need to adjust the roadmap?

### 18.2 Go/No-Go Gates

| Gate | Location | Criteria |
|------|----------|----------|
| Gate 1 | After Phase 1 | Policy Engine is deterministic, tested, < 50ms |
| Gate 2 | After Phase 3 | Full negotiation flow works with simulated agents |
| Gate 3 | After Phase 5 | MVP demo script completes successfully |
| Gate 4 | After Phase 6 | LLM integration doesn't break Policy Engine guarantees |
| Gate 5 | After Phase 7 | A2A agents can negotiate without bypassing policies |

### 18.3 Abort Criteria

Stop and reassess if:

- Policy Engine cannot be made deterministic.
- Test coverage drops below 60%.
- More than 3 critical bugs remain unresolved after a phase.
- External protocol (A2A/MCP) changes fundamentally.
- Beta users cannot complete the demo without assistance.

---

## 19. Resource Estimates

### 19.1 Team Assumption

This roadmap assumes:

- **1 senior backend developer** (Django, PostgreSQL, Celery).
- **1 frontend developer** (Vue 3, TypeScript) — can be same person.
- **0.5 DevOps** (Docker, CI/CD) — can be same person.
- **0.25 Designer** (UI/UX for approval dashboard) — optional for MVP.

### 19.2 Time Estimates by Phase

| Phase | Backend | Frontend | DevOps | Total |
|-------|---------|----------|--------|-------|
| Phase 0 | 2 days | 2 days | 1 day | 1 week |
| Phase 1 | 8 days | 0 days | 0 days | 2 weeks |
| Phase 2 | 5 days | 2 days | 0 days | 1.5 weeks |
| Phase 3 | 7 days | 3 days | 0 days | 2 weeks |
| Phase 4 | 4 days | 3 days | 0 days | 1.5 weeks |
| Phase 5 | 7 days | 3 days | 0 days | 2 weeks |
| Phase 6 | 7 days | 3 days | 0 days | 2 weeks |
| Phase 7 | 8 days | 2 days | 0 days | 2 weeks |
| Phase 8 | 5 days | 2 days | 0 days | 1.5 weeks |
| Phase 9 | 5 days | 2 days | 0 days | 1.5 weeks |
| Phase 10 | 7 days | 3 days | 0 days | 2 weeks |

### 19.3 Infrastructure Cost Estimates (MVP)

| Resource | Provider | Estimated Cost/Month |
|----------|----------|---------------------|
| Compute (Django + Celery) | DigitalOcean / Hetzner | $20–40 |
| PostgreSQL (managed) | DigitalOcean / Supabase | $15–30 |
| Redis (managed) | DigitalOcean / Upstash | $10–20 |
| LLM API (OpenAI + Anthropic) | Pay-per-use | $50–100 |
| Domain + SSL | Cloudflare | $0–15 |
| Email (SendGrid) | Free tier → $15 | $0–15 |
| **Total MVP** | | **$95–220/month** |

### 19.4 Infrastructure Cost Estimates (Post-MVP)

| Resource | Estimated Cost/Month |
|----------|---------------------|
| Additional compute (A2A/MCP) | $50–100 |
| Increased LLM usage | $200–500 |
| Monitoring (Sentry, Grafana) | $25–50 |
| **Total Post-MVP** | **$370–870/month** |

---

## 20. Definition of Done (Global)

Every phase is considered "done" when ALL of the following are true:

### 20.1 Code Quality

- [ ] All acceptance criteria met.
- [ ] Unit test coverage ≥ 80% for new code.
- [ ] Integration tests pass.
- [ ] No critical or high-severity bugs open.
- [ ] Code reviewed by at least 1 other developer.
- [ ] Linting passes (ruff, black, mypy, eslint).
- [ ] Type hints present on all function signatures.

### 20.2 Documentation

- [ ] API documentation updated (Swagger/OpenAPI).
- [ ] README updated if setup changed.
- [ ] Architecture Decision Records updated if decisions changed.
- [ ] Code comments for complex logic.

### 20.3 Deployment

- [ ] Code merged to `main` branch.
- [ ] CI/CD pipeline passes.
- [ ] Deployed to staging environment.
- [ ] Staging smoke tests pass.

### 20.4 Audit & Security

- [ ] All state changes produce AuditEvents.
- [ ] No PII in logs.
- [ ] No secrets in code.
- [ ] Security review completed for new endpoints.

### 20.5 Demonstration

- [ ] Phase deliverable can be demonstrated.
- [ ] Demo script documented.
- [ ] Screenshots or recording captured for portfolio.

---

## 21. Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-19 | Mauro Vicens | Initial approved version. |

---

## Appendix A: Documentation Suite Index

| Document | File | Status |
|----------|------|--------|
| Product Requirements Document | `docs/01-PRD.md` | ✅ Approved |
| Architecture Decision Record | `docs/02-ARCHITECTURE.md` | ✅ Approved |
| Data Model Specification | `docs/03-DATA-MODEL.md` | ✅ Approved |
| Business Flow Specification | `docs/04-BUSINESS-FLOW.md` | ✅ Approved |
| Development Roadmap | `docs/05-ROADMAP.md` | ✅ Approved (this document) |

---

## Appendix B: Next Actions

With all 5 documents approved, the immediate next steps are:

1. **Create the repository** with the structure defined in `02-ARCHITECTURE.md`.
2. **Set up the development environment** (Phase 0, Deliverable 0.4).
3. **Configure CI/CD** (Phase 0, Deliverable 0.5).
4. **Begin Phase 1: Policy Engine** — the heart of Legatio.

The first line of production code should be:

```python
# services/policy_engine/evaluator.py

def evaluate_policy(
    action: ProposedAction,
    constitution_version: ConstitutionVersion,
) -> PolicyDecision:
    """
    Deterministic policy evaluation.
    No LLM. No randomness. Same input → same output.
    """
    ...
```

**Legatio AI begins with the Policy Engine. Everything else follows.**
