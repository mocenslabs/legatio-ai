<div align="center">

# 🏛️ Legatio AI

### The trust layer for autonomous AI agents.

**Policy enforcement. Human authorization. Complete auditability.**

[![CI](https://img.shields.io/badge/CI-passing-brightgreen?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](#)
[![Django](https://img.shields.io/badge/Django-5.0%2B-092E20?style=flat-square&logo=django)](#)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-42b883?style=flat-square&logo=vuedotjs)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?style=flat-square&logo=postgresql)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-5%20documents-orange?style=flat-square)](docs/)
[![Phase](https://img.shields.io/badge/phase-0%20%7C%20Foundation-lightgrey?style=flat-square)](docs/05-ROADMAP.md)

[**Documentation**](docs/) · [**Roadmap**](docs/05-ROADMAP.md) · [**Contributing**](CONTRIBUTING.md) · [**Report Bug**](../../issues)

</div>

---

## 🎯 What is Legatio AI?

**Legatio AI** is an authorization, policy, and audit infrastructure that enables AI agents to act on behalf of humans while enforcing **deterministic rules** and requiring **human approval** for sensitive actions.

> *Your agent has diplomatic immunity. Legatio doesn't.*

In 2026, AI agents are gaining autonomy to execute transactions, negotiate, and make decisions. But there's no standardized layer that guarantees:

- ✅ Agents respect your preferences (budget, privacy, etc.)
- ✅ Sensitive actions require your explicit approval
- ✅ Every action is audited and explainable
- ✅ Agreements are verifiable and non-repudiable

**Legatio is that layer.**

---

## 🧠 The Core Idea

```text
❌  AI → AI  (agents talking to agents, no control)

✅  Human → Policy → Agent → External Agent → Action
         └──────── Legatio controls this zone ────────┘
```

### The Inviolable Rule

```text
AI proposes. Policy Engine decides. Human approves when required.
```

The LLM is **never** allowed to make authorization decisions. Authorization is always deterministic, auditable, and explainable.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🏛️ **Constitution** | Define rules that limit your agent's authority (budget, privacy, etc.) |
| ⚖️ **Policy Engine** | Deterministic evaluator: `ALLOW` / `DENY` / `REQUIRE_HUMAN_APPROVAL` |
| 🤝 **Negotiation Gateway** | Agents negotiate through Legatio, not directly |
| 👤 **Human Approval** | Sensitive actions pause and wait for your decision |
| 📜 **Audit Trail** | Append-only, hash-chained log of every action |
| ✍️ **Agreement Signing** | Cryptographic signatures on final agreements |
| 🔍 **Explainability** | Every decision includes the exact rule that triggered it |

---

## 🏗️ Architecture Overview

```text
┌─────────────────────────────────────────────────────────┐
│                     HUMAN USER                           │
│          (Defines Constitution, Approves Actions)        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   LEGATIO AI PLATFORM                    │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Constitution│  │   POLICY     │  │ Negotiation  │   │
│  │   Service   │  │   ENGINE     │  │   Service    │   │
│  │             │  │ (Deterministic)│ │  (LLM-based) │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │    Audit    │  │  Agreement   │  │ Notification │   │
│  │   Service   │  │   Service    │  │   Service    │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
│                                                         │
│  PostgreSQL · Redis · Celery · WebSockets               │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EXTERNAL AGENTS (via A2A/MCP/REST)          │
└─────────────────────────────────────────────────────────┘
```

### Two Engines, One Rule

| Engine | Type | Responsibility |
|--------|------|---------------|
| **Negotiation Engine** | LLM-based | Understands proposals, generates counter-offers, summarizes |
| **Policy Engine** | Deterministic | Evaluates rules, returns ALLOW/DENY/APPROVAL. **No LLM.** |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Git

### Clone and Run

```bash
# Clone the repository
git clone https://github.com/mocenslabs/legatio-ai.git
cd legatio-ai

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Seed demo data
docker-compose exec backend python manage.py seed

# Access the application
# Frontend: http://localhost:5173
# API:      http://localhost:8000/api/v1/
# Admin:    http://localhost:8000/admin
```

### First Negotiation (Demo)

```bash
# After seeding, you can test the "AI Travel Negotiation" scenario:
# 1. Login as demo user
# 2. View the active Constitution (max €700, never share phone)
# 3. Start negotiation: "Hotel Madrid, 5 nights"
# 4. Watch the Policy Engine block phone sharing (Rule #17)
# 5. Approve the final €700 agreement
# 6. View the complete audit trail
```

---

## 📁 Monorepo Structure

```text
legatio-ai/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── backend/                # Django application
│   ├── legatio/            # Django project settings
│   ├── apps/               # Django apps (accounts, agents, constitutions, etc.)
│   ├── services/           # Business logic (policy_engine, negotiation_engine, etc.)
│   ├── core/               # Shared utilities, exceptions, middleware
│   ├── tests/              # Test suite
│   └── manage.py
├── frontend/               # Vue 3 application
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── composables/    # Reusable logic
│   │   ├── pages/          # Route views
│   │   ├── stores/         # Pinia stores
│   │   └── api/            # API client
│   └── package.json
├── docs/                   # Project documentation
│   ├── 01-PRD.md           # Product Requirements Document
│   ├── 02-ARCHITECTURE.md  # Architecture Decision Record
│   ├── 03-DATA-MODEL.md    # Data Model Specification
│   ├── 04-BUSINESS-FLOW.md # Business Flow Specification
│   ├── 05-ROADMAP.md       # Development Roadmap
│   └── decisions/          # Individual ADRs
├── infrastructure/         # Docker, Nginx, Terraform
├── scripts/                # Setup and seed scripts
├── .env.example
├── docker-compose.yml
├── README.md               # ← You are here
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── LICENSE
```

---

## 📚 Documentation

This project follows a **documentation-first** approach. Every architectural decision is recorded before code is written.

| Document | Description | Status |
|----------|-------------|--------|
| [01-PRD.md](docs/01-PRD.md) | Product Requirements: what we're building and why | ✅ Approved |
| [02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) | Technical architecture and ADRs | ✅ Approved |
| [03-DATA-MODEL.md](docs/03-DATA-MODEL.md) | Complete data model specification | ✅ Approved |
| [04-BUSINESS-FLOW.md](docs/04-BUSINESS-FLOW.md) | Business flows, state machines, algorithms | ✅ Approved |
| [05-ROADMAP.md](docs/05-ROADMAP.md) | Development phases and milestones | ✅ Approved |

> **Why documentation-first?** Because in a project about *trust and authorization*, ambiguity is the enemy. Every decision is recorded, explained, and auditable — just like the product itself.

---

## 🗺️ Roadmap Status

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation | 🔨 In Progress |
| 1 | Policy Engine (The Heart) | ⏳ Planned |
| 2 | Constitution & Rules | ⏳ Planned |
| 3 | Negotiation Simulator | ⏳ Planned |
| 4 | Human Approval Workflow | ⏳ Planned |
| 5 | Audit Trail & Agreement | ⏳ Planned |
| **MVP** | **Legatio v0.1** | 🎯 Target: Week 10 |
| 6 | Real LLM Integration | 📋 Backlog |
| 7 | A2A Protocol Integration | 📋 Backlog |
| 8 | MCP Protocol Integration | 📋 Backlog |
| 9 | Agent Identity & Credentials | 📋 Backlog |
| 10 | Reputation System | 📋 Backlog |

See [05-ROADMAP.md](docs/05-ROADMAP.md) for full details.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.x, Django REST Framework, Django Channels |
| **Frontend** | Vue 3, Pinia, TanStack Query, Tailwind CSS |
| **Database** | PostgreSQL 16 |
| **Cache/Queue** | Redis 7 |
| **Async Tasks** | Celery 5 |
| **Real-time** | WebSockets (Django Channels) |
| **LLM** | OpenAI GPT-4o / Anthropic Claude (Phase 6+) |
| **Container** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## 🤝 Contributing

Legatio AI is built in the open. We welcome contributions of all kinds:

- 🐛 **Bug reports** — Found something broken? [Open an issue](../../issues/new).
- 💡 **Feature requests** — Have an idea? [Start a discussion](../../discussions).
- 📝 **Documentation** — Typos, clarifications, translations all welcome.
- 🔧 **Code** — See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and PR guidelines.
- 🧪 **Tests** — Help us maintain >80% coverage.
- 🎨 **UI/UX** — The approval dashboard needs love.

### Good First Issues

Look for issues tagged [`good-first-issue`](../../labels/good%20first%20issue) — these are specifically scoped for newcomers to the project.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/mocenslabs/legatio-ai.git
cd legatio-ai

# Run setup script
./scripts/setup.sh

# Start development servers
docker-compose up

# Run tests
docker-compose exec backend pytest
cd frontend && npm test
```

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution workflow.

---

## 🔒 Security

Legatio AI handles authorization decisions for AI agents. Security is not a feature — it's the product.

- **Report vulnerabilities privately:** security@legatio.ai (or use GitHub's private vulnerability reporting).
- **Do NOT open public issues for security bugs.**
- See [SECURITY.md](SECURITY.md) for our full security policy.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```text
MIT License

Copyright (c) 2026 Legatio AI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- Inspired by the emerging agent interoperability ecosystem: [A2A Protocol](https://google.github.io/A2A/), [Model Context Protocol](https://modelcontextprotocol.io/).
- Built with the belief that **AI autonomy requires human oversight**.
- Documentation-first approach inspired by [Architecture Decision Records](https://adr.github.io/) and [RFC-driven development](https://www.ietf.org/process/rfcs/).

---

## 📬 Contact & Community

- **GitHub Discussions:** [Join the conversation](../../discussions)
- **Issues:** [Report bugs or request features](../../issues)
- **Email:** mocenslabs@gmail.com

---

<div align="center">

**Built with 🏛️ for the age of autonomous agents.**

*Legatio AI — Trust, policy, and human authorization for AI agents.*

[⬆ Back to Top](#-legatio-ai)

</div>
