import { Metadata } from 'next'
import Link from 'next/link'
import {
  Users, Shield, RefreshCw, FileText,
  Activity, Settings, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Active Directory Management',
  description:
    'AD management and monitoring including user/group administration, replication monitoring, GPO management, and health tracking.',
  canonical: '/features/active-directory',
})

const capabilities = [
  {
    icon: <Users className="w-5 h-5" />,
    title: 'User & Group Management',
    description:
      'Create, modify, disable, and delete user accounts and groups with approval workflows, bulk operations, and automated provisioning from HR systems.',
  },
  {
    icon: <Activity className="w-5 h-5" />,
    title: 'Replication Monitoring',
    description:
      'Track replication status between domain controllers in real time with latency metrics, failure alerts, and topology visualization across sites.',
  },
  {
    icon: <FileText className="w-5 h-5" />,
    title: 'GPO Management',
    description:
      'View, compare, and audit Group Policy Objects with version tracking, conflict detection, and impact analysis before deploying changes to production.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Security Hardening',
    description:
      'Monitor Kerberos ticket anomalies, LDAP signing requirements, privileged group membership changes, and enforce security baselines automatically.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Health Dashboard',
    description:
      'Real-time health overview of all domain controllers, DNS services, DHCP scopes, and site links with automatic failover detection and alerting.',
  },
  {
    icon: <AlertTriangle className="w-5 h-5" />,
    title: 'Change Detection',
    description:
      'Detect and alert on unauthorized changes to AD objects, schema modifications, FSMO role transfers, and trust relationship changes with full audit trails.',
  },
]

export default function ActiveDirectoryPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Active Directory' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Users className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Active Directory</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Active Directory is the backbone of identity and access management in most Windows
              environments, yet it remains one of the most complex and risk-prone components to
              manage. Mission Control provides a purpose-built management layer for AD that goes
              far beyond what native tools like Active Directory Users and Computers (ADUC)
              provide.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Monitor replication health across domain controllers, track Group Policy
              deployments, detect security anomalies, and manage user lifecycle — all from a
              unified interface. Mission Control integrates AD monitoring with your broader
              infrastructure alerts, so a replication failure is correlated with network
              connectivity, DNS health, and domain controller resource utilization.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {capabilities.map((cap) => (
              <div key={cap.title} className="glass rounded-xl p-6 card-hover">
                <div className="p-2.5 rounded-lg bg-mc-500/10 text-mc-600 dark:text-mc-400 w-fit mb-4">
                  {cap.icon}
                </div>
                <h3 className="font-semibold mb-2">{cap.title}</h3>
                <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
                  {cap.description}
                </p>
              </div>
            ))}
          </div>

          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-4">AD Operations Without the Risk</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control introduces approval workflows for sensitive AD operations like
              privileged group modifications, schema changes, and trust relationship management.
              Every change is logged with before-and-after snapshots, providing a complete audit
              trail for compliance and forensic analysis. Automated alerts detect suspicious
              patterns such as off-hours account lockouts, mass group membership changes, or
              replication interruptions that could indicate a security incident.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The platform supports multi-forest and multi-domain environments, aggregating
              health and operational data from all AD deployments into a single pane of glass.
              Stale computer accounts, unused service accounts, and expiring passwords are
              flagged automatically, helping your team maintain a clean, secure directory
              without manual audits.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Simplify Active Directory Operations</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control and gain visibility, control, and automation for your
              Active Directory environment — with full audit logging and approval workflows.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/office-365" className="btn-outline">
                Microsoft 365
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
