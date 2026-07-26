# Supported Platforms

Mission Control is tested and supported on the platforms listed below. Community Edition users receive community-level support; Enterprise Edition customers receive priority support with guaranteed SLAs.

---

## Operating Systems

### Server (API & Database)

| OS | Version | Community | Enterprise |
|----|---------|:---------:|:----------:|
| Ubuntu | 22.04 LTS | ✅ | ✅ |
| Ubuntu | 24.04 LTS | ✅ | ✅ |
| Debian | 12 (Bookworm) | ✅ | ✅ |
| Rocky Linux | 9.x | ✅ | ✅ |
| Amazon Linux | 2023 | ✅ | ✅ |
| Windows Server | 2022 | ⚠️ | ✅ |
| macOS | 14 (Sonoma) | ⚠️ (dev only) | ❌ |

> ⚠️ Windows Server and macOS are supported for development and testing only. Production deployments should use Linux.

### Agent

| OS | Version | Community | Enterprise |
|----|---------|:---------:|:----------:|
| Ubuntu | 20.04+ | ✅ | ✅ |
| Debian | 11+ | ✅ | ✅ |
| Rocky Linux | 8.x / 9.x | ✅ | ✅ |
| Amazon Linux | 2 / 2023 | ✅ | ✅ |
| CentOS | Stream 9 | ✅ | ✅ |
| RHEL | 8.x / 9.x | ⚠️ | ✅ |
| Windows Server | 2019+ | ✅ | ✅ |
| Windows 10/11 | 22H2+ | ⚠️ | ✅ |
| macOS | 13+ | ⚠️ | ✅ |
| Alpine Linux | 3.18+ | ✅ | ✅ |

> Agents require Python 3.12 (bundled or system-installed). No external dependencies are needed.

---

## Browsers

The Mission Control frontend is tested in the following browsers:

| Browser | Version | Community | Enterprise |
|---------|---------|:---------:|:----------:|
| Google Chrome | 120+ | ✅ | ✅ |
| Mozilla Firefox | 120+ | ✅ | ✅ |
| Microsoft Edge | 120+ | ✅ | ✅ |
| Safari | 17+ | ✅ | ✅ |
| Chromium (non-Chrome) | Latest | ⚠️ | ⚠️ |
| Mobile Chrome | Latest | ⚠️ | ⚠️ |
| Mobile Safari | Latest | ⚠️ | ⚠️ |

> ⚠️ = Functional but not fully tested. Internet Explorer is not supported.

---

## Container & Orchestration

| Platform | Version | Community | Enterprise |
|----------|---------|:---------:|:----------:|
| Docker | 24.0+ | ✅ | ✅ |
| Docker Compose | v2.20+ | ✅ | ✅ |
| Kubernetes | 1.28+ | ✅ | ✅ |
| Podman | 4.0+ | ⚠️ | ✅ |
| Helm | 3.12+ | ✅ | ✅ |

### Docker Images

Official images are published to GitHub Container Registry:

```
ghcr.io/billboe3-png/missioncontrol/server:3.0.0
ghcr.io/billboe3-png/missioncontrol/agent:3.0.0
ghcr.io/billboe3-png/missioncontrol/frontend:3.0.0
```

---

## Databases

| Database | Version | Community | Enterprise |
|----------|---------|:---------:|:----------:|
| PostgreSQL | 16 | ✅ (recommended) | ✅ |
| PostgreSQL | 15 | ✅ | ✅ |
| PostgreSQL | 14 | ⚠️ | ✅ |

> PostgreSQL 16 is the primary tested version. All migrations and queries are validated against PostgreSQL 16. Older versions may work but are not guaranteed.

---

## Cache & Message Broker

| Software | Version | Community | Enterprise |
|----------|---------|:---------:|:----------:|
| Redis | 7.2+ | ✅ | ✅ |
| Redis | 7.0 | ✅ | ✅ |
| Redis Sentinel | 7.x | ⚠️ | ✅ |
| Redis Cluster | 7.x | ❌ | ✅ |

---

## Runtime Requirements

### Backend

| Dependency | Minimum | Recommended |
|------------|---------|-------------|
| Python | 3.12.0 | 3.12.4+ |
| pip | 23.0 | Latest |
| Alembic | 1.13 | Latest |
| Uvicorn | 0.30 | Latest |

### Frontend

| Dependency | Minimum | Recommended |
|------------|---------|-------------|
| Node.js | 20.0 | 20.12+ |
| npm | 10.0 | 10.5+ |
| Vite | 5.0 | 5.4+ |

---

## Cloud Providers

| Provider | Support Level | Notes |
|----------|:------------:|-------|
| Google Cloud (GCE) | ✅ Full | One-click deploy scripts included |
| AWS (EC2 / ECS / EKS) | ✅ Full | Terraform modules in `deploy/terraform/` |
| Azure (AKS) | ✅ Full | Terraform modules in `deploy/terraform/` |
| DigitalOcean | ⚠️ Community | Manual setup; community guides available |
| Fly.io | ⚠️ Community | Manual setup; community guides available |

---

## Support Levels

### Community (Open Source)

- GitHub Issues with best-effort response
- Community Slack / Discussions
- No guaranteed response time
- No backport guarantees for older versions

### Enterprise (Commercial)

- Dedicated support portal with SLA
- 4-hour response for critical issues (24/7)
- 1-business-day response for high-priority issues
- Backported security fixes for supported maintenance branches
- Custom deployment assistance
- Phone and video support available
