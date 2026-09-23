# Tenancy & Authorization Hardening — Design & Implementation Plan

Status: DRAFT (RC1 follow-up)
Related: `docs/SECURITY_REVIEW.md` (now partially stale — see §10)

---

## 1. Context

Mission Control ships with a tenant-aware **data model** (Sprint 2.9) but the
**enforcement layer** around it is incomplete. Production is effectively a single
tenant (one company, CORHQVEEAM workload), yet the public agent-registration
endpoint can rotate any agent's API key without a token, plugin routers are
unauthenticated, and several admin routers allow privilege escalation.

This doc records a ground-up audit of the current code, ranks the gaps, and
defines an enforcement-first design that keeps the existing edge/agent and
registration-token architecture intact. Changes are phased so the ~1582-test
backend CI stays green on `release/v3.0.0-rc1`.

Design rule from product: tenancy sits **above** the existing Agent architecture —

```
User → (MSP role) → Tenant (Company) → Site → Agent → Infrastructure
```

We do **not** redesign the agent relay/command-polling mechanism.

---

## 2. Current-State Audit

### 2.1 Auth primitives

| Primitive | Location | Behaviour |
|-----------|----------|-----------|
| Role hierarchy | `app/services/auth_service.py:34-56` | `ROLES = [global_admin, company_admin, site_admin, operator, readonly]`; `ROLE_HIERARCHY` ranks 5→1; `role_has_min_level(role, level)`, `require_role(user, min_role)` (raises 403) |
| Password hashing | `auth_service.py:66-75` | PBKDF2-SHA256, 260k iters |
| JWT | service (HS256, 8h) | Claims carry `sub/cid/sid/role` |
| Current-user dependency | `app/core/auth_dependency.py:18-50` | `get_current_user` — Bearer header **or** `?token=` (WebSocket handshakes), 401 on missing/invalid |
| Tenant context | `app/core/company_context.py` | `CompanyContext` + `get_company_ctx` — **client-asserted via `X-Company-Id` / `X-Site-Id` headers; unused by any route** (dead code) |

### 2.2 Tenant data model

- `Company` (companies) and `Site` (FK `company_id`) exist.
- Nullable `company_id` / `site_id` columns exist on ~20 entities, including
  `User`, `Agent`, `integration_profile`, `credential_profile`, `remote_host`,
  `sop`, playbook/command tables, `audit_trail`, `task`, `project`, `note`.
- `AgentRegistrationToken` carries `company_id` / `site_id`, `max_agents`,
  `used_count`, `expires_at` — the sanctioned way to provision an agent into a tenant.
- Important: agents registered before tenancy (and any scoped-by-param routes)
  have `company_id IS NULL`. See legacy rule, §5.1.

### 2.3 Router coverage map (verified 2026-09)

Authenticated (`Depends(get_current_user)` or router-level dependency):

- `routers/agent.py` (CRUD + execute + api-key), `agent_token.py`,
  `agent_remote_target.py`, `ai.py`, `auth.py` (self), `automation.py`,
  `company.py`, `dashboard.py`, `hyperv.py`, `identity.py`, `integration.py`,
  `marketplace.py`, `notes.py`, `parking_lot.py`, `projects.py`, `proxmox.py`,
  `remote.py`, `resume.py`, `site.py`, `tasks.py`, `zabbix.py`
- Plugins: `official_mikrotik/routes.py`, `official_mikrotik/config_routes.py`
  (router-level + per-endpoint `_require_role` guard), `official_dlink/routes.py`
  (router-level + `require_operator` / `require_admin` dependencies)

Unauthenticated (only `Depends(get_db)`):

- `routers/agent.py` **registration/heartbeat/command-result/inventory** (agent →
  server, intentionally public for agents) — **and `/register` is public**
- Plugins: `official_veeam/routes.py`, `official_docker/routes.py`,
  `official_unifi/routes.py`, `zabbix/routes.py`, `git/routes.py`,
  `hyperv/routes.py`

### 2.4 Gaps found

1. **Registration takeover** — `POST /api/v1/agents/register`
   (`routers/agent.py:61-87`) is unauthenticated. If a valid token is supplied it
   is validated + consumed, otherwise `agent_service.register_agent`
   (`services/agent_service.py:67-128`) re-registers an existing hostname and
   **rotates its API key**, returning the new key. Anyone who can reach the API
   can hijack any agent.
2. **Plugin routes unauthenticated** — Veeam, Docker, UniFi, Zabbix, Git, Hyper-V
   REST plugin routers read/write infrastructure credentials (`remote_host`
   secrets, backup servers, etc.) with no auth.
3. **No RBAC/scoping on agent CRUD** — `list_agents`, `/{id}` GET/PUT/DELETE,
   `execute`, `api-key` all require login only. No role checks, no company filter.
   `reveal_api_key` (`/agents/{id}/api-key`) is available to any logged-in user.
4. **Tenancy context is client-asserted and dead** — `get_company_ctx` trusts
   `X-Company-Id`/`X-Site-Id` and treats an absent header as *global*. Header trust
   must never decide scope.
5. **Company/site/token routers have no RBAC** — `company.py` lets any
   authenticated user create/delete companies; `site.py` likewise;
   `agent_token.py` lets any authenticated user mint tokens for any company.
6. **User management privilege escalation** — `routers/auth.py:131-203`:
   `create_user` / `update_user` require only `company_admin+`; a company_admin
   can assign the `global_admin` role (`request.role`) and set an arbitrary
   `site_id` / `company_id`, i.e. cross-tenant writes and privilege grant.
   `delete_user` is not scoped to the caller's company.
7. **Agent API keys stored plaintext** — `_hash_api_key`
   (`services/agent_service.py:55-57`) is dead code; keys are stored raw in the
   `agents.api_key` column. (Out of scope for this pass; see §10.)

---

## 3. Threats & Gaps (ranked)

| # | Severity | Gap |
|---|----------|-----|
| 1 | Critical | Public re-registration rotates any agent's API key |
| 2 | High | Plugin routers expose infrastructure data + credential CRUD unauthenticated |
| 3 | High | Any logged-in user can read any agent's API key and execute commands |
| 4 | High | Tenancy scope asserted by client header (but unused → latent) |
| 5 | Medium | company_admin can escalate to global_admin / create companies / cross-tenant writes |
| 6 | Medium | No company/site filtering on agent/company/site/token listing |

---

## 4. Design Principles

1. **Enforce from the token, not the client.** Company/site scope always derives
   from JWT claims (`cid`/`sid`); never from headers/body. Headers, if present,
   must be ignored or must *match* the token scope.
2. **Authenticate everything by default.** The only truly public routes are the
   agent bootstrap/communication endpoints (registration, heartbeat, command
   result, inventory, `/version`, agent-facing bundle download) and `/setup/*`.
   Plugin routers are user-facing and must require a user token.
3. **Authorize per-resource using a single dependency.** Introduce one helper
   (`require_min_role`) and one scope-verification helper; stop hand-rolling
   ad-hoc guards.
4. **Never loosen shared-with-main tests.** Behavior changes land in app code;
   `test_dashboard.py`, `test_setup_api.py`, `test_integration_management.py`,
   `test_zabbix_provider.py`, `test_startup_config.py` assertions stay green.
5. **Keep agent relay/edge architecture untouched.** Registration token →
   company/site assignment and the `X-Agent-API-Key` authentication for
   `/edge`/`/agents` communication remain as-is.
6. **Legacy NULL = legacy visible.** Entities with `company_id IS NULL` (pre-tenancy)
   stay visible under the rule in §5.1 so the live single-tenant UI does not break.

---

## 5. Target Design

### 5.1 Scope model & legacy-NULL rule

Let `U` be a user with role `R` and claims `cid`, `sid`. Define visibility of an
entity `E` (with `company_id` column) as:

- `R == global_admin` → **all** entities.
- Node `WHERE E.company_id = U.cid`.
- Legacy NULLs: if exactly **one** company exists in `companies`, treat `NULL`
  as owned by that company (production single-tenant case); otherwise `NULL`
  entities are visible only to `global_admin` (orphans).

This is implemented as a single reusable filter helper:

```
def company_scope_filter(user, model) -> BinaryExpression | None
    # None → no filter (global)
```

### 5.2 `CompanyContext` rewrite (`app/core/company_context.py`)

Replace the header-parsing `get_company_ctx` with a dependency that derives
context from the authenticated user:

```
async def get_company_ctx(current_user = Depends(get_current_user)) -> CompanyContext
    CompanyContext(company_id=current_user.company_id,
                   site_id=current_user.site_id,
                   is_global=(current_user.role == "global_admin"))
```

- Remove `X-Company-Id` / `X-Site-Id` trust entirely.
- No callers today → rename semantics for future use only.

### 5.3 RBAC helpers (`app/core/rbac.py`, new)

```
def require_min_role(min_role: str) -> Callable[..., User]
    # FastAPI dependency: resolves current_user, calls
    # require_role(current_user, min_role), returns user.

def enforce_target_scope(user, company_id=None, site_id=None, db=...) -> None
    # Non-global: 404 if company_id/site_id not owned by user's company.
```

Reuse `role_has_min_level`/`require_role` from `auth_service` (no duplication).

### 5.4 Endpoint authorization matrix

| Endpoint | Auth | Min role | Scope |
|----------|------|----------|-------|
| `GET /agents` | user | any | `company_scope_filter` |
| `GET /agents/{id}` | user | any | entity owned |
| `PUT /agents/{id}` | user | company_admin | entity owned |
| `DELETE /agents/{id}` | user | company_admin | entity owned |
| `POST /agents/{id}/execute` | user | operator | entity owned |
| `GET /agents/{id}/api-key` | user | **global_admin** | — |
| `GET/PUT/DELETE /companies*` | user | list/get any (scoped); create/update/delete **global_admin** | scope filter |
| `GET /sites*` | user | any (scoped) | scope filter |
| `POST/PUT/DELETE /sites*` | user | company_admin | non-global confined to own company |
| `GET/POST /agent-tokens` | user | company_admin | non-global: `company_id` pinned to caller company; `site_id` validated in company |
| `POST/DELETE /agent-tokens/{id}*` | user | company_admin | token owned by caller company (non-global) |
| `POST /agents/register` | public | — | token → its company/site (§5.5) |

### 5.5 Registration hardening (`routers/agent.py:61-87`)

Guard stays at the **router** level so the service contract (and its tests)
are untouched:

```
if payload.registration_token:
    validate_token(...) → company_id/site_id → consume_token
else:
    existing = AgentRepository.get_by_hostname(db, payload.hostname)
    if existing is not None:
        raise 403 "re-registration requires a registration_token"
```

New-hostname, token-less registration remains allowed (orchestration agents can
self-register as `company_id=NULL`).

### 5.6 User-management confinement (`routers/auth.py`)

- `create_user`: keep `company_admin+`. Constrain `site_id` to the caller's
  company (when non-global). Role grant rule: a non-global may only create roles
  **strictly below** their own rank (e.g. company_admin → site_admin/operator/
  readonly; never `global_admin` or `company_admin`).
- `update_user`: constrain target user and fields to the caller's company
  (non-global). Block promotions to a rank ≥ caller's rank, except the same
  company_admin cannot self/peer-promote. Block cross-tenant `company_id`/`site_id`.
- `delete_user`: non-global must be in same company; cannot delete a
  `global_admin`; cannot delete a user of equal or higher rank.

### 5.7 Plugin-route authentication

Add router-level `dependencies=[Depends(get_current_user)]` to:
`official_veeam/routes.py`, `official_docker/routes.py`, `official_unifi/routes.py`,
`zabbix/routes.py`, `git/routes.py`, `hyperv/routes.py`.

CI-safe: `backend/tests/conftest.py` overrides `get_current_user` with a fake
`global_admin` when no Bearer token is present, so every test that uses the
`client` fixture passes through the dependency unaffected; `raw_client` (auth
tests only) keeps the real 401 behaviour.

---

## 6. Out of Scope (this pass)

- Agent API key hashing at rest (acknowledged; follow-up).
- Tenant-switch UI, per-tenant dashboards, endpoint scoping for the ~15 other
  `company_id`-carrying entities (notes/projects/tasks/sop/playbooks/…).
- Full role-granularity per plugin action.
- `docs/SECURITY_REVIEW.md` refresh (follow-up; it currently oversells auth).

---

## 7. Implementation Plan

| Phase | Change | Files |
|-------|--------|-------|
| P1 | CompanyContext binds to JWT; drop header trust | `app/core/company_context.py` |
| P2 | RBAC helper module | `app/core/rbac.py` (new) |
| P3 | Registration re-register token guard | `app/routers/agent.py`, `app/repositories/agent_repository.py` (no-op if `get_by_hostname` exists) |
| P4 | Agent endpoint RBAC + scoping | `app/routers/agent.py` |
| P5 | Company/site/agent-token RBAC + scoping | `app/routers/company.py`, `app/routers/site.py`, `app/routers/agent_token.py` |
| P6 | User-management confinement | `app/routers/auth.py` |
| P7 | Plugin-route auth | veeam/docker/unifi/zabbix/git/hyperv `routes.py` |
| P8 | Verify + commit/push from `/opt/MissionControl` | — |

Each phase keeps ruff + pytest green; full pytest runs on the server (see §8).

---

## 8. Test & CI Strategy

- Run per-phase: `ruff check` on changed files + targeted pytest
  (`test_agent_management.py`, `test_company_api.py`, `test_site_api.py`,
  `test_auth_api.py`, `test_execute_agent_relay.py`, `test_edge_bundle.py`).
- Final: full `python -m pytest tests/ -q --tb=short` (server venv) + frontend
  `tsc && vite build`.
- CI gotchas that protect this work: conftest `_override_auth` fake `global_admin`
  (`client` fixture) makes every added `get_current_user` dependency effectively
  a global-admin passthrough in tests → no existing test regressions from P7/P4;
  service-layer `test_register_existing_hostname` is untouched because the guard
  is router-level (P3).
- Extra negative tests to add: re-register without token → 403; company_admin
  (real-token flow) scoping assertions.

---

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| Legacy-NULL agents become invisible and break the live dashboard | §5.1 rule keeps NULLs visible in single-company deployments (production) |
| Frontend calls a now-authenticated plugin route without a token | Frontend uses the authed `apiClient` for all plugin routes (verified in the eb14e8a fix) |
| Role checks on agent CRUD break automation that calls API as non-global | Production operator is global_admin; scoping only *restricts* to caller company |
| Test count churn from new guards | Prioritize router-level guards; keep service tests intact |

---

## 10. Follow-ups

- Hash agent API keys at rest (`_hash_api_key` exists but unused).
- Refresh `docs/SECURITY_REVIEW.md` to match this design after implementation.