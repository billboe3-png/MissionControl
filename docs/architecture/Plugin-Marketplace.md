# Plugin Marketplace

## Plugin Categories

### Server Plugins
| Category | Examples |
|----------|----------|
| Monitoring | Zabbix, Grafana, Prometheus, PRTG |
| Virtualization | Hyper-V, Proxmox, VMware, Nutanix |
| Cloud | Azure, AWS, Google Cloud |
| Identity | Active Directory, Entra ID, Okta, LDAP |
| DevOps | GitHub, GitLab, Jira, ServiceNow |
| Backup | Veeam, Nakivo, Synology |
| Database | SQL Server, PostgreSQL, MySQL, MongoDB |
| Communication | Slack, Teams, Discord, Email, SMS |

### Agent Plugins
| Category | Examples |
|----------|----------|
| Remote Access | TeamViewer, RustDesk, MeshCentral, VNC, RDP |
| Windows | Event Logs, Services, Registry, Updates, Defender |
| Linux | Systemd, Cron, Services |
| Monitoring | SMART Disk, Performance Counters, GPU, USB |
| Inventory | Hardware, Software, Certificates |
| Collection | Files, Logs, Events |

### Hybrid Plugins
| Category | Examples |
|----------|----------|
| Remote Desktop | Remote Desktop Hub |
| Security | Security Audit, Endpoint Compliance, Vulnerability Scanning |
| Patch Management | Patch Management, Update Compliance |
| Backup | Backup Verification |
| Inventory | Inventory Management, Certificate Management |

## Marketplace Entry Fields

Each plugin in the marketplace displays:
- **Slug**: Unique identifier
- **Name**: Display name
- **Version**: Semantic version
- **Description**: What the plugin does
- **Author**: Publisher name
- **Execution Target**: server / agent / hybrid
- **Category**: Functional category
- **Permissions**: Required permissions
- **Dependencies**: Required plugins
- **Min Core Version**: Minimum Mission Control version
- **Installed**: Whether currently installed
- **Health**: Current health status (if installed)

## Certification Process

1. Plugin submitted to marketplace
2. Automated validation (manifest, manifest schema, permissions)
3. Security review (no dangerous patterns, proper SDK usage)
4. Compatibility testing against current core version
5. Documentation review
6. Approval and publishing

## Publishing

- Official plugins: Published by Mission Control team
- Certified plugins: Published after review process
- Community plugins: Self-published with automated validation
- Private plugins: Organization-internal, not published
