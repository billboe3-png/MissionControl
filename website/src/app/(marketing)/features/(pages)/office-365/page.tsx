import { Metadata } from 'next'
import Link from 'next/link'
import {
  Cloud, Shield, BarChart3, Users,
  Activity, AlertTriangle, FileText, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Microsoft 365 Monitoring',
  description:
    'Monitor and manage Microsoft 365 tenants with service health, license tracking, security alerts, and compliance reporting.',
  canonical: '/features/office-365',
})

const capabilities = [
  {
    icon: <Activity className="w-5 h-5" />,
    title: 'Service Health Monitoring',
    description:
      'Track the health of Exchange Online, SharePoint, Teams, OneDrive, and Azure AD with proactive alerts when Microsoft reports incidents or degraded performance.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'License Management',
    description:
      'Monitor license consumption, identify unused allocations, track upcoming renewals, and forecast licensing costs across all your Microsoft 365 subscriptions.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Security Posture',
    description:
      'Aggregate Microsoft Secure Score recommendations, track conditional access policy compliance, and surface risky sign-in events that require attention.',
  },
  {
    icon: <AlertTriangle className="w-5 h-5" />,
    title: 'Alert Management',
    description:
      'Correlate Microsoft 365 service alerts with your on-premises infrastructure events — so a mail flow issue can be traced back to DNS, network, or identity problems.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Adoption Analytics',
    description:
      'Track user adoption across Teams, SharePoint, and Exchange with usage trends, inactive mailbox detection, and storage consumption forecasting.',
  },
  {
    icon: <FileText className="w-5 h-5" />,
    title: 'Compliance Reporting',
    description:
      'Generate compliance reports covering retention policies, data loss prevention alerts, audit log status, and regulatory requirements for your Microsoft 365 tenant.',
  },
]

export default function Office365Page() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Microsoft 365' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Cloud className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Microsoft 365</span> Monitoring
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Microsoft 365 is critical infrastructure for most organizations, yet many IT teams
              rely on the Microsoft 365 admin center alone for visibility. Mission Control
              connects to your Microsoft 365 tenant via the Graph API to provide comprehensive
              monitoring, analytics, and management capabilities that complement the native
              admin experience.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Correlate Microsoft 365 service health with your on-premises infrastructure to
              quickly identify whether issues are caused by Microsoft service outages or local
              network, DNS, or identity problems. Track license utilization, security posture,
              and adoption metrics alongside your other infrastructure KPIs in a unified
              operational dashboard.
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
            <h2 className="text-2xl font-bold mb-4">Beyond the Microsoft Admin Center</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              While the Microsoft 365 admin center provides basic monitoring, it lacks the
              ability to correlate cloud service health with on-premises infrastructure events.
              Mission Control bridges that gap, providing a unified view where a mail delivery
              failure can be immediately traced to its root cause — whether that is an Exchange
              Online service issue, a local DNS misconfiguration, a firewall rule change, or an
              Active Directory authentication problem.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Scheduled reports can be automatically generated and distributed to stakeholders,
              covering everything from monthly security posture reviews to quarterly license
              utilization summaries. Integration with the automation engine enables automatic
              responses to common issues, such as provisioning new users, applying security
              policies, or escalating service degradation to the appropriate support team.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Gain Microsoft 365 Visibility</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Connect your Microsoft 365 tenant to Mission Control for unified monitoring
              alongside your on-premises infrastructure, security analytics, and compliance
              reporting.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/active-directory" className="btn-outline">
                Active Directory
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
