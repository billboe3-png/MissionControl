# GitHub Repository Audit

Repository: `billboe3-png/MissionControl`
Audited path: `/opt/MissionControl`
Date: 2026-08-22
Auditor: Dexter / Hermes Agent

## Repository Overview

- **Remote:** `git@github.com:billboe3-png/MissionControl.git`
- **Visibility:** Public
- **GitHub default branch:** `develop`
- **Local branches:** `main`, `develop`, `release/v3.0.0-rc1`
- **Remote branches:** `develop`, `release/v3.0.0-rc1`
- **Tags:** v0.1.0, v0.1.1, v0.2.0, v0.2.4, v1.0.0-backend, v1.0.0-rc1, v1.0.2, v2.0.1, v2.1.0, v3.0.0, v3.1.0
- **Tracked files:** 1,185
- **Ignored/untracked:** 9,839

## Security Findings

### SECURITY-FINDING-001: Large binary artifacts tracked in Git

**What:** 24+ ZIP archives under `.agents/` including live agent bundles and version histories.  
**Where:** `.agents/agent-bundle-*.zip`, `.agents/corhqrobertb-reinstall.zip`  
**Risk:** Medium. Binaries bloat repository size, slow clone/fetch, and may embed environment-specific credentials or internal hostnames. These are build artifacts, not source.  
**Recommended action:** Remove tracked binaries from Git; serve via GitHub Releases or external artifact store. Add `.agents/*.zip` and `.agents/*.version` to `.gitignore`.

### SECURITY-FINDING-002: Top-level data files in repo root

**What:** `note.json`, `parking.json`, `parking-update.json`, `put-dup.json` appear to be operational data dumps.  
**Where:** repo root  
**Risk:** Low-medium. May contain PII, site data, or internal identifiers.  
**Recommended action:** Review contents. If they are test/seed data, move to `scripts/seed/` or `.gitignore` and generate at deploy time.

### SECURITY-FINDING-003: `.env` is local-only but docs reference it

**What:** `.env` exists on host and is gitignored, but deployment docs do not explicitly warn against committing it.  
**Risk:** Low. Current `.gitignore` already blocks `.env`.  
**Recommended action:** Add explicit warning in `.env.example` header: "Never commit `.env`."

## Audit Classifications

### KEEP

| Path | Reason |
|------|--------|
| `backend/app/` | Core backend source |
| `frontend/src/` | Core frontend source |
| `backend/alembic/` | Database migration history |
| `backend/tests/`, `frontend/src/...` | Test suites |
| `.github/workflows/ci.yml` | Active CI |
| `.github/workflows/release-validation.yml` | Active validation |
| `nginx/default.conf` | Live nginx config |
| `docs/` | Documentation |
| `scripts/backup-db.ps1`, `scripts/validate_backup.sh` | Operational scripts |
| `DEPLOYMENT.md`, `docs/architecture/DEPLOYMENT.md` | Deployment references |
| `VERSION`, `CHANGELOG.md`, `RELEASE_NOTES*.md` | Release metadata |
| `.env.example` | Template with placeholder values only |

### REMOVE

| Path | Reason | Dependency | Risk | Action |
|------|--------|-----------|------|--------|
| `.agents/agent-bundle-*.zip` | Build artifacts, ~8MB, do not belong in source control | Agent packaging workflow may expect these present locally for `edge bundle download` endpoint | Medium | Remove from Git tracking; keep local files for runtime |
| `.agents/agent-bundle-live.version` | Derived artifact | Low | Low | Remove from Git tracking |
| `.agents/corhqrobertb-reinstall.zip` | Host-specific artifact | Low | Low | Remove from Git tracking |
| `note.json`, `parking.json`, `parking-update.json`, `put-dup.json` | Unclear operational data files at repo root | Unknown; may be referenced by ad-hoc scripts | Medium | Review contents; likely remove from Git |

### ARCHIVE

| Path | Reason | Action |
|------|--------|--------|
| `docs/reference/DEPLOYMENT_AWS.md` | Future architecture, not active | Move to `docs/archive/` |
| `docs/reference/DEPLOYMENT_AZURE.md` | Future architecture, not active | Move to `docs/archive/` |
| `docs/reference/DEPLOYMENT_KUBERNETES.md` | Future architecture, not active | Move to `docs/archive/` |
| `docs/reference/DEPLOYMENT_PROXMOX.md` | Proxmox LXC deployment, may still be relevant | Keep under REVIEW first |
| `docs/reference/DEPLOYMENT_GCE.md` | Superseded by live deployment on `optihosting.co.za` | Archive after confirming no unique instructions |
| `PLAN-agent-relay.md` | Sprint plan artifact | Move to `docs/archive/plans/` |
| `RELEASE_NOTES_v1.0.md` | Superseded by `RELEASE_NOTES.md`/`CHANGELOG.md` | Move to `docs/archive/` |
| Old tags `v0.*`, `v1.0.0-backend`, `v1.0.0-rc1` | Pre-RC1 history | Retain; do not delete tags |

### REVIEW

| Path | Question |
|------|----------|
| `docs/architecture/DEPLOYMENT.md` | References `docker-compose.prod.yml` which does not exist. Update or remove reference. |
| `docs/reference/DEPLOYMENT_DOCKER.md` | May overlap with `DEPLOYMENT.md`. Consolidate? |
| `docs/deployment/edge-proxy-deployment.md` | Active? |
| `backend/debug/` | Contains debug scripts (`install-agent.bat`, `fix_agent_version.py`). Should these be in repo? |
| `.agents/reinstall-tmp/` | Temporary extraction directory accidentally committed? |
| `.agents/packaging/` | Installer packaging scripts; needed for release or local only? |
| `AGENT_DEPLOYMENT.md` | Mixes deployment docs with agent-specific content. Split or consolidate? |
| `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SUPPORTED_PLATFORMS.md` | Are these up to date and actively maintained? |

## Git Hygiene Issues

1. **Default branch mismatch:** GitHub default is `develop`, but deployment docs reference `main` as production. This is workable, but must be explicit in policy docs.
2. **Missing `main` remote:** `main` exists locally but is not on remote. If `main` is the LIVE branch, it must be pushed and protected.
3. **Release branches:** `release/v3.0.0-rc1` exists locally and remotely. No release branch policy is documented.
4. **No branch protection rules visible in repo:** Must configure required status checks, review, and linear history on `main`.

## Recommended Immediate Actions

1. Push `main` to remote and set it as a protected production branch, or align policy to use `develop` as the integration branch and `main` as the explicit promotion target.
2. Remove tracked agent bundle ZIPs from Git history using `git filter-repo` or BFG, then add patterns to `.gitignore`.
3. Add `.agents/*.zip`, `.agents/*.version`, `note.json`, `parking*.json`, `put-dup.json` to `.gitignore`.
4. Create `.env.dev.example` and `.env.production.example` with clearly separated values.
5. Remove reference to nonexistent `docker-compose.prod.yml` from docs, or create it as part of the two-environment deployment work.
