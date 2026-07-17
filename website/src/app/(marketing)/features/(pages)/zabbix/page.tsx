import { Metadata } from 'next'
import Link from 'next/link'
import {
  Gauge, Link2, Bell, BarChart3,
  Shield, RefreshCw, Layers, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Zabbix Integration',
  description:
    'Native Zabbix integration for metrics, events, and topology with unified alert management and automated remediation.',
  canonical: '/features/zabbix',
})

const capabilities = [
  {
    icon: <Link2 className="w-5 h-5" />,
    title: 'Native API Integration',
    description:
      'Connect directly to Zabbix via its API to pull hosts, metrics, triggers, and topology data — no proprietary agents or intermediate services required.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Unified Metric Views',
    description:
      'Combine Zabbix metrics with data from other monitoring sources in a single dashboard, giving your team a consolidated view without switching tools.',
  },
  {
    icon: <Bell className="w-5 h-5" />,
    title: 'Alert Deduplication',
    description:
      'Mission Control deduplicates and correlates Zabbix alerts with other sources, reducing alert fatigue and ensuring only actionable incidents reach your team.',
  },
  {
    icon: <Layers className="w-5 h-5" />,
    title: 'Topology Mapping',
    description:
      'Import Zabbix host groups, templates, and dependency relationships to automatically build service maps and visualize infrastructure dependencies.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Credential Management',
    description:
      'Store Zabbix API credentials securely in the credential vault with automatic rotation and access auditing — never expose credentials in configuration files.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Bidirectional Sync',
    description:
      'Keep Zabbix and Mission Control in sync with periodic data reconciliation, ensuring your operational views always reflect the latest discovered state.',
  },
]

export default function ZabbixPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Zabbix' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Gauge className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Zabbix</span> Integration
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Many organizations have invested heavily in Zabbix monitoring infrastructure.
              Mission Control complements your existing Zabbix deployment by providing a unified
              operational layer on top of Zabbix data — combining it with infrastructure
              management, automation, and AI-assisted analysis in a single platform.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The integration connects directly to the Zabbix API, pulling hosts, metrics,
              triggers, events, and topology data in real time. Your Zabbix templates and
              host groups are imported as operational context, enabling Mission Control to
              correlate Zabbix alerts with configuration changes, capacity trends, and
              automated response playbooks.
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
            <h2 className="text-2xl font-bold mb-4">Preserve Your Zabbix Investment</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Migrating away from Zabbix is not always practical or desirable. Mission Control
              lets you keep your Zabbix infrastructure running while adding the operational
              capabilities your team needs — automated incident response, cross-system
              correlation, credential management, and AI-assisted analysis — all without
              replacing your existing monitoring stack.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The integration supports Zabbix 5.x and 6.x, with full compatibility for
              triggers, maintenance windows, proxies, and distributed monitoring topologies.
              Configuration is minimal — provide your Zabbix server URL and API credentials,
              and Mission Control handles the rest, including automatic discovery and ongoing
              data synchronization.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Enhance Your Zabbix Deployment</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Connect Mission Control to your existing Zabbix server and unlock unified alerting,
              automated response, and AI-assisted operations — all in minutes.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
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
