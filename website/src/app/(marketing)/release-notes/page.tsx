import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Tag, Calendar, CheckCircle, AlertCircle, Wrench } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Release Notes',
  description: 'Detailed release notes for every Mission Control version. View new features, improvements, bug fixes, and breaking changes.',
  canonical: '/release-notes',
})

const releases = [
  {
    version: '3.0.0',
    date: '2026-07-01',
    type: 'major',
    title: 'Mission Control 3.0',
    summary: 'AI-assisted operations, plugin marketplace v2, enterprise multi-tenancy, and redesigned dashboard.',
    breaking: [
      'Legacy API v1 endpoints removed — migrate to v2',
      'Agent minimum version raised to 2.8.0',
    ],
    features: [
      'AI Incident Response Engine with predictive alerting',
      'Plugin Marketplace v2 with sandboxed execution',
      'Enterprise multi-tenancy with tenant isolation',
      'Redesigned dashboard with customizable widgets',
      'Webhook support for all alert channels',
    ],
    fixes: [
      'Resolved memory leak in long-running agent connections',
      'Fixed dashboard rendering issue on Safari 17',
      'Corrected timezone handling in scheduled playbooks',
    ],
  },
  {
    version: '2.9.0',
    date: '2026-06-01',
    type: 'minor',
    title: 'Multi-Site Enhancements',
    summary: 'Cross-site alert correlation, geographic map view, and agent health dashboard.',
    features: [
      'Cross-site alert correlation and deduplication',
      'Geographic map view for multi-site deployments',
      'Agent health dashboard with version tracking',
      'Bulk agent upgrade capability',
    ],
    fixes: [
      'Fixed credential vault sync delay between replicas',
      'Resolved log forwarding reconnection on network flap',
    ],
  },
  {
    version: '2.8.0',
    date: '2026-04-15',
    type: 'minor',
    title: 'Playbook Engine v2',
    summary: 'Visual playbook editor, conditional branching, and 50+ new built-in actions.',
    features: [
      'Visual playbook editor with drag-and-drop',
      'Conditional branching and error handling in playbooks',
      '50+ new built-in actions for common operations',
      'Playbook execution history and rollback',
    ],
    fixes: [
      'Fixed notification deduplication in high-volume scenarios',
      'Resolved API rate limiter counter drift',
    ],
  },
  {
    version: '2.7.0',
    date: '2026-02-20',
    type: 'minor',
    title: 'Security Hardening',
    summary: 'mTLS agent communication, session recording, and SOC 2 compliance framework.',
    features: [
      'mTLS for all agent-server communication',
      'Terminal session recording and playback',
      'SOC 2 compliance framework with audit reports',
      'Credential rotation scheduling',
    ],
    fixes: [
      'Fixed RBAC policy evaluation for nested groups',
      'Resolved memory usage in Prometheus scrape endpoint',
    ],
  },
  {
    version: '2.6.0',
    date: '2025-12-10',
    type: 'minor',
    title: 'Proxmox & Hyper-V',
    summary: 'Full Proxmox VE and Hyper-V management with live migration visibility.',
    features: [
      'Proxmox VE integration with VM lifecycle management',
      'Hyper-V management with live migration tracking',
      'Virtual machine resource trending and forecasting',
      'Hypervisor cluster health dashboard',
    ],
    fixes: [
      'Fixed Windows agent WMI query timeout on large domains',
      'Resolved Docker container stats collection interval',
    ],
  },
]

const typeConfig: Record<string, { label: string; color: string }> = {
  major: { label: 'Major', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
  minor: { label: 'Minor', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  patch: { label: 'Patch', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400' },
}

export default function ReleaseNotesPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Release Notes' }]} />

      <section className="section">
        <div className="container-wide max-w-4xl">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Release Notes</span>
            </h1>
            <p className="section-subtitle">
              A complete history of Mission Control releases, features, improvements, and fixes.
            </p>
          </div>

          <div className="space-y-8">
            {releases.map((release) => {
              const config = typeConfig[release.type]
              return (
                <div key={release.version} className="glass rounded-xl p-8">
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    <h2 className="text-2xl font-bold">v{release.version}</h2>
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${config.color}`}>
                      {config.label}
                    </span>
                    <span className="text-sm text-surface-500 dark:text-surface-400 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(release.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{release.title}</h3>
                  <p className="text-surface-500 dark:text-surface-400 mb-6">{release.summary}</p>

                  <div className="space-y-6">
                    {release.features.length > 0 && (
                      <div>
                        <h4 className="flex items-center gap-2 font-semibold text-sm mb-3">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          New Features
                        </h4>
                        <ul className="space-y-1.5">
                          {release.features.map((f) => (
                            <li key={f} className="text-sm text-surface-600 dark:text-surface-300 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 flex-shrink-0" />
                              {f}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {release.fixes.length > 0 && (
                      <div>
                        <h4 className="flex items-center gap-2 font-semibold text-sm mb-3">
                          <Wrench className="w-4 h-4 text-blue-500" />
                          Bug Fixes
                        </h4>
                        <ul className="space-y-1.5">
                          {release.fixes.map((f) => (
                            <li key={f} className="text-sm text-surface-600 dark:text-surface-300 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                              {f}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {release.breaking && release.breaking.length > 0 && (
                      <div>
                        <h4 className="flex items-center gap-2 font-semibold text-sm mb-3">
                          <AlertCircle className="w-4 h-4 text-amber-500" />
                          Breaking Changes
                        </h4>
                        <ul className="space-y-1.5">
                          {release.breaking.map((b) => (
                            <li key={b} className="text-sm text-surface-600 dark:text-surface-300 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 flex-shrink-0" />
                              {b}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>
    </>
  )
}
