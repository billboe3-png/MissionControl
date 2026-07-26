# Security Policy

The Mission Control team takes security seriously. This document describes our security policies, supported versions, how to report vulnerabilities, and the security features built into the platform.

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported | End of Life |
|---------|:---------:|:-----------:|
| 3.0.x   | ✅ Active | TBD         |
| 2.0.x   | ✅ Maintenance | 2026-12-31 |
| 1.0.x   | ❌ EOL    | 2025-12-31  |

We recommend always running the latest stable release. See [CHANGELOG.md](CHANGELOG.md) for details on each release.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue in Mission Control, please report it responsibly through one of the following channels:

### Email

Send a detailed report to **[security@missioncontrol.dev](mailto:security@missioncontrol.dev)**.

### GitHub Security Advisories

Use the [GitHub Security Advisory](https://github.com/billboe3-png/MissionControl/security/advisories/new) form for private vulnerability reporting.

### What to Include

Your report should include:

- **Description** of the vulnerability and its potential impact
- **Steps to reproduce** the issue
- **Affected versions**
- **Proof of concept** (code, screenshots, or logs) if possible
- **Suggested fix** if you have one

### What to Expect

- **Acknowledgment** within 48 hours of your report
- **Status update** within 7 business days with initial assessment
- **Resolution timeline** communicated once the issue is confirmed
- **Credit** in the release notes (unless you prefer anonymity)

We follow a 90-day disclosure deadline. If a fix is not ready within 90 days, we will coordinate with the reporter on an disclosure timeline.

---

## Security Update Process

1. A vulnerability report is received and triaged by the security team.
2. A private fix branch is created, and the fix is developed and tested.
3. The fix is reviewed by at least one additional maintainer.
4. A patched release is published.
5. A GitHub Security Advisory is published simultaneously with the release.
6. Users are notified through:
   - GitHub Release notes
   - Security mailing list (if subscribed)
   - Repository README banner for critical issues

### Backporting

Critical and high-severity fixes are backported to all supported maintenance branches (currently 2.0.x). Low and moderate severity fixes are applied to the active release only.

---

## Security Features

### Authentication & Authorization

- JWT-based authentication with configurable token expiry
- Role-based access control (RBAC) with granular permissions
- API key authentication for programmatic access and agent communication
- Account lockout after configurable failed login attempts

### Agent Communication

- Agents authenticate to the server using unique, rotating API keys
- Agent commands are signed and verified to prevent tampering
- Heartbeat traffic is encrypted in transit (TLS required)
- Agent configuration stored with restricted filesystem permissions

### Data Protection

- Sensitive configuration values are encrypted at rest using AES-256
- Database connections require TLS in production configurations
- Secrets are never written to application logs
- Credential input fields are masked in the UI

### API Security

- All API endpoints require authentication (public endpoints explicitly marked)
- Rate limiting on authentication endpoints
- CORS configured per-environment — no wildcard origins in production
- Input validation on all API parameters (Pydantic models)
- SQL injection prevention via SQLAlchemy parameterized queries

### Audit Logging

- All administrative actions are recorded in the audit log
- Agent command execution is logged with operator identity and timestamp
- Login events (success and failure) are recorded
- Audit logs are append-only and tamper-evident

### Plugin Security

- Plugins run in a sandboxed context with restricted filesystem access
- Plugin permissions are declared and must be approved by an administrator
- Plugin code is scanned for known vulnerabilities before installation
- Plugins cannot access other plugins' data or configurations

---

## Threat Model

### In Scope

| Attack Surface | Description |
|----------------|-------------|
| Web UI | XSS, CSRF, clickjacking, authentication bypass |
| API | Injection (SQL, command, template), broken authentication, IDOR |
| Agent Protocol | Command injection, replay attacks, spoofing |
| Plugin System | Sandbox escape, privilege escalation, data exfiltration |
| Data Storage | Unauthorized access, data leakage, injection |
| Infrastructure | Container escape, network interception, secrets exposure |

### Out of Scope

- Denial-of-service attacks against public instances
- Social engineering of Mission Control staff
- Vulnerabilities in third-party dependencies (report these upstream, then notify us)
- Physical security of deployment infrastructure

### Asset Classification

| Asset | Sensitivity |
|-------|------------|
| Agent credentials | Critical |
| User credentials / tokens | Critical |
| Audit logs | High |
| Agent command history | High |
| System inventory data | Medium |
| Playbook definitions | Medium |
| Plugin configurations | Low–Medium |

---

## Security Contact

| Channel | Contact |
|---------|---------|
| Security email | [security@missioncontrol.dev](mailto:security@missioncontrol.dev) |
| GitHub Advisories | [Report a vulnerability](https://github.com/billboe3-png/MissionControl/security/advisories/new) |
| General inquiries | [security@missioncontrol.dev](mailto:security@missioncontrol.dev) |

For non-security issues, please use [GitHub Issues](https://github.com/billboe3-png/MissionControl/issues).

---

## Compliance

Mission Control Enterprise Edition provides additional compliance features:

- SOC 2 Type II audit support
- GDPR data subject request tooling
- HIPAA-ready logging and access controls
- Custom retention policies for audit and operational data

These features are not available in the Community Edition. See [SUPPORTED_PLATFORMS.md](SUPPORTED_PLATFORMS.md) for edition comparison.

---

## Acknowledgments

We感谢 the security research community for responsibly disclosing vulnerabilities. Contributors who report valid security issues will be credited in the release notes unless they request anonymity.
