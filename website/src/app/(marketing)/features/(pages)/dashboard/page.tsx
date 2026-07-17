import { Metadata } from 'next'
import Link from 'next/link'
import {
  LayoutDashboard, Layers, BarChart3, Bell, Filter,
  Settings, Maximize2, RefreshCw, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Dashboard',
  description:
    'Unified operational workspace with customizable widgets, real-time metrics, and contextual drill-downs across your entire infrastructure.',
  canonical: '/features/dashboard',
})

const capabilities = [
  {
    icon: <Layers className="w-5 h-5" />,
    title: 'Customizable Layouts',
    description:
      'Build your ideal workspace with drag-and-drop widget placement, saved layouts per role, and responsive panels that adapt to any screen size.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Real-Time Metrics',
    description:
      'Stream live performance data from every monitored system with sub-second refresh rates, interactive charts, and historical trend overlays.',
  },
  {
    icon: <Bell className="w-5 h-5" />,
    title: 'Alert Correlation',
    description:
      'Aggregate alerts from all sources into a unified incident timeline with deduplication, severity escalation, and noise reduction.',
  },
  {
    icon: <Filter className="w-5 h-5" />,
    title: 'Advanced Filtering',
    description:
      'Slice data by environment, site, service tier, or custom tags to focus on exactly what matters to your current operational context.',
  },
  {
    icon: <Maximize2 className="w-5 h-5" />,
    title: 'Contextual Drill-Downs',
    description:
      'Click any metric or alert to instantly navigate to the underlying infrastructure, related incidents, or historical performance data.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Auto-Refresh Streams',
    description:
      'Configure per-widget refresh intervals or stream data continuously so your team always sees the latest state without manual page reloads.',
  },
]

export default function DashboardPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Dashboard' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <LayoutDashboard className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Dashboard</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control gives your operations team a single pane of glass across every
              system, service, and site you manage. The Dashboard is the nerve center of your
              IT operations — combining real-time metrics, alerts, and infrastructure status
              into one cohesive, customizable workspace.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Whether you are monitoring a single data center or coordinating operations across
              dozens of global sites, the Dashboard scales to present the right information at
              the right time. Every widget links directly to deeper diagnostic views, so your
              team can move from overview to root cause in a single click.
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
            <h2 className="text-2xl font-bold mb-4">Built for Operations Teams</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The Dashboard is designed around the workflows of NOC operators, systems
              administrators, and DevOps engineers. Each widget supports multi-select time
              ranges, allowing you to correlate events across different metrics and identify
              patterns that would be invisible in siloed monitoring tools. Custom color
              coding and threshold markers help your team spot anomalies at a glance, while
              role-based layout templates ensure every team member sees information relevant
              to their responsibilities.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Share dashboards with colleagues through persistent links or scheduled PDF
              snapshots for management. Every layout can be exported and imported across
              environments, making it simple to replicate a proven monitoring setup from
              staging to production or from one data center to another.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">See Your Infrastructure Clearly</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Stop switching between dozens of tools. Mission Control brings everything into
              one dashboard so your team can respond faster and work smarter.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Deploy Mission Control
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/monitoring" className="btn-outline">
                Explore Monitoring
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
