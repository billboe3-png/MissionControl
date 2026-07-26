# Architecture Review Report — Sprint 3.2A

**Date:** 2026-07-26
**Scope:** Full repository audit for Mission Control v1 Architecture Alignment
**Repository:** 328 backend files (~57K lines), 32 agent files (~4.3K lines), 143 frontend files

---

## Executive Summary

Mission Control has grown to 328 backend files across 14 directories. This audit classifies every component against the new agent-first architecture. The server must focus on web UI, API, auth, automation, AI, and plugin management. Agents handle all infrastructure collection. SSH/WinRM become fallback-only.

**Key findings:**
- 6 empty/placeholder directories can be removed
- 1 stub router (`git.py`) returning 501
- 3 "thin wrapper" services that just delegate to platform modules
- 12 dashboard providers that duplicate agent collection
- SSH/WinRM providers (~2,000 lines) become fallback-only
- `remote_service.py` (960 lines) and `automation_service.py` (1,532 lines) need refactoring
- Agent code is already clean and well-structured — minimal changes needed

---

## Component Classification

### REMOVE (Dead Code / Empty / Unused)

| Component | Path | Reason |
|-----------|------|--------|
| Empty API package | `backend/app/api/` | Empty directory, never used |
| Empty storage package | `backend/app/storage/` | Empty directory, never used |
| Empty utils package | `backend/app/utils/` | Empty directory, never used |
| Empty seeders dir | `backend/app/db/seeders/` | Empty, seeding moved to `app/seed/` |
| Git router (stub) | `backend/app/routers/git.py` | Returns HTTP 501, never implemented |
| Stale root files | `git`, `temp-check.ps1` | Accidental commits, not part of project |
| Old website | `website/` (deleted in commit d2880ba) | Already removed |
| Old sprint scripts | `scripts/Create-Sprint*.ps1`, `scripts/PreSprint1.ps1` | Historical, no longer used |
| Old sprint fixes | `scripts/Fix-Sprint*.ps1`, `scripts/Sprint-*.ps1` | Historical, no longer used |

**Total: ~15 files/directories to remove**

---

### REMOVE (Architecture Misalignment — Server Should NOT Do This)

Per the new architecture, the server should NOT directly collect infrastructure data. These components duplicate what agents provide:

| Component | Path | Lines | Reason |
|-----------|------|------:|--------|
| Docker provider | `backend/app/providers/docker_provider.py` | 136 | Agent collects Docker data via plugin |
| Git provider | `backend/app/providers/git_provider.py` | 150 | Agent collects git info; server doesn't need it |
| System provider | `backend/app/providers/system_provider.py` | 47 | Agent collects CPU/memory/disk |
| Docker service | `backend/app/services/docker_service.py` | 12 | Thin wrapper over removed provider |
| Doctor service | `backend/app/services/doctor_service.py` | 5 | Thin wrapper over platform |
| Status service | `backend/app/services/status_service.py` | 5 | Thin wrapper over platform |
| Summary service | `backend/app/services/summary_service.py` | 42 | Dashboard KPI aggregation — move to dashboard_service |
| System service | `backend/app/services/system_service.py` | 40 | psutil metrics — agent collects this |
| Platform abstraction | `backend/app/platform/` (5 files) | 132 | OS detection/status is agent territory |
| Infrastructure abstraction | `backend/app/infrastructure/` (6 files) | 175 | Docker SDK wrapper — agent plugin handles this |
| Docker router | `backend/app/routers/docker.py` | 20 | Returns agent-collected data |
| Doctor router | `backend/app/routers/doctor.py` | 17 | Returns agent-collected data |
| Status router | `backend/app/routers/status.py` | 17 | Returns agent-collected data |
| Version router | `backend/app/routers/version.py` | 19 | Redundant — use `/api/v1/health/live` |
| Docker dashboard provider | `backend/app/providers/hyperv_dashboard.py` | 63 | Replace with agent-sourced dashboard |
| Proxmox dashboard provider | `backend/app/providers/proxmox_dashboard.py` | 67 | Replace with agent-sourced dashboard |
| Remote dashboard provider | `backend/app/providers/remote_provider.py` | 74 | Replace with agent-sourced dashboard |

**Total: ~23 files (~965 lines) to remove or replace**

---

### REFACTOR (SSH/WinRM → Fallback-Only)

SSH/WinRM remain but become fallback mechanisms, not primary:

| Component | Path | Lines | Action |
|-----------|------|------:|--------|
| SSH provider | `backend/app/providers/remote/ssh_provider.py` | 1,155 | Keep as fallback; mark as deprecated |
| WinRM provider | `backend/app/providers/remote/winrm_provider.py` | 829 | Keep as fallback; mark as deprecated |
| Remote base | `backend/app/providers/remote/base_provider.py` | 168 | Simplify interface |
| Remote factory | `backend/app/providers/remote/provider_factory.py` | 102 | Add agent-first resolution |
| Remote service | `backend/app/services/remote_service.py` | 960 | Refactor: agent-first, SSH/WinRM fallback |
| Remote router | `backend/app/routers/remote.py` | 554 | Refactor: prefer agent execution |
| Remote host model | `backend/app/models/db/remote_host.py` | 97 | Keep — hosts still exist, just prefer agents |
| Credential profile | `backend/app/models/db/credential_profile.py` | 113 | Keep — still needed for fallback |
| Remote schemas | `backend/app/schemas/remote_*.py` | ~370 | Simplify — less focus on direct SSH |
| Remote repository | `backend/app/repositories/remote_host_repository.py` | 183 | Keep |
| Remote repository | `backend/app/repositories/command_history_repository.py` | 159 | Keep |
| Remote repository | `backend/app/repositories/credential_profile_repository.py` | 177 | Keep |
| Remote repository | `backend/app/repositories/command_template_repository.py` | 85 | Keep |
| Remote repository | `backend/app/repositories/scheduled_command_repository.py` | 134 | Keep — agent can schedule |
| Command history model | `backend/app/models/db/command_history.py` | 75 | Keep |
| Command template model | `backend/app/models/db/command_template.py` | 58 | Keep |
| Scheduled command model | `backend/app/models/db/scheduled_command.py` | 69 | Keep |
| Credential profile model | `backend/app/models/db/credential_profile.py` | 113 | Keep |

**Total: ~4,800 lines to refactor (SSH/WinRM stay as fallback)**

---

### REFACTOR (Automation Providers → Agent-First)

Automation execution should prefer agent-based execution:

| Component | Path | Lines | Action |
|-----------|------|------:|--------|
| Automation base | `backend/app/providers/automation/base_provider.py` | 85 | Keep |
| Automation factory | `backend/app/providers/automation/provider_factory.py` | 87 | Agent-first resolution |
| Agent automation | `backend/app/providers/automation/agent_provider.py` | 131 | **Primary** execution method |
| SSH automation | `backend/app/providers/automation/ssh_provider.py` | 124 | Fallback |
| WinRM automation | `backend/app/providers/automation/winrm_provider.py` | 123 | Fallback |
| PowerShell automation | `backend/app/providers/automation/powershell_provider.py` | 139 | Fallback |
| Bash automation | `backend/app/providers/automation/bash_provider.py` | 134 | Fallback |
| HTTP automation | `backend/app/providers/automation/http_provider.py` | 162 | Keep (webhook triggers) |
| Hyper-V automation | `backend/app/providers/automation/hyperv_provider.py` | 138 | Agent-first |
| Proxmox automation | `backend/app/providers/automation/proxmox_provider.py` | 127 | Agent-first |

**Total: ~1,250 lines — factory refactored, providers kept as fallback**

---

### KEEP (Core Server Functionality)

| Component | Path | Lines | Reason |
|-----------|------|------:|--------|
| **Agent Management** | | | |
| Agent router | `backend/app/routers/agent.py` | 300 | Primary management mechanism |
| Agent service | `backend/app/services/agent_service.py` | 658 | Core agent orchestration |
| Agent model | `backend/app/models/db/agent.py` | 190 | Core data model |
| Agent command model | `backend/app/models/db/agent_command.py` | 145 | Command queue |
| Agent target model | `backend/app/models/db/agent_remote_target.py` | 118 | Remote target relay |
| Agent token model | `backend/app/models/db/agent_registration_token.py` | 99 | Registration tokens |
| Agent repository | `backend/app/repositories/agent_repository.py` | 261 | Data access |
| Agent schemas | `backend/app/schemas/agent.py` | 295 | API contracts |
| Agent token service | `backend/app/services/agent_token_service.py` | 131 | Token management |
| Agent token router | `backend/app/routers/agent_token.py` | 71 | Token API |
| Agent target router | `backend/app/routers/agent_remote_target.py` | 234 | Target CRUD |
| Agent target repo | `backend/app/repositories/agent_remote_target_repository.py` | 65 | Data access |
| Agent target schema | `backend/app/schemas/agent_remote_target.py` | 59 | API contracts |
| Agent token schema | `backend/app/schemas/agent_token.py` | 38 | API contracts |
| **Multi-Tenancy** | | | |
| Company model | `backend/app/models/db/company.py` | 166 | Tenant isolation |
| Site model | `backend/app/models/db/site.py` | 142 | Site management |
| User model | `backend/app/models/db/user.py` | 103 | RBAC |
| Company router | `backend/app/routers/company.py` | 78 | Tenant API |
| Site router | `backend/app/routers/site.py` | 194 | Site API |
| Auth router | `backend/app/routers/auth.py` | 227 | JWT auth |
| Auth service | `backend/app/services/auth_service.py` | 265 | Auth logic |
| Company service | `backend/app/services/company_service.py` | 258 | Company CRUD |
| Site service | `backend/app/services/site_service.py` | 408 | Site CRUD |
| Company context | `backend/app/core/company_context.py` | 71 | Tenant context |
| Auth dependency | `backend/app/core/auth_dependency.py` | 45 | JWT extraction |
| **Plugin Framework** | | | |
| Plugin base | `backend/app/plugins/base.py` | 89 | ABC |
| Server plugin SDK | `backend/app/plugins/server.py` | 146 | Server plugins |
| Agent plugin SDK | `backend/app/plugins/agent.py` | 171 | Agent plugins |
| Communication | `backend/app/plugins/communication.py` | 273 | Plugin protocol |
| Plugin loader | `backend/app/plugins/loader.py` | 180 | Dynamic loading |
| Plugin router | `backend/app/routers/plugin.py` | 218 | Plugin API |
| Plugin service | `backend/app/services/plugin_service.py` | 270 | Plugin lifecycle |
| Plugin marketplace | `backend/app/services/plugin_marketplace_service.py` | 312 | Catalog |
| Plugin model | `backend/app/models/db/plugin.py` | 173 | Plugin registry |
| Plugin repository | `backend/app/repositories/plugin_repository.py` | 117 | Data access |
| Plugin schemas | `backend/app/schemas/plugin.py` | 157 | API contracts |
| **Automation** | | | |
| Automation service | `backend/app/services/automation_service.py` | 1,532 | Playbook engine |
| Automation router | `backend/app/routers/automation.py` | 660 | 42 endpoints |
| Playbook models | `backend/app/models/db/playbook*.py` (5) | ~400 | Playbook data |
| Approval models | `backend/app/models/db/approval_*.py` (2) | ~106 | Approval workflow |
| Audit model | `backend/app/models/db/audit_trail.py` | 56 | Audit trail |
| Event trigger model | `backend/app/models/db/event_trigger.py` | 67 | Event triggers |
| Execution log model | `backend/app/models/db/execution_log.py` | 67 | Execution logs |
| Automation repositories | 7 files | ~700 | Data access |
| Automation schemas | 7 files | ~500 | API contracts |
| **AI Operations** | | | |
| AI engine | `backend/app/ai/ai_engine.py` | 420 | Orchestrator |
| AI provider | `backend/app/ai/ai_provider.py` | 596 | LLM providers |
| AI service | `backend/app/ai/ai_service.py` | 310 | Service layer |
| Confidence engine | `backend/app/ai/confidence_engine.py` | 109 | Scoring |
| Correlation engine | `backend/app/ai/correlation_engine.py` | 273 | Alert correlation |
| Incident classifier | `backend/app/ai/incident_classifier.py` | 318 | Classification |
| Recommendation engine | `backend/app/ai/recommendation_engine.py` | 327 | Recommendations |
| AI router | `backend/app/routers/ai.py` | 153 | AI API |
| AI schemas | `backend/app/schemas/ai.py` | 72 | API contracts |
| **Integration Profiles** | | | |
| Integration router | `backend/app/routers/integration.py` | 144 | CRUD + test |
| Integration service | `backend/app/services/integration_service.py` | 536 | Lifecycle |
| Integration model | `backend/app/models/db/integration_profile.py` | 225 | Config storage |
| Integration repository | `backend/app/repositories/integration_profile_repository.py` | 179 | Data access |
| Integration schemas | `backend/app/schemas/integration.py` | 148 | API contracts |
| **Identity (Server Plugins)** | | | |
| Identity router | `backend/app/routers/identity.py` | 420 | AD + M365 API |
| Identity service | `backend/app/services/identity_service.py` | 300 | AD + M365 logic |
| Identity providers | 9 files | ~1,700 | LDAP, Graph, agent |
| Identity schemas | `backend/app/schemas/identity.py` | 330 | API contracts |
| **Virtualization (Server Plugins)** | | | |
| Hyper-V router | `backend/app/routers/hyperv.py` | 253 | Hyper-V API |
| Hyper-V service | `backend/app/services/hyperv_service.py` | 73 | Thin service |
| Hyper-V providers | 6 files | ~1,650 | Base, real, mock, agent |
| Proxmox router | `backend/app/routers/proxmox.py` | 338 | Proxmox API |
| Proxmox service | `backend/app/services/proxmox_service.py` | 100 | Thin service |
| Proxmox providers | 6 files | ~1,800 | Base, real, mock, agent |
| Virtualization base | `backend/app/providers/virtualization/` (3) | ~170 | Shared models |
| Hyper-V schemas | `backend/app/schemas/hyperv.py` | 220 | API contracts |
| Proxmox schemas | `backend/app/schemas/proxmox.py` | 326 | API contracts |
| **Monitoring (Server Plugin)** | | | |
| Zabbix router | `backend/app/routers/zabbix.py` | 195 | Zabbix API |
| Zabbix service | `backend/app/services/zabbix_service.py` | 91 | Thin service |
| Zabbix providers | 6 files | ~1,700 | Base, real, mock, agent |
| Zabbix schemas | `backend/app/schemas/zabbix.py` | 308 | API contracts |
| **Backup (Server Plugin)** | | | |
| Veeam router | `backend/app/routers/veeam.py` | 229 | Veeam API |
| Veeam service | `backend/app/services/veeam_service.py` | 417 | Veeam logic |
| Veeam providers | 9 files | ~3,100 | Base, real, mock, agent, PowerShell, DB bridge |
| Veeam schemas | `backend/app/schemas/veeam.py` | 180 | API contracts |
| **Core Infrastructure** | | | |
| Main app | `backend/app/main.py` | 250 | FastAPI factory |
| Config | `backend/app/core/config.py` | 314 | Settings |
| Security | `backend/app/core/security.py` | 119 | Fernet encryption |
| Startup check | `backend/app/core/startup_check.py` | 80 | Env validation |
| DB engine | `backend/app/db/database.py` | 50 | SQLAlchemy |
| DB base | `backend/app/db/base.py` | 13 | DeclarativeBase |
| Postgres health | `backend/app/db/postgres.py` | 44 | Health check |
| Redis singleton | `backend/app/db/redis.py` | 21 | Client + health |
| **Dashboard** | | | |
| Dashboard router | `backend/app/routers/dashboard.py` | 38 | Aggregation |
| Dashboard service | `backend/app/services/dashboard_service.py` | 301 | Orchestrator |
| Dashboard providers | 10 files | ~600 | Project, task, note, etc. |
| **Seed Data** | | | |
| Seed runner | `backend/app/seed/runner.py` | ~50 | Orchestrator |
| Seed modules | 8 files | ~300 | Demo data |
| **Setup** | | | |
| Setup router | `backend/app/routers/setup.py` | 50 | First-run wizard |
| Setup service | `backend/app/services/setup_service.py` | 147 | Bootstrap logic |
| **Health** | | | |
| Health router | `backend/app/routers/health.py` | 29 | Liveness/readiness |
| Health provider | `backend/app/providers/health_provider.py` | 52 | DB + Redis checks |
| Health service | `backend/app/services/health_service.py` | 36 | Health dashboard |
| **Application Metadata** | | | |
| Application service | `backend/app/services/application_service.py` | 31 | App info for dashboard |

---

### MERGE

| Components | Action | Reason |
|------------|--------|--------|
| `application_service.py` + `summary_service.py` | Merge into `dashboard_service.py` | Both provide dashboard metadata |
| `docker_service.py` + `doctor_service.py` + `status_service.py` | Remove (replaced by agent data) | Thin wrappers with no unique logic |
| `IntegrationsService` + `IntegrationService` | Check for duplication | `integrations_service.py` (35 lines) may overlap with `integration_service.py` (536 lines) |
| Multiple "overview" endpoints per provider | Consolidate where possible | Hyper-V, Proxmox, Zabbix, Veeam each have overview + individual endpoints |

---

### KEEP (Agent — Minimal Changes)

The agent is already well-structured and aligned with the new architecture:

| Component | Path | Lines | Action |
|-----------|------|------:|--------|
| Agent orchestrator | `.agents/agent/agent.py` | 358 | Keep — already implements heartbeat-driven model |
| Agent client | `.agents/agent/client.py` | 125 | Keep — outbound-only, retry logic |
| Agent config | `.agents/agent/config.py` | 137 | Keep |
| Agent heartbeat | `.agents/agent/heartbeat.py` | 52 | Keep |
| Agent inventory | `.agents/agent/inventory.py` | 304 | Keep |
| Agent executor | `.agents/agent/executor.py` | 244 | Keep |
| Agent command queue | `.agents/agent/command_queue.py` | 105 | Keep |
| Agent remote manager | `.agents/agent/remote.py` | 170 | Keep |
| Agent plugins | 7 plugin files | ~1,169 | Keep |
| Agent connectors | 4 connector files | ~697 | Keep as fallback mechanism |
| Agent tests | `tests/test_agent.py` | 514 | Keep |
| Agent installers | `install-agent.ps1`, `install-agent-linux.sh` | ~830 | Keep |

**No structural changes needed to the agent.**

---

### KEEP (Frontend — Minimal Changes)

| Component | Action |
|-----------|--------|
| Pages for removed features | Remove `pages/infrastructure/DockerPage.tsx`, `GitPage.tsx` |
| Remote Operations pages | Keep but update to prefer agent execution |
| All other pages | Keep — they display data regardless of source |
| Services | Update `api.ts` to remove dashboard calls for removed providers |
| Navigation | Update to remove dead links |
| Components | Keep — all are reusable UI components |

---

## Database Review

### Tables to KEEP (29 tables)

All 29 existing tables are needed by current features:

| Table | Used By |
|-------|---------|
| `agents` | Agent management |
| `agent_commands` | Command queue |
| `agent_registration_tokens` | Agent registration |
| `agent_remote_targets` | Remote target relay |
| `companies` | Multi-tenancy |
| `sites` | Site management |
| `users` | Authentication |
| `integration_profiles` | Integration config |
| `credential_profiles` | Credential vault |
| `remote_hosts` | Remote operations (fallback) |
| `command_history` | Command audit |
| `command_templates` | Reusable commands |
| `scheduled_commands` | Scheduled execution |
| `playbooks` | Automation |
| `playbook_steps` | Automation |
| `playbook_executions` | Automation |
| `playbook_schedules` | Automation |
| `playbook_variables` | Automation |
| `event_triggers` | Automation |
| `approval_requests` | Automation |
| `approval_workflows` | Automation |
| `execution_logs` | Automation |
| `audit_trail` | Automation |
| `plugins` | Plugin framework |
| `projects` | Project management |
| `tasks` | Task management |
| `notes` | Note management |
| `parking_lots` | Backlog |
| `resumes` | Resume context |

### Tables: No changes needed

No tables are obsolete — all are actively used by existing features. The "unused features" (projects, tasks, notes, parking lot, resume) are part of the core workspace functionality and should remain.

---

## Migration Impact Assessment

| Change | Migration Impact | Risk |
|--------|-----------------|------|
| Remove empty directories | None | None |
| Remove stub `git.py` router | None (no DB) | None |
| Remove platform/infrastructure dirs | None (no DB) | None |
| Remove dashboard providers | None (no DB) | None |
| Refactor SSH/WinRM to fallback | None (no schema change) | Low |
| Refactor automation providers | None (no schema change) | Low |
| Add agent-first resolution | None (no schema change) | Low |

**No database migrations required for this sprint.**

---

## Recommendations

### Community Edition v1.0

1. **Agent-first architecture**: All infrastructure data flows through agents. Server never polls directly.
2. **Configuration-driven**: Community = Docker Compose / LXC. Enterprise = Cloud/K8s. Same codebase.
3. **Plugin marketplace**: Server plugins for Veeam, Zabbix, Hyper-V, Proxmox, AD, M365.
4. **Fallback SSH/WinRM**: For devices that absolutely cannot run agents (switches, firewalls).

### Enterprise Edition

1. **Multi-region**: Agent relay chains for geographically distributed infrastructure.
2. **RBAC expansion**: Role-based access with per-site, per-company, per-plugin permissions.
3. **Audit compliance**: Extended audit trail with SIEM integration.
4. **SSO/SAML**: Enterprise identity provider integration.

---

## Technical Debt Summary

| Item | Severity | Effort |
|------|----------|--------|
| `automation_service.py` at 1,532 lines | Medium | Refactor into smaller modules |
| `remote_service.py` at 960 lines | Medium | Refactor to agent-first |
| `ssh_provider.py` at 1,155 lines | Low | Keep as fallback, no change needed |
| Empty directories (`api/`, `storage/`, `utils/`) | Low | Quick cleanup |
| Stub `git.py` router | Low | Quick removal |
| `docs/ROADMAP.md` outdated | Low | Already updated |
| `docs/` has 60+ files, many outdated | Medium | Review and update |

---

## Summary Statistics

| Category | Before | After (Planned) |
|----------|--------|-----------------|
| Backend files | 328 | ~290 |
| Backend lines | ~57,172 | ~52,000 |
| Routers | 30 | 24 |
| Services | 32 | 26 |
| Providers (total) | 56 | 45 |
| Provider dirs | 9 | 7 |
| Empty directories | 4 | 0 |
| Tests | 43 | 43 (no tests removed) |
| Agent files | 32 | 32 (no changes) |
| Frontend pages | 73 | 71 |
