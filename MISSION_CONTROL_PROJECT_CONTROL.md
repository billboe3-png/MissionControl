# Mission Control — Project Control System

> **GIT REPOSITORY = CANONICAL PROJECT SOURCE OF TRUTH.**
> All important project information must live in this repository. Chat history, agent memory, local notes, and desktop files are NOT authoritative.

---

## 1. Purpose

Mission Control is an IT operations dashboard and workspace that provides:

- **Infrastructure monitoring** across heterogeneous environments (Linux, Windows, containers, network devices)
- **Agent-first automation** — a managed Agent executes all remote operations on behalf of the server
- **Plugin ecosystem** — community-extensible integrations (Git, Docker, Zabbix, Veeam, UniFi, MikroTik, D-Link, Hyper-V)
- **AI Operations** — anomaly detection, remediation suggestions, and log analysis
- **Multi-tenancy with RBAC** — team and role-based access control

---

## 2. Product Stage

**Community Edition v3.0.0-RC1** — Release candidate for real-world client testing.

The project is in **stabilization and validation mode**, not feature expansion.

---

## 3. Strategic Objective

```
STABILIZE → VALIDATE → DEPLOY → REAL-WORLD TEST → CLIENT TEST → RC1 → COMMUNITY EDITION v1.0
```

Stability and validation take priority over feature count.

---

## 4. Development Priority

1. **Stabilize** — Fix bugs, eliminate flaky tests, ensure CI passes
2. **Validate** — End-to-end testing against real infrastructure (MikroTik, D-Link, Veeam, Zabbix)
3. **Deploy** — Safe deployment to DEV environment
4. **RC1** — Release candidate readiness
5. **Client testing** — Real-world validation by early adopters

---

## 5. Release Objective

Deliver a production-ready **Community Edition RC1** that:

- Passes all CI checks (ruff, pytest, frontend build)
- Has verified end-to-end agent relay for all installed plugins
- Maintains LIVE environment stability
- Has no known critical regressions
- Has updated documentation matching the actual repository state

---

## 6. DEV / LIVE Architecture

| Environment | URL | Branch | Rules |
|-------------|-----|--------|-------|
| **DEV** | `https://missioncontroldev.optichosting.co.za` | `develop` | May break |
| **LIVE** | `https://Missioncontrol.optichosting.co.za` | `main` | Must remain stable |

### Git Flow

```
feature/*
    ↓
develop  →  DEV
    ↓
release validation
    ↓
main  →  LIVE
```

- Never develop directly on `main`
- Never test unfinished features on LIVE
- Never perform destructive testing on LIVE
- Do not create a third environment unless explicitly authorized

---

## 7. Git Strategy

- **Canonical source**: The Git repository at `https://github.com/billboe3-png/MissionControl`
- **Working branch**: `release/v3.0.0-rc1`
- **Commit convention**: Conventional commits (`fix(backend): …`, `feat(agent): …`, `chore: …`, `ci(backend): …`)
- **Before significant work**: `git status`, `git branch`, `git fetch`
- **Never**: `git reset --hard`, `git clean -fd` without explicit authorization
- **Commit/push from server**: `/opt/MissionControl` on `release/v3.0.0-rc1`
- **Never commit secrets** (`.env`, credentials, API keys)

---

## 8. Agent-First Architecture

```
Browser
    ↓
Mission Control (server)
    ↓
Mission Control Agent
    ↓
Infrastructure
```

The **Mission Control Agent is the network execution boundary**. The server must NOT bypass the Agent for any operation intended to occur from the Agent's network.

This applies to:
- MikroTik (RouterOS CLI, WebFig, configuration, discovery, ARP, MAC tables, topology, health checks, automation, backups)
- SNMP
- SSH
- WinRM
- Network device management (D-Link, etc.)
- Configuration changes
- Remote diagnostics
- Monitoring and automation

If an existing implementation bypasses the Agent, treat it as an architectural defect to be corrected.

---

## 9. Plugin Architecture

Plugins are installed in `backend/app/plugins/installed/` and discovered/loaded at runtime by the plugin loader.

### Currently Installed Plugins

| Plugin | Type | Status |
|--------|------|--------|
| `git` | integration | Active |
| `hyperv` | integration | Active |
| `official_dlink` | agent-relay | Active (RC1) |
| `official_docker` | integration | Active |
| `official_mikrotik` | agent-relay | Active (RC1) |
| `official_unifi` | integration | Active |
| `official_veeam` | integration + collector | Active |
| `system_info` | system | Active |
| `zabbix` | integration | Active |

### Plugin SDK

Plugins implement `ServerPluginSDK` with lifecycle methods: `setup()`, `start()`, `stop()`, `get_routes()`, `get_dashboard_widgets()`, `get_navigation_items()`, `health_check()`.

Agent plugins implement `AgentPlugin` with: `initialize()`, `collect_inventory()`, `execute_command()`.

---

## 10. AI Operations Architecture

- **AI Operations module**: Anomaly detection, remediation suggestions, log analysis
- **Context management**: `backend/app/ai/context.py`
- **Prompts**: `backend/app/ai/prompts.py`
- **Summarizer**: `backend/app/ai/summarizer.py`

---

## 11. Security Rules

- Never commit secrets, credentials, or `.env` files
- Never expose API keys in code or logs
- Use Fernet-generated secret keys for CI/workflows
- Authenticate all API endpoints with JWT/Bearer tokens
- Rate-limit login attempts per account
- Validate all agent command inputs
- Separate LIVE and DEV credentials
- All remote operations must go through the Agent (no direct server-to-infrastructure bypass)

---

## 12. Deployment Rules

- **Server**: Deployed via Docker Compose on the target host
- **Agent**: Installed as a systemd service on the managed machine
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis
- **Reverse proxy**: Nginx
- **Migrations**: Always run `alembic upgrade head` before pytest
- **Container names**: `missioncontrol-backend-1`, `missioncontrol-frontend-1`, `missioncontrol-nginx-1`, `missioncontrol-postgres-1`, `missioncontrol-redis-1`

---

## 13. Testing Rules

- **Backend tests**: `python -m pytest tests/ -q --tb=short` from `backend/`
- **Ruff linting**: Run on all changed files
- **Frontend build**: `npm run build` must pass TypeScript compilation
- **Test environment**: Requires `TESTING=1`, valid Fernet `MISSIONCONTROL_SECRET_KEY`, PostgreSQL, Redis
- **Shared assertions**: `tests/api/test_dashboard.py`, `test_setup_api.py`, `test_integration_management.py`, `test_zabbix_provider.py`, `test_startup_config.py` are shared with `main` — fix behavior in app code, not by loosening tests
- **Definition of Done**: Tests must pass; never convert NOT VERIFIED into PASS

---

## 14. Definition of Done

A task is complete only when **all** of the following apply:

- Implementation exists
- Tests exist
- Tests pass
- Integration works (verified against real or simulated targets)
- Quality gates pass (ruff, pytest, frontend build)
- Documentation is updated
- No known critical regression exists

Report results as:
- **PASS** — Verified by test
- **FAIL** — Test or verification failed
- **NOT VERIFIED** — Not yet tested; do not claim completion

---

## 15. Anti-Side-Tracking Rules

Do NOT start unrelated work. Do not introduce:

- New features
- New plugins
- UI redesigns
- Speculative refactoring
- New AI capabilities
- New integrations
- Architecture changes
- Cosmetic improvements
- "Nice to have" functionality

Unless directly required by:
- Current sprint
- Confirmed bug
- Deployment problem
- Security problem
- Failing test
- Release blocker
- Production reliability

If you identify an interesting idea outside the current objective:

**PARKED IDEA:**
- Reason: Outside current project objective
- Potential future sprint: TBD

Then continue with the current work.

---

## 16. Problem-First Exception

A developer may temporarily leave the current task when discovering:

- Security vulnerabilities
- Data-loss risks
- Production failures
- Deployment failures
- Authentication/authorization failures
- Agent failures (broken relay, broken communication)
- Database corruption
- Migration failures
- Release blockers
- Serious performance problems

Fix the confirmed problem first. After resolution, return to the original objective.

---

## 17. Documentation Synchronization Rules

When significant project state changes, update:

- `MISSION_CONTROL_PROJECT_CONTROL.md` (this file)
- `ROADMAP.md`
- `PROJECT_MEMORY.md`

Documentation must describe the **actual repository state**. Never claim something is complete if it is not verified.

---

## 18. Multi-Machine Development Rules

Mission Control may be developed from multiple PCs. The project state must remain identical regardless of which PC is used.

### Machine-Specific State (DO NOT commit)
- `.env` files
- Credentials
- Docker runtime state
- Local configuration
- Installed development tools
- Hardware
- IP addresses
- Operating-system configuration

### Shared State (MUST be in Git)
- Source code
- Plugin definitions
- Database migrations
- Tests
- Configuration templates
- Documentation
- Project control files

### Remote Edit Loop (server)
1. Edit local temp copy
2. `scp <file> billboe3@34.35.177.209:/opt/MissionControl/backend/<path>`
3. Run checks via `ssh ... bash /tmp/script.sh`
- Avoid `&&` inside PowerShell-quoted ssh commands (use a script file)

---

## 19. Git Synchronization Rules

- Pull/fetch before starting work: `git fetch`
- Work on `release/v3.0.0-rc1`
- Commit on server (`/opt/MissionControl`), not local OneDrive checkout
- Local OneDrive checkout has unrelated WIP (hyper-V plugins) — do not commit from there
- Before committing: `git status`, `git diff`, `git log --oneline -10`
- Stage only intended files
- Conventional commit messages
- Push from server only

---

## 20. AI-Agent Consistency Rules

- All AI agents (OpenCode, Dexter, Hermes) must read `MISSION_CONTROL_PROJECT_CONTROL.md` before significant work
- Agents must also read `ROADMAP.md` and `PROJECT_MEMORY.md`
- Agents must inspect Git state before acting
- Agents must determine the current objective before implementing
- Agents must search for existing implementations before creating new ones
- Agents must make the smallest appropriate change
- Agents must test changes before declaring completion
- Agents must update documentation when project state changes
- Never claim functionality exists unless it is implemented and verified

---

## 21. Change-Control Rules

Before any significant change:

1. Read this document and ROADMAP.md
2. Inspect the repository
3. Identify the current active objective
4. Determine the minimum work required
5. Implement only that work
6. Test it
7. Fix failures
8. Re-test
9. Update documentation if project state changed
10. Report results

Do not implement changes that conflict with project architecture unless fixing a confirmed problem.

---

## 22. Root-Cause-First Debugging

When something breaks:

1. DO NOT immediately patch the symptom
2. Determine:
   - What failed?
   - Where did it fail?
   - Why did it fail?
   - What depends on it?
   - Is it systemic?
   - What regression risk exists?
3. Fix the smallest correct root cause
4. Verify the fix
5. Check for related issues

---

## 23. Parking Lot

Ideas that are intentionally not implemented because they are outside the current RC1 objective.

### Parked Ideas

| Idea | Reason | Potential Future Sprint |
|------|--------|------------------------|
| Edge agent support (IoT/edge) | Not required for RC1 | 4.x |
| Workflow orchestration engine | Not required for RC1 | 4.x |
| GitOps integration | Not required for RC1 | 4.x |
| Terraform provider | Not required for RC1 | 4.x |
| OpenTelemetry integration | Not required for RC1 | 4.x |
| Secret manager integration | Not required for RC1 | 4.x |
| Multi-region agent federation | Enterprise feature | 4.x |
| OPA-based RBAC policies | Enterprise feature | 4.x |
| AI-powered playbook generation | Enterprise feature | 4.x |
| Mobile-responsive terminal UI | Not required for RC1 | 3.3.0 |
| Plugin marketplace reviews/ratings | Not required for RC1 | 3.3.0 |

---

## 24. Current Known Blockers

- **D-Link plugin import**: Local `relay.py` had `AgentCommand` imported from wrong module (`app.models.db.agent` instead of `app.models.db.agent_command`). Container copy was fixed via script; local file needs update and commit.
- **Agent 6 (zabbix-proxy)**: Goes offline after restart commands due to systemd start-limit-hit. Requires manual `sudo systemctl reset-failed mission-control-agent && sudo systemctl start mission-control-agent`.
- **Backend container stability**: Veeam circular import issue caused crashes; requires monitoring.
- **RC1 CI**: Must keep backend tests (1512+ passed) and frontend build green.

---

## 25. Current Priorities

1. **Keep CI green** — ruff + pytest + frontend build on `release/v3.0.0-rc1`
2. **Fix the D-Link local import** — Update `relay.py` to use `from app.models.db.agent_command import AgentCommand`
3. **Agent 6 reliability** — Ensure stable agent relay for MikroTik and D-Link testing
4. **End-to-end validation** — Test CLI, MAC, VLAN, WebUI for both MikroTik and D-Link via agent relay
5. **Documentation sync** — Ensure all docs match actual repository state
6. **RC1 readiness** — Stabilize, validate, deploy

---

## 26. OpenCode Rules

OpenCode must:

1. Read `MISSION_CONTROL_PROJECT_CONTROL.md` before significant work
2. Read `ROADMAP.md`
3. Read `PROJECT_MEMORY.md`
4. Inspect Git state
5. Determine the current objective
6. Determine whether the requested work is authorized
7. Search for existing implementations before creating new ones
8. Make the smallest appropriate change
9. Test changes
10. Update project documentation when project state changes
11. NOT blindly implement requests that conflict with project architecture

---

## 27. Multi-PC Coordination

The project is worked on from multiple PCs. To avoid confusion:

- **Always check `git status` and `git branch`** before starting work
- **Always fetch** before starting work: `git fetch`
- **Work on the correct branch**: `release/v3.0.0-rc1`
- **Local OneDrive checkout**: Has unrelated WIP on git/hyper-V plugins — do not commit from there
- **Server repo**: `/opt/MissionControl` — this is where commits and pushes happen
- **If uncertain about state**: Ask the project owner or check the server repo
- **Never overwrite another developer's changes** without explicit authorization
