# Mission Control — Roadmap

> **Current Release: v3.0.0-RC1 (Release Candidate 1)**
> **Branch:** `release/v3.0.0-rc1`
> **Status:** Stabilization and validation for Community Edition RC1
> **Target:** Real-world client testing → RC1 → Community Edition v1.0
> 
> **Immediate Priority:** Keep CI green (ruff + pytest + frontend build), fix known blockers, complete end-to-end agent-relay validation for MikroTik and D-Link.
> 
> **CI Status (latest verified):** Run `31415687763` on `release/v3.0.0-rc1`: **all green** — backend lint ✓, backend tests **1512 passed / 1 skipped**, frontend tsc+build ✓.

---

This document outlines the Mission Control project roadmap. Priorities may shift based on community feedback, security needs, and Enterprise customer requirements.

---

## Current Release: 3.x

**Status:** Active development and support

### Delivered in 3.0.0

- AI Operations module (anomaly detection, remediation suggestions, log analysis)
- Plugin system with community marketplace
- Multi-tenancy with RBAC
- Web-based terminal with session recording
- Live log streaming
- Playbook editor with conditions, loops, and parallel execution
- Bulk operations across agent groups
- SSO / SAML (Enterprise)
- Advanced audit logging (Enterprise)
- Compliance reports (Enterprise)
- One-click GCE deployment
- Terraform modules for AWS and Azure

### Planned for 3.x (Patch / Minor Releases)

| Feature | Edition | Target | Status |
|---------|---------|--------|--------|
| Agent auto-update mechanism | Community | 3.1.0 | In progress |
| Playbook versioning and rollback | Community | 3.1.0 | In progress |
| Inventory diff notifications | Community | 3.1.0 | Planned |
| AI-powered playbook generation | Enterprise | 3.2.0 | Planned |
| Custom dashboard metrics API | Community | 3.2.0 | Planned |
| Agent health score dashboard | Community | 3.2.0 | Planned |
| RBAC permission templates | Enterprise | 3.2.0 | Planned |
| Webhook retry and dead-letter queue | Community | 3.3.0 | Planned |
| Plugin marketplace reviews and ratings | Community | 3.3.0 | Planned |
| Mobile-responsive terminal UI | Community | 3.3.0 | Planned |
| HIPAA compliance report template | Enterprise | 3.3.0 | Planned |

---

## Near-Term: 4.x

**Status:** Early planning

### Planned Features

| Feature | Edition | Description |
|---------|---------|-------------|
| Workflow orchestration engine | Community | DAG-based workflow scheduler replacing simple playbook chaining |
| Edge agent support | Community | Lightweight agents for IoT and edge computing nodes |
| GitOps integration | Community | Sync agent configurations and playbooks from Git repositories |
| Terraform provider | Community | Manage Mission Control resources as Terraform objects |
| OpenTelemetry integration | Community | Distributed tracing across agents and server |
| Secret manager integration | Community | Native integration with HashiCorp Vault, AWS Secrets Manager |
| Multi-region agent federation | Enterprise | Geographically distributed server clusters with agent failover |
| Custom RBAC policies | Enterprise | Open Policy Agent (OPA) integration for custom authorization rules |
| Data residency controls | Enterprise | Region-locked data storage for compliance requirements |
| Premium support dashboard | Enterprise | SLA tracking, incident history, and escalation workflows |

### Architecture Goals for 4.x

- **Horizontal scaling** — Stateless API servers behind a load balancer with shared Redis/PostgreSQL.
- **Agent protocol v2** — Binary protocol replacing JSON for lower latency and bandwidth.
- **Event-driven architecture** — Internal event bus for decoupled component communication.
- **Observability** — First-class metrics, tracing, and structured logging across all components.

---

## Long-Term Vision

### Where Mission Control is Heading

**Infrastructure automation for every team.** Mission Control aims to be the platform where teams manage their entire fleet — from traditional servers to containers to edge devices — with automation, AI assistance, and enterprise-grade security.

### Key Themes

#### Universal Agent Coverage
- Agents for Linux, Windows, macOS, containers, Kubernetes, and edge/IoT devices
- Agent-to-agent communication for mesh-style operations
- Offline agent support with store-and-forward for intermittent connectivity

#### AI-Native Operations
- Closed-loop remediation: detect, diagnose, and fix issues automatically
- Predictive scaling and capacity planning
- Natural-language infrastructure queries ("how many nginx servers are running?")

#### Enterprise Readiness
- FedRAMP and SOC 2 Type II certification
- Multi-region deployment with data residency
- Disaster recovery and business continuity tooling

#### Community Ecosystem
- Thriving plugin marketplace with hundreds of integrations
- Community-contributed playbooks and templates
- Conference talks, tutorials, and certification programs

---

## Community vs Enterprise Feature Split

Features are split between editions as follows:

### Community Edition (Free, Open Source)
All core platform features including:
- Agent management and monitoring
- Playbook editor and execution engine
- Basic RBAC
- Plugin SDK and marketplace
- Basic AI operations
- Inventory and change tracking
- Remote terminal and log streaming
- Docker and Kubernetes deployment

### Enterprise Edition (Commercial)
All Community features plus:
- SSO / SAML integration
- Advanced audit logging and compliance reports
- Custom RBAC policies (OPA)
- Multi-region agent federation
- Data residency controls
- Custom branding and white-labeling
- Premium support with SLA
- AI-powered playbook generation
- Dedicated deployment assistance

See [SUPPORTED_PLATFORMS.md](SUPPORTED_PLATFORMS.md) for a detailed feature comparison.

---

## How to Request a Feature

1. **Search existing issues** at [github.com/billboe3-png/MissionControl/issues](https://github.com/billboe3-png/MissionControl/issues) to see if the feature has already been discussed.
2. **Open a new issue** using the **Feature Request** template.
3. **Describe the problem** you are trying to solve, your proposed solution, and any alternatives you considered.
4. **Label it** — maintainers will apply labels like `enhancement`, `feature-request`, `enterprise-only`, or `community-welcome`.
5. **Engage in discussion** — maintainers may ask clarifying questions or suggest scope adjustments.

### What Makes a Good Feature Request

- Clearly describes the **problem** before proposing a solution
- Includes **use cases** — who benefits and how
- Is scoped to a **single capability** (one feature per issue)
- Acknowledges **alternatives** and tradeoffs
- Indicates whether it is relevant to Community, Enterprise, or both

---

## Release Cadence

| Release Type | Frequency | Description |
|-------------|-----------|-------------|
| Patch (3.0.x) | As needed | Bug fixes and security patches |
| Minor (3.x.0) | ~Monthly | New features, backward-compatible |
| Major (X.0.0) | ~Annually | Breaking changes, major features |

Beta and release candidate periods are used for major releases. Subscribe to [releases on GitHub](https://github.com/billboe3-png/MissionControl/releases) for notifications.

---

## Questions or Feedback

- Open a [Discussion](https://github.com/billboe3-png/MissionControl/discussions) for general roadmap feedback
- Email [product@missioncontrol.dev](mailto:product@missioncontrol.dev) for Enterprise-specific requests
- Join the community Slack (link in the repository About section)

---

## RC1-Specific Notes (v3.0.0-RC1)

### Installed Plugins (verified in `backend/app/plugins/installed/`)
- `git` — Git integration
- `hyperv` — Hyper-V integration  
- `official_dlink` — D-Link DGS-1210 agent-relay (NEW)
- `official_docker` — Docker integration
- `official_mikrotik` — MikroTik RouterOS agent-relay (NEW)
- `official_unifi` — UniFi integration
- `official_veeam` — Veeam integration + collector
- `system_info` — System info plugin
- `zabbix` — Zabbix integration

### Agent Plugins (in `.agents/agent/plugins/`)
- `dlink_plugin.py` — D-Link CLI, REST, WebUI stream
- `mikrotik_plugin.py` — MikroTik CLI, REST, native API, WebFig relay
- `active_directory_plugin.py` — AD via SSH/PowerShell

### Known Blockers for RC1
1. **D-Link import fix** — Local `relay.py` needs `AgentCommand` import corrected
2. **Agent 6 (zabbix-proxy)** — Goes offline after restart; needs systemd `reset-failed`
3. **Veeam circular import** — Pre-existing issue causing backend crashes; needs fix

### RC1 Validation Checklist
- [ ] CI green: ruff + pytest + frontend build
- [ ] MikroTik E2E via Agent 6: CLI, ARP, Terminal, WebFig
- [ ] D-Link E2E via Agent 6: CLI, MAC table, VLAN, WebUI tunnel
- [ ] Veeam dashboard: real data verified
- [ ] Zabbix integration: hosts, metrics, alerts
- [ ] UniFi integration: sites, devices, clients
- [ ] Documentation sync: all docs match repo state