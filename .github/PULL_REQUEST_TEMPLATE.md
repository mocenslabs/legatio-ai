<!--
Thank you for contributing to Legatio AI! 🏛️
Please fill in this template completely. Incomplete PRs may be closed.
Remember: Conventional Commits + passing checks + 1 approval are required to merge.
-->

## Summary

<!-- One or two paragraphs: what does this PR do and why? -->

## Related Issue

<!-- Use "Closes #123" or "Fixes #123" to auto-link. -->

Closes #

## Type of Change

<!-- Check all that apply. -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that causes existing functionality to change)
- [ ] 📝 Documentation update
- [ ] 🔧 Refactor (no functional change)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test additions or corrections
- [ ] 🏗️ Build / CI / dependencies
- [ ] 🎨 UI / styling

## Affected Area

<!-- Which part of the monorepo does this touch? -->

- [ ] Backend — Policy Engine
- [ ] Backend — Constitution / Rules
- [ ] Backend — Negotiation
- [ ] Backend — Approval
- [ ] Backend — Agreement
- [ ] Backend — Audit
- [ ] Backend — API / views
- [ ] Frontend — Components
- [ ] Frontend — Stores / state
- [ ] Infrastructure / Docker
- [ ] Documentation

## Description of Changes

<!-- Detailed explanation of what changed and how. Include design decisions. -->

## How Has This Been Tested?

<!-- Describe the tests you ran. Include commands. -->

```bash
# Example:
cd backend && pytest tests/unit/test_policy_engine.py
cd frontend && npm test
```

- [ ] Unit tests added / updated
- [ ] Integration tests added / updated
- [ ] Manually tested locally

## Policy Engine Safety

<!-- REQUIRED if your change touches the Policy Engine or authorization flow. -->

- [ ] My change preserves determinism (same input → same output).
- [ ] DENY rules still take priority.
- [ ] Fail-safe behavior preserved (errors → DENY, never ALLOW).
- [ ] No LLM introduced into authorization decisions.
- [ ] Not applicable — this PR does not touch authorization logic.

## Security Checklist

- [ ] No secrets, keys, or credentials included.
- [ ] Input validation present on any new endpoints.
- [ ] No PII added to logs or audit payloads.
- [ ] Object-level permissions enforced on new views.

## Checklist

- [ ] My code follows the [coding standards](../CONTRIBUTING.md#coding-standards).
- [ ] My commits follow [Conventional Commits](../CONTRIBUTING.md#commit-conventions).
- [ ] I have run `make check` locally and it passes.
- [ ] All new and existing tests pass.
- [ ] Test coverage has not decreased.
- [ ] I have updated documentation if behavior changed.
- [ ] I have added an ADR if this introduces an architectural decision.
- [ ] I have self-reviewed my own code.

## Screenshots / Recordings

<!-- If this is a UI change, add before/after screenshots. -->

| Before | After |
|--------|-------|
|        |       |

## Additional Notes

<!-- Anything reviewers should know? Open questions? Follow-ups? -->
