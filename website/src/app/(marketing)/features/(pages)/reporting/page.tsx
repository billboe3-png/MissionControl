import { Metadata } from 'next'
import Link from 'next/link'
import {
  FileText, Calendar, BarChart3, Download,
  Settings, Users, Clock, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Reporting',
  description:
    'Comprehensive reporting with scheduled exports, custom dashboards, compliance reports, and PDF/CSV export options.',
  canonical: '/features/reporting',
})

const capabilities = [
  {
    icon: <FileText className="w-5 h-5" />,
    title: 'Report Builder',
    description:
      'Create custom reports by selecting data sources, metrics, time ranges, and layouts — with a visual builder that requires no SQL or scripting knowledge.',
  },
  {
    icon: <Calendar className="w-5 h-5" />,
    title: 'Scheduled Delivery',
    description:
      'Schedule reports for automatic generation and delivery via email, Slack, or file share — daily, weekly, monthly, or on a custom schedule.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Compliance Reports',
    description:
      'Generate audit-ready reports covering uptime SLAs, security configurations, access reviews, and change management compliance across your infrastructure.',
  },
  {
    icon: <Download className="w-5 h-5" />,
    title: 'Export Formats',
    description:
      'Export reports in PDF, CSV, Excel, and HTML formats with configurable formatting, branding, and data granularity options for different audiences.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'Stakeholder Dashboards',
    description:
      'Create executive-level dashboards that summarize operational health, capacity trends, and incident metrics for leadership review.',
  },
  {
    icon: <Clock className="w-5 h-5" />,
    title: 'Historical Analysis',
    description:
      'Compare current metrics against historical baselines, track trends over months or years, and identify long-term patterns in infrastructure performance.',
  },
]

export default function ReportingPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Reporting' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <FileText className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Reporting</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control includes a comprehensive reporting engine that transforms
              operational data into actionable insights for technical teams, management, and
              compliance auditors. Build custom reports, schedule automatic delivery, and
              generate audit-ready documentation — all from data that Mission Control already
              collects as part of its monitoring and management operations.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Reports are not afterthoughts in Mission Control — they are deeply integrated
              with every module. A compliance report can pull data from monitoring, credential
              management, access control, and change tracking. A capacity report can combine
              infrastructure inventory, performance trends, and growth projections. This
              cross-module data access produces reports that are far richer than what
              standalone reporting tools can deliver.
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
            <h2 className="text-2xl font-bold mb-4">From Data to Decisions</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The report builder provides a visual interface for selecting data sources,
              defining time ranges, choosing visualization types, and configuring layout.
              Reports can be saved as templates and shared across the organization, ensuring
              consistency in how operational metrics are presented. Each report can include
              charts, tables, summaries, and narrative text blocks that provide context for the
              data.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Scheduled delivery ensures that stakeholders receive the information they need
              without requesting it manually. Monthly uptime reports go to management, weekly
              security posture summaries go to the CISO, and daily capacity alerts go to the
              infrastructure team — all generated and delivered automatically from a single
              platform.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Turn Operational Data into Insight</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Build, schedule, and deliver professional reports that demonstrate operational
              excellence and compliance to every stakeholder.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/dashboard" className="btn-outline">
                Explore Dashboards
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
