# Destination Diff — Source Revision, Working Tree, Per-Host Configuration

**Status:** Phase 2 design + executed *repository-only* preservation (no host or production change).
**Labels:** **[V]** verified · **[A]** assumption · **[?]** unresolved · **[R]** recommendation.

This document exists because production does **not** run a clean, committed tree. It records exactly
what runs today, what was preserved, what is excluded, and how each host's configuration must differ.

---

## 1. Source revision

| Item | Value |
|---|---|
| Repository (authoritative) | `/opt/MissionControl` on `34.35.177.209` [V] |
| Branch | `release/v3.0.0-rc1` [V] |
| Application commit before migration work | `ca2d267` (Phase 1 recorded this) [V] |
| Current HEAD (Phase 1 docs) | `601a878` — docs only, **not pushed** [V] |
| Live-config snapshot commit | `75a8280` on branch `migration/prod-live-snapshot-2026-10-20` [V, created 2026-10-20] |
| Local Windows checkout | divergent line `8b996bd` with unrelated WIP — **not** a deployment source [V] |
| Deploy revision rule | every deployment records `git rev-parse HEAD` **and** `sha256sum` of the deployed compose/nginx files in `execution-log.md` |

**Important:** the running backend uses a **bind mount** (`./backend:/app`), so the *working tree* —
not the image contents — defines the running application code. The image tag alone is not a
reproducible description of production.

---

## 2. Working tree captured on 2026-10-20

### 2.1 Modified tracked files

| File | sha256 (live) | Meaning |
|---|---|---|
| `docker-compose.yml` | `d4e9685b01503bd31a3bd21b418670314fd42db439fd1ca94ade05f862ac5ca4` | +20/−1 lines: adds `dockhand` service + volume, publishes `3000:3000`, adds `/health` check, passes `DOCKERHAND_SECRET` fallback |
| `nginx/default.conf` | `734f40e45c1ce3ff0b4ac3871c2fbc21dae83af2910f2c5da611126c2e747505` | +42/−4 lines: adds `/dockhand/` proxy + sub_filter rewriting + redirect, cipher list, websocket timeouts |

### 2.2 Untracked files (13 entries)

| Path | Size | Classification | Rationale |
|---|---|---|---|
| `backend/app/plugins/installed/official_veeam/agent_remote_target.py` | small | **EXCLUDE (dead duplicate)** | Defines the same table as the **tracked** `backend/app/models/db/agent_remote_target.py`. Verified: **no module imports the plugin-local copy**; the only references are the tracked model and cache artefacts. Not required at runtime. **[V]** |
| `backend/tests/test_agent_token_service.py` | small | EXCLUDE (unverified) | Untracked test; not executed during this phase (test runs are a Phase 3/CI action) |
| `backend/tests/test_veeam_collector.py` | small | EXCLUDE (unverified) | Same |
| `backend/tests/test_veeam_column_case.py` | small | EXCLUDE (broken) | Imports a symbol that does not exist in the tracked code |
| `.agents/Install-MissionControl-Agent.cmd` | 4 KB | EXCLUDE (artifact) | Agent installer script, not part of the server |
| `.agents/*.zip`, `.agents/*.zip.2026-10-20` | 100 KB–2 MB | EXCLUDE (artifact) | Built agent bundles and dated copies |
| `.agents/agent/plugins/veeam_plugin.py.new` | small | EXCLUDE (WIP) | Superseded plugin draft |
| `deploy/2vm/` | small | EXCLUDE (superseded) | Earlier OCI scaffold; conflicts with this design; kept for reference only |
| `installer/msi/build/`, `installer/msi/output/` | varies | EXCLUDE (build output) | Windows installer artefacts |

**Correction to the Phase 1 audit (§3 / R5):** Phase 1 recorded that the backend *imports* the untracked
`official_veeam/agent_remote_target.py`, and that a git-only deploy would break at import. Re-verification
for Phase 2 found no importer: `grep -rn agent_remote_target backend` returns only the tracked model
definition and its importers. The runtime dependency claim was **wrong**; `audit-report.md` has been
corrected. Consequence: the destination needs the working tree for **parity**, not because of this file.

### 2.3 What was preserved

- Commit `75a8280` on `migration/prod-live-snapshot-2026-10-20` contains the **exact live**
  `docker-compose.yml` and `nginx/default.conf`, created in a temporary worktree so the running checkout
  was never touched. Verified afterwards: live branch still `release/v3.0.0-rc1`, same two modified files,
  same sha256 values.
- The snapshot is a **provenance record only**; it is not a deployment target and must not be checked out
  on a destination.
- Secrets: `docker-compose.yml` contains no literal credential — only
  `${MISSIONCONTROL_SECRET_KEY:?…}` and dockhand's weak default fallback `changeme-dockhand-secret`
  (a default, not a live credential; flagged for removal). `nginx/default.conf` contains no secrets. **[V]**
- `.env` is **not tracked** and is not in the snapshot. `.env.production` *is* tracked; its key value
  differs from the live key (compared by hash only — **no secret value was printed**) **[V]**. It is not
  used at runtime; see §6 hygiene item.

### 2.4 Protected copy (not yet executed)

The git snapshot is the protected copy. An additional filesystem copy is optional and **has not been
created**; if wanted before cutover:

```bash
cd /opt/MissionControl
tar -czf ~/migration-baseline-2026-10-20.tar.gz \
    docker-compose.yml nginx/default.conf .env .env.production \
    backend/app/plugins/installed/official_veeam/agent_remote_target.py
sha256sum ~/migration-baseline-2026-10-20.tar.gz
```

Note: that archive would contain secrets and must stay `600` and off Git.

---

## 3. Deployment source for the destinations

Two branches, two purposes — do not mix them:

| Branch | Content | Purpose |
|---|---|---|
| `migration/prod-live-snapshot-2026-10-20` (`75a8280`) | live compose + nginx as-is | provenance / diff baseline |
| `migration/2vm-deploy` (created in Phase 3) | Phase 3 additions: split compose files, target nginx config, env templates, deploy/validate scripts | **the only deployment source** |

Rules:

1. The destination receives the working tree of `migration/2vm-deploy` **plus** the untracked
   environment files (`.env`) over a secure channel — never a bare `git clone` of `release/*`.
2. No secret value enters Git. Env templates contain key names and placeholder markers only.
3. Every host records the deployed revision (`git rev-parse HEAD`) and file hashes.
4. The snapshot branch is never pushed to `release/v3.0.0-rc1` and never merged.

---

## 4. Per-host configuration differences

### 4.1 Services present

| Service | Source | FE | BE | Note |
|---|---|---|---|---|
| `nginx` | yes | **yes** | no | edge only |
| `frontend` | yes | **yes** | no | static SPA |
| `backend` | yes | no | **yes** | |
| `postgres` | yes | no | **yes** | no published port |
| `redis` | yes | no | **yes** | no published port |
| `dockhand` | yes | **no** | **no** | D-B: not migrated |
| host edge agent | yes | no | no | D-C: not migrated (retires with source host) |

### 4.2 `docker-compose.yml` differences

| Live | FE target | BE target |
|---|---|---|
| one file, six services | `docker-compose.frontend.yml`, two services | `docker-compose.backend.yml`, three services |
| `nginx` publishes `80`, `443` and `3000` | publishes `80`, `443` only | n/a |
| backend `ports: 8000:8000` (all interfaces) | n/a | `10.0.0.33:8000:8000` **only** |
| `depends_on` backend/frontend/dockhand | `nginx → frontend` (same host) | `backend → postgres, redis` (healthy) |
| `SESSION_SECRET` for dockhand | removed | removed |
| `MISSIONCONTROL_SECRET_KEY` inline **and** in `.env` | n/a | `.env` only (single source of truth) |
| no `logging:` stanza | `max-size 10m`, `max-file 3` | same |
| bind `./backend:/app`, `.:/project` | n/a | both retained (parity) |
| `docker.sock` rw | **absent** | retained (parity; hardening item) |
| `POSTGRES_HOST=postgres`, `REDIS_HOST=redis` | n/a | unchanged (compose DNS) |

### 4.3 `nginx/default.conf` differences

| Element | Live | FE target | Reason |
|---|---|---|---|
| `upstream /api/` | `backend:8000` | `10.0.0.33:8000` | cross-host |
| `/dockhand/`, `/dockhand` redirect, `sub_filter` lines | present | **removed** | D-B |
| `/health` static 200 | present | kept (harmless) but **healthcheck uses `/api/v1/health/live`** | the static check cannot detect API failure |
| `/.well-known/acme-challenge/` | absent | added **before** the 301 | renewal without stopping nginx |
| cipher list, TLS protocols, websocket headers, 3600 s timeouts, `client_max_body_size`, buffering | live values | unchanged | preserve behaviour |
| `server_name`, certificate paths | `missioncontrol.optichosting.co.za`, `/etc/letsencrypt/live/...` | unchanged | |
| port 80 block | 301 → https | 301 → https, with ACME exception | |

### 4.4 Environment (key names only — no values)

| Key | Source | FE | BE |
|---|---|---|---|
| `MISSIONCONTROL_SECRET_KEY` | inline + `.env` | — | `.env`, **byte-identical** to source, mode 600 |
| `POSTGRES_DB/USER/PASSWORD` | `.env` | — | `.env` |
| `POSTGRES_HOST/PORT` | `.env` (`localhost` host-pinned via `/etc/hosts`) | — | `postgres` / `5432` |
| `REDIS_HOST/PORT` | `.env` (`redis`) | — | `redis` / `6379` |
| `BACKEND_CORS_ORIGINS` | `.env` | — | kept as-is |
| `PROJECT_DIR` | compose (`/project`) | — | `/project` (repo mount) |
| `DOCKER_HOST` | compose (`unix:///var/run/docker.sock`) | — | same |
| `SSH_AUTO_ADD_HOST_KEYS` | compose (`true`) | — | same |
| `DOCKERHAND_SECRET` | compose fallback | **dropped** | **dropped** |
| `/etc/hosts` `redis`/`postgres` pins | present (CI workaround) | **do not copy** | **do not copy** |

---

## 5. Image provenance (D-A)

| Image | Built where | Transfer | Tag |
|---|---|---|---|
| backend | operator workstation (Docker 29.8.2, 8.1 GB RAM) **[V]** | `docker save \| gzip \| ssh docker load` | `missioncontrol-backend:<sha>-<date>` |
| frontend | same workstation (node build stage inside Docker) | same | `missioncontrol-frontend:<sha>-<date>` |
| nginx / postgres / redis | pulled on host, **pinned by digest** equal to source | registry | digest |

Build inputs: the **working tree of `migration/2vm-deploy`** at a recorded commit, with `.env` excluded
from the build context check. Images are loaded *before* compose up; no build happens on a 956 MB VM.

---

## 6. Hygiene items found while producing this diff (not migration blockers)

| Item | Risk | Recommendation | Phase |
|---|---|---|---|
| `.env.production` is **tracked** in Git (value differs from live) | secret-shaped values in history; confusion about which env is real | inspect, then remove from the repo in a separate, reviewed change | separate work item |
| dockhand default `changeme-dockhand-secret` in compose | weak default; unauthenticated UI | disappears with D-B | with D-B |
| `.env` mode `664` on source | local users can read the Fernet key | 600 on destinations; 600 on source is a separate fix | destination now, source separately |
| untracked installer `.zip` files in repo root | bloat/confusion | leave; exclude from deploy | — |
| `deploy/2vm/` untracked scaffold | ambiguity about which compose is real | do not deploy; superseded by `deploy/migration-2vm/` | Phase 3 |

---

## 7. Verification of this document's actions

| Claim | How verified |
|---|---|
| Snapshot contains exactly the live files | `git show --stat 75a8280` → 2 files, +58/−4, matching `git diff --stat` on the live tree |
| Live checkout untouched | post-check `git rev-parse --abbrev-ref HEAD` = `release/v3.0.0-rc1`; `git status --porcelain` unchanged; sha256 identical to pre-check |
| No secret committed | keyword scan of both files; only env references and a documented default |
| Plugin-local module unused | `grep -rn agent_remote_target backend --include=*.py` → no importer of the plugin copy |
