# Contributing to Legatio AI

First off, **thank you** for considering contributing to Legatio AI! 🏛️

Legatio is a trust and authorization layer for autonomous AI agents. Because the product itself is about **policies, transparency, and auditability**, we hold our development process to the same standard: every decision is documented, every change is traceable, and every contribution follows clear rules.

This document explains how to contribute effectively. Please read it before opening your first Pull Request.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Types of Contributions](#types-of-contributions)
3. [Getting Started](#getting-started)
4. [Development Setup](#development-setup)
5. [Project Structure](#project-structure)
6. [Coding Standards](#coding-standards)
7. [Commit Conventions](#commit-conventions)
8. [Branch Naming](#branch-naming)
9. [Pull Request Process](#pull-request-process)
10. [Review Process](#review-process)
11. [Testing Requirements](#testing-requirements)
12. [Documentation Requirements](#documentation-requirements)
13. [Issue Guidelines](#issue-guidelines)
14. [Security Vulnerabilities](#security-vulnerabilities)
15. [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to **mocenslabs@gmail.com**.

---

## Types of Contributions

We welcome many kinds of contributions, not just code:

| Type | Description | Label |
|------|-------------|-------|
| 🐛 **Bug Reports** | Found something broken? Tell us. | `bug` |
| 💡 **Feature Requests** | Have an idea? Start a discussion first. | `enhancement` |
| 📝 **Documentation** | Typos, clarifications, translations. | `documentation` |
| 🔧 **Code** | New features, bug fixes, refactors. | `code` |
| 🧪 **Tests** | Improve coverage, add edge cases. | `tests` |
| 🎨 **UI/UX** | Improve the approval dashboard, design system. | `design` |
| 🌐 **Translations** | Help us reach more developers. | `i18n` |

### Looking for a starting point?

Browse issues labeled:

- [`good-first-issue`](../../labels/good%20first%20issue) — scoped for newcomers.
- [`help-wanted`](../../labels/help%20wanted) — the core team needs help here.

---

## Getting Started

### Prerequisites

Before contributing, make sure you have installed:

- **Git** 2.30+
- **Docker** 24+ and **Docker Compose** v2
- **Python** 3.11+
- **Node.js** 20+ and **npm** 10+
- **make** (optional, for convenience commands)

### Fork and Clone

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/mocenslabs/legatio-ai.git
cd legatio-ai

# 2. Add the upstream remote
git remote add upstream https://github.com/mocenslabs/legatio-ai.git

# 3. Verify remotes
git remote -v
# origin    https://github.com/mocenslabs/legatio-ai.git (fetch)
# upstream  https://github.com/mocenslabs/legatio-ai.git (fetch)
```

---

## Development Setup

### Automated Setup

```bash
# Run the setup script (creates .env, installs dependencies, starts services)
./scripts/setup.sh
```

### Manual Setup

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start infrastructure (PostgreSQL, Redis)
docker-compose up -d postgres redis

# 3. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py seed
cd ..

# 4. Frontend setup
cd frontend
npm install
cd ..

# 5. Start development servers
docker-compose up
```

### Verify Installation

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# Linting
make lint
```

If all three pass, you're ready to contribute. 🎉

---

## Project Structure

Legatio is a **monorepo**. Familiarize yourself with the layout:

```text
legatio-ai/
├── backend/                # Django application
│   ├── apps/               # Django apps (domain modules)
│   ├── services/           # Business logic (policy_engine, etc.)
│   ├── core/               # Shared utilities
│   └── tests/
├── frontend/               # Vue 3 application
│   ├── src/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── pages/
│   │   └── stores/
├── docs/                   # Project documentation
│   ├── 01-PRD.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-DATA-MODEL.md
│   ├── 04-BUSINESS-FLOW.md
│   ├── 05-ROADMAP.md
│   └── decisions/          # Individual ADRs
├── infrastructure/         # Docker, Nginx configs
└── scripts/                # Setup and utility scripts
```

### Where does my code go?

| Change type | Location |
|-------------|----------|
| New Django model | `backend/apps/<app>/models.py` |
| Business logic | `backend/services/<service>/` |
| API endpoint | `backend/apps/<app>/views.py` + `urls.py` |
| Vue component | `frontend/src/components/` |
| Reusable logic | `frontend/src/composables/` |
| Documentation | `docs/` |
| Architectural decision | `docs/decisions/ADR-XXX.md` |

---

## Coding Standards

### Python (Backend)

We enforce style automatically. **Do not fight the formatter.**

| Tool | Purpose |
|------|---------|
| `ruff` | Linting and import sorting |
| `mypy` | Static type checking (strict) |
| `pytest` | Testing framework |

**Rules:**

- ✅ Type hints on **all** function signatures.
- ✅ Docstrings (Google style) on all public functions.
- ✅ Absolute imports only.
- ✅ `snake_case` for functions/variables, `PascalCase` for classes.
- ❌ No `print()` in production code. Use `logging`.
- ❌ No bare `except:`. Always catch specific exceptions.
- ❌ No business logic in views. Use service layer.

**Example:**

```python
def evaluate_policy(
    action: ProposedAction,
    constitution_version: ConstitutionVersion,
) -> PolicyDecision:
    """Evaluate a proposed action against a constitution.

    Args:
        action: The proposed action to evaluate.
        constitution_version: The active constitution version.

    Returns:
        A PolicyDecision with outcome ALLOW, DENY, or REQUIRE_HUMAN_APPROVAL.
    """
    ...
```

**Before committing, run:**

```bash
cd backend
ruff check --fix .
mypy .
```

### TypeScript (Frontend)

| Tool | Purpose |
|------|---------|
| `ESLint` | Linting |
| `Prettier` | Formatting |
| `TypeScript` | Type checking (strict mode) |
| `Vitest` | Unit testing |

**Rules:**

- ✅ Strict mode enabled. **No `any`.**
- ✅ Composition API with `<script setup>`.
- ✅ `PascalCase` for components, `camelCase` for functions.
- ✅ `kebab-case` for file names.
- ❌ No inline styles. Use Tailwind classes.

**Example:**

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePolicyDecision } from '@/composables/usePolicyDecision';

const props = defineProps<{
  proposalId: string;
}>();

const { decision, isLoading } = usePolicyDecision(props.proposalId);

const isDenied = computed(() => decision.value?.outcome === 'DENY');
</script>
```

**Before committing, run:**

```bash
cd frontend
npm run lint
npm run type-check
npm run format
```

### Pre-commit Hooks

We use `pre-commit` to automate checks. Install once:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit` and block commits that fail checks.

---

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/). This is **mandatory**, not optional. It powers our changelog and makes history readable.

### Format

```text
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Usage |
|------|-------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting; no code logic change |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `revert` | Reverts a previous commit |

### Scopes

Use the area of the codebase affected:

```text
policy-engine, constitution, negotiation, approval, agreement,
audit, frontend, api, infra, docs
```

### Examples

✅ **Good:**

```text
feat(policy-engine): add DENY priority over ALLOW rules

DENY rules are now evaluated first and short-circuit the
evaluation loop. This ensures forbidden actions are blocked
immediately without evaluating remaining rules.

Closes #42
```

```text
fix(approval): prevent race condition on concurrent decisions

Use select_for_update() when processing approval decisions
to ensure only the first decision is applied.

Fixes #87
```

```text
docs(data-model): clarify ConstitutionVersion immutability
```

❌ **Bad:**

```text
update code
fix stuff
wip
asdfasdf
```

### Rules

- Subject line ≤ 72 characters.
- Imperative mood: "add", not "added" or "adds".
- No period at the end of the subject.
- Reference issues in the footer: `Closes #123`, `Fixes #456`.
- Breaking changes: add `!` after type, e.g. `feat(api)!: change response format`.

---

## Branch Naming

Create a new branch for every change. **Never commit directly to `main`.**

### Format

```text
<type>/<ticket>-<short-description>
```

### Examples

```text
feat/leg-42-policy-engine-deny-priority
fix/leg-87-approval-race-condition
docs/leg-15-clarify-immutability
test/leg-99-policy-engine-edge-cases
```

### Rules

- Lowercase only.
- Hyphens between words (no underscores or spaces).
- Include issue number if one exists.
- Keep it short but descriptive.

---

## Pull Request Process

### Before You Start

1. **Check existing issues and PRs.** Your idea may already be in progress.
2. **Open an issue first** for significant changes (new features, architectural changes). Discuss before coding.
3. **Small PRs get merged faster.** Aim for < 400 lines changed.

### Step-by-Step

```bash
# 1. Sync your fork with upstream
git checkout main
git pull upstream main
git push origin main

# 2. Create a feature branch
git checkout -b feat/leg-42-policy-engine-deny-priority

# 3. Make your changes (with tests!)

# 4. Run the full check suite
make check    # lint + type-check + tests

# 5. Commit with conventional messages
git add .
git commit -m "feat(policy-engine): add DENY priority over ALLOW rules"

# 6. Push to your fork
git push origin feat/leg-42-policy-engine-deny-priority
```

### PR Template

When you open a PR, fill in the template completely:

```markdown
## Summary
<!-- One paragraph: what does this PR do and why? -->

## Related Issue
Closes #

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor
- [ ] Test

## Checklist
- [ ] My code follows the coding standards
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated documentation if needed
- [ ] My commits follow Conventional Commits
- [ ] I have run `make check` locally

## Screenshots (if UI change)

## Additional Notes
```

### PR Requirements

A PR **cannot be merged** until:

- [ ] All CI checks pass.
- [ ] At least 1 approval from a maintainer.
- [ ] No unresolved review comments.
- [ ] Test coverage does not decrease.
- [ ] Documentation updated if behavior changed.

---

## Review Process

### What reviewers look for

1. **Correctness** — Does it solve the problem?
2. **Architecture** — Does it respect the separation of Policy Engine / Negotiation Engine?
3. **Tests** — Are edge cases covered?
4. **Readability** — Will someone understand this in 6 months?
5. **Security** — Does it introduce vulnerabilities?

### Review SLA

- We aim to review PRs within **48 hours**.
- If your PR is urgent, mention it in the PR description.

### Receiving feedback

- Feedback is about the code, not the person.
- Ask questions if something is unclear.
- Push back respectfully if you disagree — we want the best outcome.

---

## Testing Requirements

### Coverage Targets

| Area | Minimum Coverage |
|------|-----------------|
| Policy Engine | **100%** |
| Services | 85% |
| API views | 80% |
| Frontend composables | 80% |
| Overall | 80% |

### What to test

- ✅ Happy path.
- ✅ Edge cases (empty rules, malformed input).
- ✅ Error handling (fail-safe behavior).
- ✅ State machine transitions.
- ✅ Concurrency (where applicable).

### Running tests

```bash
# Backend
cd backend
pytest                          # all tests
pytest tests/unit/              # unit only
pytest --cov=apps --cov=services  # with coverage

# Frontend
cd frontend
npm test
npm run test:coverage
```

### Policy Engine tests are special

The Policy Engine is the heart of Legatio. Any change to it **must** include:

- Tests proving determinism (same input → same output).
- Tests for DENY priority.
- Tests for fail-safe behavior (exception → DENY).

---

## Documentation Requirements

### When to update docs

Update documentation when your change affects:

- API endpoints → update OpenAPI/Swagger.
- Data model → update `docs/03-DATA-MODEL.md`.
- Business flow → update `docs/04-BUSINESS-FLOW.md`.
- Architecture → create a new ADR in `docs/decisions/`.

### Architecture Decision Records

If your change introduces a **significant architectural decision**, write an ADR:

```text
docs/decisions/ADR-0XX-short-title.md
```

Use the template in `docs/decisions/TEMPLATE.md`. ADRs are immutable once approved; changes require a new ADR.

---

## Issue Guidelines

### Bug Reports

Use the [Bug Report template](../../.github/ISSUE_TEMPLATE/bug_report.md). Include:

- Steps to reproduce.
- Expected vs. actual behavior.
- Environment (OS, Python/Node versions).
- Relevant logs or screenshots.

### Feature Requests

Use the [Feature Request template](../../.github/ISSUE_TEMPLATE/feature_request.md). Include:

- The problem you're trying to solve.
- Proposed solution (if any).
- Alternatives considered.

### Questions

Use [GitHub Discussions](../../discussions) for questions, not Issues.

---

## Security Vulnerabilities

**Do NOT open a public Issue for security vulnerabilities.**

Report privately via:

- Email: **mocenslabs@gmail.com**
- GitHub's private vulnerability reporting.

See [SECURITY.md](SECURITY.md) for details.

---

## Community

- 💬 **Discussions:** [GitHub Discussions](../../discussions)
- 🐛 **Issues:** [GitHub Issues](../../issues)
- 📧 **Email:** mocenslabs@gmail.com

### Recognition

All contributors are recognized in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file. We use the [all-contributors](https://allcontributors.org/) specification.

---

## Thank You! 🏛️

Every contribution — a typo fix, a test, a feature — makes Legatio better. Thank you for helping build the trust layer for autonomous AI agents.

**Now go forth and contribute!**
