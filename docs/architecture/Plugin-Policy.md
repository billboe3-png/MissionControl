# Plugin Policy — Mandatory Plugin Categories

Every vendor-specific integration MUST be implemented as a plugin. This document defines the complete list.

## Monitoring
| Plugin | Target | Description |
|--------|--------|-------------|
| Zabbix | Server | Zabbix API integration |
| PRTG | Server | PRTG Network Monitor integration |
| Grafana | Server | Grafana dashboard embedding |
| Prometheus | Server | Prometheus metrics queries |
| Datadog | Server | Datadog APM and monitoring |
| Nagios | Server | Nagios Core integration |

## Cloud
| Plugin | Target | Description |
|--------|--------|-------------|
| Azure | Server | Azure resource management |
| AWS | Server | AWS resource management |
| Google Cloud | Server | GCP resource management |

## Identity
| Plugin | Target | Description |
|--------|--------|-------------|
| Active Directory | Server | AD/LDAP integration |
| Microsoft Entra ID | Server | Azure AD / Entra ID |
| Okta | Server | Okta SSO integration |
| Ping Identity | Server | PingFederate integration |

## Virtualization
| Plugin | Target | Description |
|--------|--------|-------------|
| Hyper-V | Server | Hyper-V VM management |
| Proxmox | Server | Proxmox VE management |
| VMware | Server | vSphere/ESXi management |
| Nutanix | Server | Nutanix AHV management |

## Containers
| Plugin | Target | Description |
|--------|--------|-------------|
| Docker | Server | Docker container management |
| Kubernetes | Server | K8s cluster management |
| OpenShift | Server | Red Hat OpenShift management |

## Networking
| Plugin | Target | Description |
|--------|--------|-------------|
| Cisco | Server | Cisco IOS/NX-OS management |
| Fortinet | Server | FortiGate firewall management |
| MikroTik | Server | RouterOS management |
| UniFi | Server | UniFi network management |
| pfSense | Server | pfSense firewall management |

## Remote Desktop
| Plugin | Target | Description |
|--------|--------|-------------|
| TeamViewer | Agent | TeamViewer remote access |
| RustDesk | Agent | RustDesk remote access |
| MeshCentral | Agent | MeshCentral remote access |
| VNC | Agent | VNC remote access |
| RDP | Agent | Windows Remote Desktop |

## Backups
| Plugin | Target | Description |
|--------|--------|-------------|
| Veeam | Server | Veeam B&R integration |
| Nakivo | Server | Nakivo Backup integration |
| Synology | Server | Synology Hyper Backup |

## Databases
| Plugin | Target | Description |
|--------|--------|-------------|
| SQL Server | Server | SQL Server monitoring |
| PostgreSQL | Server | PostgreSQL monitoring |
| MySQL | Server | MySQL monitoring |
| MongoDB | Server | MongoDB monitoring |
| Redis | Server | Redis monitoring |
| RabbitMQ | Server | RabbitMQ monitoring |

## ITSM
| Plugin | Target | Description |
|--------|--------|-------------|
| Jira | Server | Jira issue tracking |
| ServiceNow | Server | ServiceNow ITSM |
| Freshservice | Server | Freshservice ITSM |

## Communication
| Plugin | Target | Description |
|--------|--------|-------------|
| Slack | Server | Slack notifications |
| Microsoft Teams | Server | Teams notifications |
| Discord | Server | Discord notifications |
| Email | Server | Email notifications |
| SMS | Server | SMS notifications |
| Webhooks | Server | Generic webhook integration |

## Decision Rule

If a feature involves a specific vendor's product, API, or protocol:
1. It MUST NOT be added to the core
2. It MUST be implemented as a plugin
3. It MUST use only the Plugin SDK public interfaces
4. It MUST be independently versioned and updated
