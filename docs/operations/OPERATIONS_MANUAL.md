# Mission Control Operations Manual

**Version:** 1.0  
**Effective Date:** July 26, 2026  
**Owner:** Operations Team  
**Classification:** Internal Use

---

## Table of Contents

1. [OPERATIONS_MANUAL.md](./OPERATIONS_MANUAL.md) — This document: master index and overview
2. [DASHBOARD.md](./DASHBOARD.md) — Reading and interpreting the dashboard
3. [AGENTS.md](./AGENTS.md) — Monitoring agent management and states
4. [INVENTORY.md](./INVENTORY.md) — Understanding collected inventory data
5. [ALERTS.md](./ALERTS.md) — Alert management and response
6. [AUTOMATION.md](./AUTOMATION.md) — Automation execution and oversight
7. [PLAYBOOKS.md](./PLAYBOOKS.md) — Creating and managing playbooks
8. [PLUGINS.md](./PLUGINS.md) — Plugin operations and marketplace
9. [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md) — Remote command execution and management
10. [REPORTING.md](./REPORTING.md) — Available reports and data export
11. [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) — Incident response procedures
12. [MAINTENANCE.md](./MAINTENANCE.md) — Scheduled maintenance procedures
13. [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) — Disaster recovery and backup

---

## Overview

Mission Control is a centralized infrastructure management platform that aggregates data from multiple domain services — Hyper-V, Proxmox, Zabbix, Veeam, and others — into a single operational view. It provides real-time monitoring, automated remediation, AI-assisted operations, and comprehensive inventory management across your entire infrastructure.

The dashboard at `GET /api/v1/dashboard` serves as the primary entry point, returning aggregated data from all domain services in a single API call.

---

## Operator Responsibilities

### Daily Responsibilities

| Task | Frequency | Reference |
|------|-----------|-----------|
| Review dashboard for anomalies | Every shift start | [DASHBOARD.md](./DASHBOARD.md) |
| Respond to active alerts | Continuous | [ALERTS.md](./ALERTS.md) |
| Verify agent health | Every 2 hours | [AGENTS.md](./AGENTS.md) |
| Review automation execution results | Every 4 hours | [AUTOMATION.md](./AUTOMATION.md) |
| Check AI recommendations | Every shift start | [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) |

### Weekly Responsibilities

| Task | Frequency | Reference |
|------|-----------|-----------|
| Review agent inventory changes | Weekly | [INVENTORY.md](./INVENTORY.md) |
| Audit remote operations command history | Weekly | [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md) |
| Review plugin health and updates | Weekly | [PLUGINS.md](./PLUGINS.md) |
| Generate operational reports | Weekly | [REPORTING.md](./REPORTING.md) |

### Monthly Responsibilities

| Task | Frequency | Reference |
|------|-----------|-----------|
| Execute scheduled maintenance | Monthly | [MAINTENANCE.md](./MAINTENANCE.md) |
| Test disaster recovery procedures | Monthly | [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) |
| Review and update playbooks | Monthly | [PLAYBOOKS.md](./PLAYBOOKS.md) |
| Certificate and credential renewal check | Monthly | [MAINTENANCE.md](./MAINTENANCE.md) |

---

## How to Use This Manual

Each document in this operations manual is self-contained but cross-references related documents. Start with the document that matches your current task:

- **New operators:** Start with [DASHBOARD.md](./DASHBOARD.md) to learn how to read the operational view, then proceed to [ALERTS.md](./ALERTS.md) for response procedures.
- **Troubleshooting an issue:** Begin with [ALERTS.md](./ALERTS.md) and [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md).
- **Executing remote changes:** Refer to [REMOTE_OPERATIONS.md](./REMOTE_OPERATIONS.md).
- **Automating a task:** Start with [PLAYBOOKS.md](./PLAYBOOKS.md), then see [AUTOMATION.md](./AUTOMATION.md) for execution oversight.
- **Scheduled maintenance:** Follow [MAINTENANCE.md](./MAINTENANCE.md) procedures.

---

## System Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                   Mission Control API                    │
│              286 endpoints, JWT auth, rate limited       │
├─────────────┬──────────────┬──────────────┬─────────────┤
│  Dashboard  │   Automation │   AI Engine  │  Event Bus  │
│  (GET /api  │   (Playbooks │  (Correlate, │  (34 event  │
│   /v1/      │   Schedules, │   Recommend, │   types,    │
│   dashboard)│   Approvals) │   Score)     │   async     │
│             │              │              │   pub/sub)  │
├─────────────┴──────────────┴──────────────┴─────────────┤
│                    Agent Network                          │
│           9 states, 30s heartbeat cycle                   │
│     agent → server commands + remote targets              │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│ Hyper-V  │ Proxmox  │  Zabbix  │  Veeam   │  Plugins     │
│          │          │          │          │  (Server/    │
│          │          │          │          │   Agent/     │
│          │          │          │          │   Hybrid)    │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
```

---

## Quick Reference: API Access

All operational data is accessible through the Mission Control API. Authentication uses JWT tokens.

```bash
# Obtain a token
curl -X POST https://missioncontrol.example.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "operator", "password": "***"}'

# Access the dashboard
curl -H "Authorization: Bearer <token>" \
  https://missioncontrol.example.com/api/v1/dashboard
```

Rate limiting is enforced. If you receive a `429 Too Many Requests` response, wait before retrying. Current rate limit: defined in the API gateway configuration.

---

## Emergency Contacts

| Role | Contact | When to Escalate |
|------|---------|-----------------|
| On-Call Operator | Defined in PagerDuty | First responder for all alerts |
| Infrastructure Lead | Defined in team roster | Severity 1 incidents, DR activation |
| Security Team | Defined in security policy | Security-related alerts, credential compromise |
| Platform Engineering | Defined in team roster | Platform-level failures, API outages |

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-26 | Operations Team | Initial release |
