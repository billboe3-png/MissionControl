export const trustedTechnologies = [
  { name: 'Docker', icon: 'Docker' },
  { name: 'Kubernetes', icon: 'Kubernetes' },
  { name: 'Linux', icon: 'Linux' },
  { name: 'Windows', icon: 'Windows' },
  { name: 'VMware', icon: 'VMware' },
  { name: 'Proxmox', icon: 'Proxmox' },
  { name: 'Hyper-V', icon: 'HyperV' },
  { name: 'Zabbix', icon: 'Zabbix' },
  { name: 'Prometheus', icon: 'Prometheus' },
  { name: 'Grafana', icon: 'Grafana' },
  { name: 'Ansible', icon: 'Ansible' },
  { name: 'Terraform', icon: 'Terraform' },
]

export const stats = [
  { value: '99.99%', label: 'Uptime SLA' },
  { value: '50,000+', label: 'Infrastructure Nodes' },
  { value: '99+', label: 'Countries Deployed' },
  { value: '<5s', label: 'Alert Response Time' },
]

export const roadmapItems = [
  {
    quarter: 'Q3 2026',
    title: 'AI Incident Response Engine',
    description: 'Machine learning models for predictive alerting and automated root cause analysis.',
    status: 'in-progress' as const,
  },
  {
    quarter: 'Q4 2026',
    title: 'Plugin Marketplace v2',
    description: 'Community plugin store with rating, reviews, and sandboxed execution.',
    status: 'upcoming' as const,
  },
  {
    quarter: 'Q1 2027',
    title: 'Zero-Trust Architecture',
    description: 'Zero-trust networking for agent communication with mTLS and JIT access.',
    status: 'upcoming' as const,
  },
  {
    quarter: 'Q2 2027',
    title: 'Global Federation',
    description: 'Multi-region federation with active-active failover and global alert aggregation.',
    status: 'future' as const,
  },
]

export const pricingPlans = [
  {
    name: 'Community',
    price: '$0',
    description: 'For individual teams and small deployments',
    features: [
      'Up to 50 infrastructure nodes',
      'Core monitoring and alerts',
      'Dashboard and reporting',
      'Community support',
      'REST API access',
      'Single site',
    ],
    cta: 'Get Started',
    href: '/downloads',
    featured: false,
  },
  {
    name: 'Professional',
    price: '$99',
    period: '/node/month',
    description: 'For growing organizations',
    features: [
      'Up to 500 infrastructure nodes',
      'All Community features',
      'Automation and playbooks',
      'Multi-site management',
      'Credential vault',
      'Priority support',
      'Plugin framework',
    ],
    cta: 'Start Free Trial',
    href: '/contact',
    featured: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'For large-scale deployments',
    features: [
      'Unlimited infrastructure nodes',
      'All Professional features',
      'Multi-tenant with isolation',
      'AI operations engine',
      'Custom integrations',
      'Dedicated support engineer',
      'SLA guarantees',
      'On-premises deployment',
    ],
    cta: 'Contact Sales',
    href: '/contact',
    featured: false,
  },
]

export const supportedPlatforms = [
  { name: 'Ubuntu', category: 'Linux' },
  { name: 'Debian', category: 'Linux' },
  { name: 'RHEL', category: 'Linux' },
  { name: 'CentOS', category: 'Linux' },
  { name: 'Rocky Linux', category: 'Linux' },
  { name: 'SUSE Linux', category: 'Linux' },
  { name: 'Windows Server 2019', category: 'Windows' },
  { name: 'Windows Server 2022', category: 'Windows' },
  { name: 'Windows Server 2025', category: 'Windows' },
  { name: 'Windows 10/11', category: 'Windows' },
  { name: 'macOS Ventura+', category: 'macOS' },
  { name: 'Docker', category: 'Container' },
  { name: 'Kubernetes', category: 'Container' },
  { name: 'Podman', category: 'Container' },
]

export const blogPosts = [
  {
    slug: 'introducing-mission-control-3',
    title: 'Introducing Mission Control 3.0: The Enterprise IT Operations Platform',
    excerpt: 'We are proud to announce Mission Control 3.0 with AI-assisted operations, expanded plugin framework, and enterprise multi-tenancy.',
    date: '2026-07-01',
    author: 'Robert Chen',
    tags: ['Release', 'AI', 'Enterprise'],
    image: '/images/blog-release-3.jpg',
  },
  {
    slug: 'ai-incident-management',
    title: 'How AI is Transforming Incident Management in IT Operations',
    excerpt: 'Explore how machine learning and AI are revolutionizing incident detection, root cause analysis, and automated remediation.',
    date: '2026-06-15',
    author: 'Sarah Miller',
    tags: ['AI', 'Incident Management', 'Operations'],
    image: '/images/blog-ai-incidents.jpg',
  },
  {
    slug: 'multi-tenant-best-practices',
    title: 'Multi-Tenant Best Practices for MSPs',
    excerpt: 'Learn how Managed Service Providers can leverage Mission Control to efficiently manage multiple clients from a single pane of glass.',
    date: '2026-06-01',
    author: 'James Wilson',
    tags: ['MSP', 'Multi-Tenant', 'Best Practices'],
    image: '/images/blog-multitenant.jpg',
  },
  {
    slug: 'securing-remote-operations',
    title: 'Securing Remote Operations in Enterprise Environments',
    excerpt: 'A comprehensive guide to secure remote server access with session recording, RBAC, and compliance auditing.',
    date: '2026-05-20',
    author: 'Emily Park',
    tags: ['Security', 'Remote Operations', 'Compliance'],
    image: '/images/blog-security.jpg',
  },
]
