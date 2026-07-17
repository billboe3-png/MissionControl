import { Metadata } from 'next'
import Link from 'next/link'
import {
  Globe, Wifi, HardDrive, Map,
  Shield, RefreshCw, BarChart3, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Multi-Site Management',
  description:
    'Centralized management for geographically distributed sites with WAN-aware operations, local caching, and offline resilience.',
  canonical: '/features/multi-site',
})

const capabilities = [
  {
    icon: <Globe className="w-5 h-5" />,
    title: 'Site Hierarchy',
    description:
      'Organize infrastructure into sites, regions, and zones with role-based access that maps to your organizational structure and geographic distribution.',
  },
  {
    icon: <Wifi className="w-5 h-5" />,
    title: 'WAN-Aware Operations',
    description:
      'Operations adapt automatically to available bandwidth — prioritizing critical data during WAN degradation and deferring bulk transfers when links are congested.',
  },
  {
    icon: <HardDrive className="w-5 h-5" />,
    title: 'Local Data Caching',
    description:
      'Site-local caches store monitoring data, credentials, and configuration locally so operations continue even when the central server is unreachable.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Offline Resilience',
    description:
      'Agents and site gateways continue operating autonomously during network outages, buffering data locally and synchronizing when connectivity is restored.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Site-Level Access Control',
    description:
      'Restrict operators to site-specific resources with RBAC policies that map to physical locations, ensuring staff can only access systems they are authorized to manage.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Cross-Site Reporting',
    description:
      'Generate reports that span all sites or drill into individual locations, with comparisons of uptime, performance, and operational metrics across your global estate.',
  },
]

export default function MultiSitePage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Multi-Site' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Globe className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Multi-Site</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control is designed to manage infrastructure across geographically
              distributed sites — from branch offices and retail locations to regional data
              centers and cloud regions. The multi-site architecture ensures that operations
              remain effective regardless of WAN quality, site connectivity, or geographic
              separation.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Each site operates semi-autonomously with local data caching and agent execution,
              while the central Mission Control instance provides unified visibility, cross-site
              correlation, and centralized policy management. This architecture means your
              operations team can manage globally while acting locally — responding to site-specific
              issues with the context and tools they need.
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
            <h2 className="text-2xl font-bold mb-4">Operate Globally, Act Locally</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Traditional monitoring platforms struggle when sites have limited or unreliable
              WAN connectivity. Mission Control&apos;s site gateway architecture solves this by
              maintaining local caches of critical data and executing operations locally at each
              site. During WAN outages, the site gateway continues collecting metrics, executing
              playbooks, and managing local infrastructure — synchronizing all data with the
              central server when connectivity is restored.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The cross-site correlation engine identifies patterns that span locations — such
              as a cloud provider outage affecting multiple regions, or a software deployment
              causing issues across branch offices — giving your team a global perspective that
              site-level monitoring alone cannot provide.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Manage Infrastructure Everywhere</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control across your distributed infrastructure with site-aware
              operations, offline resilience, and centralized management.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/multi-tenant" className="btn-outline">
                Multi-Tenant
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
