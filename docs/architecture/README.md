# Mission Control Architecture Documentation

This is the official architecture governance documentation for Mission Control v3. These documents define how Mission Control is built, extended, and maintained.

## Document Index

| Document | Description |
|----------|-------------|
| [MissionControl-v3-Roadmap.md](MissionControl-v3-Roadmap.md) | Vision, mission, platform goals, and long-term roadmap |
| [Core-Platform.md](Core-Platform.md) | What belongs inside the Mission Control core |
| [Plugin-Architecture.md](Plugin-Architecture.md) | Plugin system design and execution targets |
| [Plugin-SDK.md](Plugin-SDK.md) | SDK interfaces, extension points, and API |
| [Plugin-Governance.md](Plugin-Governance.md) | Plugin policy, compatibility, and lifecycle rules |
| [Plugin-Marketplace.md](Plugin-Marketplace.md) | Marketplace categories, certification, and publishing |
| [Marketplace-Governance.md](Marketplace-Governance.md) | Marketplace submission, review, and lifecycle rules |
| [Coding-Standards.md](Coding-Standards.md) | Python, TypeScript, naming, and folder conventions |
| [API-Standards.md](API-Standards.md) | REST API design rules and versioning |
| [Testing-Standards.md](Testing-Standards.md) | Test categories, coverage targets, and quality gates |
| [Security-Standards.md](Security-Standards.md) | Authentication, authorization, encryption, and isolation |
| [Release-Process.md](Release-Process.md) | Release lifecycle, versioning, and hotfix process |
| [Architecture-Decisions.md](Architecture-Decisions.md) | Key architectural decisions (ADRs) |
| [Architecture-Principles.md](Architecture-Principles.md) | Foundational design principles and anti-patterns |
| [Future-Roadmap.md](Future-Roadmap.md) | Version 3.x, 4.x, and 5.x planned features |

## Quick Start

- **New developers**: Start with [Core-Platform.md](Core-Platform.md) and [Coding-Standards.md](Coding-Standards.md)
- **Plugin developers**: Start with [Plugin-SDK.md](Plugin-SDK.md) and [Plugin-Architecture.md](Plugin-Architecture.md)
- **Architecture review**: Start with [MissionControl-v3-Roadmap.md](MissionControl-v3-Roadmap.md), [Architecture-Principles.md](Architecture-Principles.md), and [Architecture-Decisions.md](Architecture-Decisions.md)
- **Marketplace operations**: Start with [Marketplace-Governance.md](Marketplace-Governance.md) and [Plugin-Governance.md](Plugin-Governance.md)

## Governing Principles

1. The core platform remains lightweight
2. Vendor functionality belongs in plugins
3. Everything communicates through APIs
4. Security is not optional
5. Backwards compatibility is maintained

See [Architecture-Principles.md](Architecture-Principles.md) for the complete list of design principles and anti-patterns.
