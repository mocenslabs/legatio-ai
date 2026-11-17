<div align="center">

# Legatio AI

### The trust layer for autonomous AI agents

**Deterministic policy. Human authorization. Cryptographic audit.**

[![CI](https://img.shields.io/badge/CI-passing-brightgreen?style=flat-square)](#supporting-evidence)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](#)
[![Django](https://img.shields.io/badge/Django-5-092E20?style=flat-square&logo=django)](#)
[![Vue](https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vuedotjs)](#)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square)](LICENSE)
[![Phase](https://img.shields.io/badge/status-MVP-orange?style=flat-square)](docs/05-ROADMAP.md)

[Documentation](docs/) · [Architecture](docs/02-ARCHITECTURE.md) · [MVP demo script](docs/MVP_DEMO.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Project overview

**Legatio AI** is an authorization, policy, and audit layer for AI agents that act on behalf of people.

### The problem

As agents gain autonomy (renew subscriptions, book travel, negotiating with other agents), they can take **irreversible or high-cost actions** without a clear, enforceable boundary. Today that often depends on:

- Prompt text the model may ignore under pressure
- Ad-hoc "please confirm" UIs with no durable trail
- Logs that are not cryptographically bound to what was actually decided

That is an **AI safety and control** problem: unauthorized spend, privacy leaks, or "the agent agreed to something I never approved."

### What Legatio does

Legatio sits **between** the human, their agent, and external counterparties:

```text
Human  →  Constitution (rules)  →  Agent  →  Negotiation  →  External agent
              │                        │
              └──── Policy Engine ─────┘
                       │
              ALLOW / DENY / REQUIRE_HUMAN_APPROVAL
                       │
              Audit trail + signed agreement
```

Users define a **Constitution** (deterministic rules: budget caps, sensitive data, auto-renew limits). Every proposal is evaluated by a **Policy Engine that does not use an LLM**. Risky outcomes pause for **human approval**. Final outcomes can be **hashed and signed**; events form an **append-only audit chain**.

> Core rule: **AI proposes. Policy decides. Humans approve when required.**

---

## Safety approach

How Legatio reduces **unauthorized or irreversible** AI actions:

### 1. Separation of proposal vs authorization

| Component | Role | May authorize? |
|-----------|------|----------------|
| Negotiation / LLM path | Interpret offers, draft counter-offers, summarize | **No** |
| **Policy Engine** (pure Python) | Evaluate rules → `ALLOW` / `DENY` / `REQUIRE_HUMAN_APPROVAL` | **Yes (only)** |
| Human | Explicit approve / reject when policy requires it | **Yes** |

The model **never** chooses authorization. That decision is code + rules + optional human confirmation.

### 2. Fail-closed evaluation

- On evaluation failure or unexpected conditions, the system defaults to **DENY** or **REQUIRE_HUMAN_APPROVAL**, not silent `ALLOW`.
- **DENY** takes priority over permissive outcomes.
- Sensitive requests (e.g. data the user forbids) can be hard-denied without a negotiation "retry until yes."

### 3. Human-in-the-loop for high-risk actions

When rules mark a proposal as needing approval (price band, renewals, edge cases), the flow **stops** until a human decides. Agents cannot complete that path alone.

### 4. Cryptographic accountability

- **Agreements**: canonical payload → hash → signature (server signing key).
- **Audit**: append-only events with **hash chaining** so tampering is detectable.
- **Secrets**: TOTP and similar secrets encrypted at rest (Fernet) when configured.

### 5. Explainability

Each policy decision can point to the **rule that fired**, so operators and users can answer *why* something was allowed, denied, or escalated—without treating a free-form model explanation as the authority.

### What this is *not* (by design)

- Not a general "aligned LLM." Safety is enforced **outside** the model.
- Not a full legal eIDAS / QES product in the MVP.
- Not a guarantee against a fully malicious external agent that lies in free text; the controlled surface is **structured proposals + policy + human gates + audit**.

---

## Supporting evidence

| Evidence | Where |
|----------|--------|
| Product and problem definition | [docs/01-PRD.md](docs/01-PRD.md) |
| Architecture and safety ADRs (deterministic policy, fail-closed, audit) | [docs/02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) |
| Data model | [docs/03-DATA-MODEL.md](docs/03-DATA-MODEL.md) |
| End-to-end business flow | [docs/04-BUSINESS-FLOW.md](docs/04-BUSINESS-FLOW.md) |
| MVP demo steps (API + seed) | [docs/MVP_DEMO.md](docs/MVP_DEMO.md) |
| Automated tests | `backend/tests/` — unit, integration, e2e (CI: pytest + coverage gate ≥ 80%) |
| Continuous integration | GitHub Actions: backend lint (ruff, mypy), tests, frontend eslint + type-check, Docker builds |
| OpenAPI (local) | `/api/v1/docs/` (Swagger) when the backend is running |

### Demo video

Public walkthrough of the MVP (policy, approval, audit):

```text
https://youtu.be/Hpfr-EVDFKE
https://youtu.be/bUAs-zTX7cs
```


### Suggested verification for reviewers

```bash
# From repository root
cp .env.example .env   # configure secrets — see comments in the file
./scripts/setup.sh

# Backend tests (Docker)
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend \
  pytest -q --tb=line
```

Safety-relevant behaviors covered by design and tests include: policy `DENY` / approval-required paths, agreement verification, audit hash-chain integrity, and auth / 2FA secret encryption at rest.

---

## Limitations

Honest scope for reviewers:

1. **MVP surface** — Focused flows (subscription-style / travel-style negotiations with structured proposals), not every industry protocol.
2. **External agents** — Counterparties are assumed to use the expected structured interface; adversarial multi-agent games are out of scope for v0.1.
3. **LLM quality** — Negotiation *wording* still depends on the model; **authorization** does not. Hallucinated offers are constrained by policy, not by trusting the model to self-censor.
4. **Identity and billing** — Organization/roles and plan models are foundational; production payment provider and full multi-tenant hardening are ongoing.
5. **Operations** — Primary path is Docker Compose locally; managed production deployment is the next step, not a finished multi-region SLA.
6. **Signatures** — Server-side cryptographic signatures and hash chains in PostgreSQL; not qualified electronic signatures or public blockchain anchoring in the MVP.
7. **UX** — Web UI is usable for demos (getting-started guide, empty states, English/Spanish); enterprise admin polish is incomplete.

---

## Quick start

### Requirements

- Docker 24+ and Docker Compose v2
- Optional: Python 3.12+, Node 20+ for host-side tooling

### Run

```bash
git clone https://github.com/mocenslabs/legatio-ai.git
cd legatio-ai
cp .env.example .env
# Set DJANGO_SECRET_KEY, JWT secrets, ENCRYPTION_KEY (Fernet), SERVER_SIGNING_KEY

./scripts/setup.sh
# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
# API docs: http://localhost:8000/api/v1/docs/
```

Seed data and a step-by-step script: [docs/MVP_DEMO.md](docs/MVP_DEMO.md).

---

## Repository layout

```text
backend/           Django API, Policy Engine, audit, agreements
frontend/          Vue 3 + TypeScript UI
docs/              PRD, architecture, data model, flows, roadmap
infrastructure/    Docker Compose, nginx, terraform stubs
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

## Contact

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md)

*Built for controllable agent autonomy: policy and audit as safety infrastructure, not prompts alone.*
