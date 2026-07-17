import { Metadata } from 'next'
import Link from 'next/link'
import {
  Server, Network, HardDrive, Cpu, MemoryStick,
  Search, RefreshCw, Database, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Infrastructure Management',
  description:
    'Comprehensive inventory and management for servers, VMs, containers, and network devices across hybrid environments.',
  canonical: '/features/infrastructure',
})

const capabilities = [
  {
    icon: <Search className="w-5 h-5" />,
    title: 'Auto-Discovery',
    description:
      'Automatically detect and classify every server, switch, router, and endpoint on your network — including shadow IT assets your team may not know about.',
  },
  {
    icon: <Network className="w-5 h-5" />,
    title: 'Network Topology',
    description:
      'Visualize the complete network topology with dependency mapping, VLAN segmentation, and hop-by-hop path analysis for troubleshooting connectivity issues.',
  },
  {
    icon: <HardDrive className="w-5 h-5" />,
    title: 'Asset Lifecycle',
    description:
      'Track hardware and software assets from procurement through decommission with warranty tracking, license compliance, and end-of-life alerts.',
  },
  {
    icon: <Cpu className="w-5 h-5" />,
    title: 'Capacity Planning',
    description:
      'Forecast resource utilization trends and receive proactive alerts before CPU, memory, or storage thresholds are breached.',
  },
  {
    icon: <Database className="w-5 h-5" />,
    title: 'Configuration Management',
    description:
      'Store and compare system configurations with drift detection, change history, and rollback capabilities for any infrastructure component.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Health Scoring',
    description:
      'Aggregate dozens of metrics into a single health score per asset, giving your team an instant overview of infrastructure status across the estate.',
  },
]

export default function InfrastructurePage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Infrastructure' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Server className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Infrastructure</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides a complete, real-time inventory of every device, server,
              and service across your hybrid infrastructure. From on-premises data centers to
              cloud deployments and remote branch offices, you gain full visibility into what
              you own, where it runs, and how it is performing.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Our auto-discovery engine continuously scans your network segments, virtualization
              platforms, and cloud APIs to maintain an accurate asset register. Every discovered
              device is automatically classified, tagged, and monitored — eliminating the
              spreadsheet-driven inventory processes that introduce errors and staleness.
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
            <h2 className="text-2xl font-bold mb-4">Unified Across Hybrid Environments</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Modern infrastructure spans physical servers, Hyper-V and Proxmox clusters,
              Docker containers, and public cloud resources. Mission Control normalizes data
              from all of these sources into a consistent model, so your team can query, filter,
              and manage assets regardless of where they run. The inventory integrates directly
              with monitoring, automation, and reporting — ensuring that every operational
              workflow starts from an accurate, up-to-date view of your estate.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Role-based access controls ensure that each team member sees only the assets
              relevant to their scope of responsibility, while executive-level views roll
              up inventory data into summary dashboards suitable for capacity planning,
              budgeting, and compliance audits.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Take Control of Your Infrastructure</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control and see every asset in your environment within minutes —
              no agents, no manual data entry, no incomplete spreadsheets.
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
