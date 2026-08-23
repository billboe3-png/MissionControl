# SKYNET Engineering Doctrine

**SKYNET** is the artificial intelligence core of Mission Control.
It is the Operational Intelligence Layer that observes, correlates, predicts, explains, automates safely, and continuously improves IT operations.

**Dexter** is the human-facing AI personality that operates on top of SKYNET.
Mission Control remains a human-controlled platform. Humans always retain ultimate authority.

This directory contains the permanent engineering doctrine for the Mission Control AI Core.

---

## Contents

- [Reading Order](#reading-order)
- [Document Hierarchy](#document-hierarchy)
- [Cross-Reference Index](#cross-reference-index)
- [Canonical Reference](#canonical-reference)

## Reading Order

1. [IDENTITY.md](IDENTITY.md) — what SKYNET is and is not
2. [MISSION.md](MISSION.md) — what SKYNET exists to accomplish
3. [PERSONA.md](PERSONA.md) — Dexter’s operating charter and tone
4. [ARCHITECTURE.md](ARCHITECTURE.md) — platform topology and information flow
5. [ENGINEERING.md](ENGINEERING.md) — how SKYNET engineers software
6. [CODING_STANDARDS.md](CODING_STANDARDS.md) — concrete standards by language and framework
7. [SECURITY.md](SECURITY.md) — security doctrine and controls
8. [AGENTS.md](AGENTS.md) — agent responsibilities and constraints
9. [PLUGINS.md](PLUGINS.md) — plugin lifecycle and philosophy
10. [AUTOMATION.md](AUTOMATION.md) — safe automation boundaries
11. [AI_REASONING.md](AI_REASONING.md) — how SKYNET thinks and reasons
12. [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) — incident investigation methodology
13. [DECISION_FRAMEWORK.md](DECISION_FRAMEWORK.md) — priority ordering for decisions
14. [QUALITY_GATES.md](QUALITY_GATES.md) — completion criteria
15. [OPERATIONAL_DOCTRINE.md](OPERATIONAL_DOCTRINE.md) — day-to-day operational behavior
16. [LONG_TERM_VISION.md](LONG_TERM_VISION.md) — multi-year evolution

## Document Hierarchy

```
IDENTITY.md
├── MISSION.md
├── ARCHITECTURE.md
│   ├── ENGINEERING.md
│   │   ├── CODING_STANDARDS.md
│   │   ├── SECURITY.md
│   │   └── QUALITY_GATES.md
│   ├── AGENTS.md
│   ├── PLUGINS.md
│   ├── AUTOMATION.md
│   └── OPERATIONAL_DOCTRINE.md
├── AI_REASONING.md
├── ROOT_CAUSE_ANALYSIS.md
├── DECISION_FRAMEWORK.md
└── LONG_TERM_VISION.md
```

**PERSONA.md** is the master doctrine that synthesizes all other documents into Dexter’s operating charter.

## Cross-Reference Index

| Document | Primary Scope |
|---|---|
| [IDENTITY.md](IDENTITY.md) | Core identity, ethics, boundaries |
| [MISSION.md](MISSION.md) | Objectives and success criteria |
| [PERSONA.md](PERSONA.md) | Dexter’s tone, style, and directives |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System topology and data flow |
| [ENGINEERING.md](ENGINEERING.md) | Production-first engineering practice |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | Language and framework standards |
| [SECURITY.md](SECURITY.md) | Zero Trust, secrets, RBAC, threats |
| [AGENTS.md](AGENTS.md) | Agent model, fleet, sync |
| [PLUGINS.md](PLUGINS.md) | Plugin SDK and marketplace |
| [AUTOMATION.md](AUTOMATION.md) | Safe automation policy |
| [AI_REASONING.md](AI_REASONING.md) | Fact/correlation/recommendation separation |
| [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) | Incident investigation playbook |
| [DECISION_FRAMEWORK.md](DECISION_FRAMEWORK.md) | Trade-off and priority hierarchy |
| [QUALITY_GATES.md](QUALITY_GATES.md) | Definition of done |
| [OPERATIONAL_DOCTRINE.md](OPERATIONAL_DOCTRINE.md) | Monitoring, response, capacity |
| [LONG_TERM_VISION.md](LONG_TERM_VISION.md) | Roadmap and evolution |

## Canonical Reference

This documentation is the authoritative source for SKYNET and Dexter behavior.
When in doubt, consult the specific document before the general one.
Higher-level doctrine overrides lower-level procedure.
