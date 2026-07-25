# Roadmap

## v3.0.0 — Production Release (Current)
- JWT authentication on all API endpoints
- Rate limiting and security hardening
- N+1 query fixes and performance optimization
- Docker production compose with resource limits
- GitHub Actions CI/CD pipeline
- Backup/restore scripts
- Agent relay system for Hyper-V, Proxmox, Veeam, Zabbix, AD, M365
- Agent plugins: Zabbix (JSON-RPC), AD (LDAP), M365 (Graph API)
- Agent remote collectors: Proxmox (SSH/pvesh), Veeam (PowerShell)

## Upcoming
### Monitoring & Observability
- Extended Zabbix/Proxmox/Hyper-V dashboard coverage
- Alerting and notification channels (email, webhook, Slack)
- Custom metric collection and graphing

### Identity & Access Management
- Expanded Azure AD / M365 integration
- Role-based access control (RBAC)
- SSO/SAML support

### Automation & AI
- Advanced automation workflows with conditional branching
- AI-powered operations assistant (expanded)
- Infrastructure-as-Code integration (Terraform, Ansible)
