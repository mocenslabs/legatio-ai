# Maintainer Availability & Collaboration Model

> **Last updated:** August 20, 2026

---

## 🕤 Maintainer Availability

The primary maintainer of Legatio AI operates on a **limited but consistent schedule**:

```text
📅 Monday through Friday
🕤 9:30 AM – 11:00 AM (GMT-3 / Argentina Time)
```

**Total: ~7.5 hours per week.**

This is the window during which the maintainer will:

- Review and merge Pull Requests
- Respond to Issues and Discussions
- Provide architectural guidance
- Update documentation
- Coordinate with contributors

---

## 🔄 Async-First Collaboration

Legatio AI was designed from day one with **asynchronous collaboration** in mind. The project does not depend on synchronous meetings, real-time pair programming, or immediate responses.

### What this means for contributors:

✅ **You can contribute at any time.** Work when it suits you. The project lives on GitHub, not in real-time chat.

✅ **No pressure for instant responses.** The maintainer reviews contributions during their availability window. Expect responses within 1-2 business days.

✅ **Clear documentation.** All architectural decisions, data models, and business flows are documented in `/docs`. You can understand the project without needing to ask questions first.

✅ **Well-defined issues.** Issues are tagged with `good-first-issue`, `help-wanted`, and difficulty levels. Pick what matches your skills and availability.

✅ **Sustainable pace.** This project values quality over speed. There are no artificial deadlines or crunch periods.

---

## 📬 Response Time Expectations

| Type | Expected Response Time |
|------|------------------------|
| Pull Request review | 1-2 business days |
| Issue response | 1-2 business days |
| Discussion participation | 2-3 business days |
| Urgent security issues | Same day (if within availability window) |

If your contribution requires immediate attention (e.g., a critical bug fix), please mark it clearly in the PR/Issue title with `[URGENT]`.

---

## 🎯 How to Contribute Effectively

Given the async model, here's how to make the most of your contributions:

### 1. Read the documentation first

Before opening an Issue or starting work, review:

- [`docs/01-PRD.md`](docs/01-PRD.md) — What we're building and why
- [`docs/02-ARCHITECTURE.md`](docs/02-ARCHITECTURE.md) — Technical decisions and ADRs
- [`docs/03-DATA-MODEL.md`](docs/03-DATA-MODEL.md) — Database schema
- [`docs/04-BUSINESS-FLOW.md`](docs/04-BUSINESS-FLOW.md) — How the system behaves
- [`docs/05-ROADMAP.md`](docs/05-ROADMAP.md) — What's planned and what's not

### 2. Comment before you code

If you want to work on an Issue, comment on it first:

```text
"I'd like to work on this. Planning to approach it by [brief description].
Does that align with the project direction?"
```

This prevents duplicate work and ensures alignment before you invest time.

### 3. Small, focused PRs

Pull Requests under 400 lines get reviewed and merged faster. Break large features into smaller, reviewable chunks.

### 4. Be explicit about questions

If you need guidance, be specific:

❌ "How should I implement this?"

✅ "I'm implementing the Policy Engine evaluation. Should DENY rules short-circuit
immediately, or should I evaluate all rules and return the highest priority result?
The docs suggest short-circuiting, but I want to confirm."

---

## 🧭 Current Project Phase

Legatio AI is currently in **Phase 0: Foundation**.

See [`docs/05-ROADMAP.md`](docs/05-ROADMAP.md) for the complete phase breakdown.

**Priority areas for contributions right now:**

- [ ] Backend scaffolding (Django project structure)
- [ ] Frontend scaffolding (Vue 3 project structure)
- [ ] Docker Compose configuration
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Test suite setup
- [ ] Documentation improvements

---

## 🤝 Collaboration Philosophy

### Sustainable over fast

This project is built at a sustainable pace. There is no investor pressure, no launch deadline, no crunch. We prioritize:

- **Code quality** over speed
- **Documentation** over assumptions
- **Community health** over feature velocity
- **Maintainer well-being** over unsustainable commitments

### Transparent communication

If the maintainer needs to reduce availability further (due to personal circumstances, health, or professional obligations), this document will be updated. Contributors will be notified via:

- GitHub Discussions announcement
- Telegram channel post
- README notice (if extended absence)

### No heroics required

You don't need to be a senior developer to contribute. You don't need to work full-time. You don't need to be available during the maintainer's window. Contribute when you can, at the level you're comfortable with.

---

## 📞 Contact & Coordination

### Primary channels (async):

- **GitHub Issues** — Bug reports, feature requests
- **GitHub Discussions** — Questions, ideas, community conversation
- **Pull Requests** — Code contributions

### Secondary channel (announcements):

- **Telegram channel** — Project updates, milestone announcements
  - Join: [[LINK]](https://t.me/+rAUUypI4EcgyZmUx)
  - Note: This is a low-traffic announcement channel, not a support chat.

### Not available:

- ❌ Synchronous meetings (no Zoom, no Google Meet)
- ❌ Real-time pair programming
- ❌ Phone calls
- ❌ WhatsApp (to protect maintainer privacy)

---

## 🙏 Acknowledgment

Thank you for understanding and respecting this collaboration model. Legatio AI is built in the open, at a sustainable pace, with the belief that **quality and community health matter more than velocity**.

If this model works for you, welcome aboard. 🏛️

If you need a project with faster response times or synchronous collaboration, we understand — and we wish you well.

---

**Maintainer:** [Mauro Vicens / @mocenslabs]  
**Timezone:** GMT-3 (Argentina)  
**Availability:** Mon-Fri, 9:30-11:00 AM  
**Last updated:** August 20, 2026
