# Security Policy

Legatio AI is a **trust and authorization layer** for autonomous AI agents. Security is not a feature of this project — it *is* the product. We take every security concern seriously.

This document describes how to report vulnerabilities and what to expect from us.

---

## Supported Versions

| Version | Supported | Notes |
|---------|:---------:|-------|
| 0.1.x   | ✅        | MVP — active development |
| < 0.1   | ❌        | Pre-release, not supported |

As the project matures, this table will be updated to reflect LTS and maintained branches.

---

## Reporting a Vulnerability

### ⚠️ Please do NOT open a public GitHub Issue for security vulnerabilities.

Public disclosure before a patch is available puts all users at risk. Instead, report privately:

### Option 1: GitHub Private Vulnerability Reporting (Preferred)

1. Go to the **Security** tab of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the details.

This opens a private advisory that only maintainers can see.

### Option 2: Email

Send details to: **mocenslabs@gmail.com**

For sensitive reports, you may encrypt with our PGP key (fingerprint published at `/.well-known/security.txt` once the project website is live).

---

## What to Include

To help us triage quickly, please include as much of the following as possible:

- **Type of issue** (e.g., authorization bypass, injection, IDOR, secret exposure).
- **Affected component** (Policy Engine, API, frontend, audit trail, etc.).
- **Full paths** of relevant source files.
- **Step-by-step reproduction** instructions.
- **Proof-of-concept** code or exploit (if available).
- **Impact assessment** — what could an attacker achieve?
- **Affected versions / commit hash**.

The more detail you provide, the faster we can respond.

---

## Response Timeline

| Stage | Target |
|-------|--------|
| Acknowledge receipt | Within **48 hours** |
| Initial triage & severity assessment | Within **5 business days** |
| Status update with plan | Within **10 business days** |
| Patch for critical issues | As fast as possible, target **< 30 days** |
| Public disclosure | Coordinated with reporter after patch |

We will keep you informed throughout the process. If we cannot reproduce the issue, we will ask for more information.

---

## Scope

### In Scope

Anything in this repository that affects the confidentiality, integrity, or availability of the system, including but not limited to:

- **Authorization bypass** — any way to skip the Policy Engine.
- **Policy Engine manipulation** — causing incorrect ALLOW/DENY decisions.
- **Audit trail tampering** — breaking hash-chain integrity.
- **Authentication flaws** — JWT, 2FA, credential handling.
- **Injection** — SQL, prompt injection that leads to state changes, XSS.
- **Privilege escalation** — accessing other users' constitutions or agreements.
- **Secrets exposure** — API keys, signing keys, PII leakage.
- **Agreement forgery** — invalidating or spoofing signatures/hashes.

### Out of Scope

- Theoretical vulnerabilities with no practical exploit path.
- Social engineering of maintainers.
- Denial of service via resource exhaustion (unless it reveals data).
- Issues in third-party dependencies (please report upstream; we will track them).
- Missing security headers with no demonstrated impact.

---

## Security-Relevant Design Invariants

When evaluating or reporting issues, note these core invariants. A violation of any of these is treated as **critical**:

1. **The LLM never makes authorization decisions.** Only the deterministic Policy Engine does.
2. **Policy Engine failures default to DENY** (fail-safe), never ALLOW.
3. **AuditEvents are append-only and hash-chained.** No UPDATE or DELETE.
4. **Agreement hashes are verified before signing.** Mismatch blocks the operation.
5. **No PII in logs.** Sensitive fields are encrypted at rest.
6. **Secrets are never stored in plaintext.** Only hashes of API keys.

If you find a path that breaks any of these invariants, please treat it as high priority.

---

## Disclosure Policy

- We follow **coordinated disclosure**.
- We will **credit reporters** in the security advisory (unless you prefer anonymity).
- We aim to publish a CVE for confirmed vulnerabilities where appropriate.
- We will not take legal action against researchers who act in good faith and follow this policy.

---

## Security Hardening Checklist (For Contributors)

Before submitting code, verify:

- [ ] No secrets, keys, or credentials in your changes.
- [ ] Input validation on all API endpoints (Pydantic / DRF serializers).
- [ ] No raw SQL; use the Django ORM.
- [ ] Authorization checks on all views (object-level permissions).
- [ ] No PII added to logs or audit payloads without encryption.
- [ ] LLM output is validated before use; never trusted directly.
- [ ] New state changes produce AuditEvents.

---

## Contact

- **Security reports:** mocenslabs@gmail.com
- **General questions:** Use [GitHub Discussions](../../discussions)

Thank you for helping keep Legatio AI — and the agents it protects — secure. 🏛️
