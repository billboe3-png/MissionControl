export interface Feature {
  title: string
  description: string
  icon: string
  href: string
}

export const features: Feature[] = [
  {
    title: 'Dashboard',
    description: 'Unified operational workspace with customizable widgets, real-time metrics, and contextual drill-downs across your entire infrastructure.',
    icon: 'LayoutDashboard',
    href: '/features/dashboard',
  },
  {
    title: 'Infrastructure',
    description: 'Comprehensive inventory and management for servers, VMs, containers, and network devices across hybrid environments.',
    icon: 'Server',
    href: '/features/infrastructure',
  },
  {
    title: 'Monitoring',
    description: 'Real-time monitoring with intelligent alerting, anomaly detection, and automated incident response across all systems.',
    icon: 'Activity',
    href: '/features/monitoring',
  },
  {
    title: 'Zabbix',
    description: 'Native Zabbix integration for metrics, events, and topology with unified alert management and automated remediation.',
    icon: 'Gauge',
    href: '/features/zabbix',
  },
  {
    title: 'Hyper-V',
    description: 'Full lifecycle management for Hyper-V hosts and VMs including provisioning, migration, replication, and backup orchestration.',
    icon: 'Monitor',
    href: '/features/hyper-v',
  },
  {
    title: 'Proxmox',
    description: 'Manage Proxmox clusters with unified VM/CT operations, storage management, HA configuration, and live migration support.',
    icon: 'Container',
    href: '/features/proxmox',
  },
  {
    title: 'Docker',
    description: 'Container lifecycle management with image registries, compose deployments, swarm clusters, and real-time container monitoring.',
    icon: 'Box',
    href: '/features/docker',
  },
  {
    title: 'Active Directory',
    description: 'AD management and monitoring including user/group administration, replication monitoring, GPO management, and health tracking.',
    icon: 'Users',
    href: '/features/active-directory',
  },
  {
    title: 'Microsoft 365',
    description: 'Monitor and manage Microsoft 365 tenants with service health, license tracking, security alerts, and compliance reporting.',
    icon: 'Cloud',
    href: '/features/office-365',
  },
  {
    title: 'Remote Operations',
    description: 'Secure remote desktop, SSH, and PowerShell access with session recording, RBAC, and audit logging for compliance.',
    icon: 'MonitorSmartphone',
    href: '/features/remote-operations',
  },
  {
    title: 'Automation',
    description: 'Event-driven automation engine with visual workflow builder, scheduling, and cross-system orchestration.',
    icon: 'Zap',
    href: '/features/automation',
  },
  {
    title: 'Playbooks',
    description: 'Pre-built and custom playbooks for incident response, maintenance tasks, and operational procedures with version control.',
    icon: 'BookOpen',
    href: '/features/playbooks',
  },
  {
    title: 'Mission Control Agent',
    description: 'Lightweight agent for secure connectivity, local execution, and data collection across firewalled and air-gapped environments.',
    icon: 'Radio',
    href: '/features/mc-agent',
  },
  {
    title: 'AI Operations',
    description: 'AI-assisted incident analysis, root cause recommendation, anomaly prediction, and automated remediation suggestions.',
    icon: 'Brain',
    href: '/features/ai-operations',
  },
  {
    title: 'Plugin Framework',
    description: 'Extensible plugin architecture with SDK, marketplace, and community-contributed integrations for custom workflows.',
    icon: 'Puzzle',
    href: '/features/plugin-framework',
  },
  {
    title: 'Multi-Tenant',
    description: 'Enterprise multi-tenancy with isolated workspaces, custom branding, role-based access, and tenant-specific policies.',
    icon: 'Building2',
    href: '/features/multi-tenant',
  },
  {
    title: 'Multi-Site',
    description: 'Centralized management for geographically distributed sites with WAN-aware operations, local caching, and offline resilience.',
    icon: 'Globe',
    href: '/features/multi-site',
  },
  {
    title: 'Reporting',
    description: 'Comprehensive reporting with scheduled exports, custom dashboards, compliance reports, and PDF/CSV export options.',
    icon: 'FileText',
    href: '/features/reporting',
  },
  {
    title: 'Credential Vault',
    description: 'Enterprise-grade credential management with encryption, rotation policies, access auditing, and secrets injection.',
    icon: 'Shield',
    href: '/features/credential-vault',
  },
  {
    title: 'REST API',
    description: 'Comprehensive REST API with OpenAPI specification, rate limiting, webhooks, and SDK support for custom integrations.',
    icon: 'Code',
    href: '/features/rest-api',
  },
]
