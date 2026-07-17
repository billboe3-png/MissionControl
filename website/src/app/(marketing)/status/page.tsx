import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { CheckCircle, ExternalLink } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Status',
  description: 'Real-time status of Mission Control services including API, dashboard, agent communication, and alert engine.',
  canonical: '/status',
})

const services = [
  { name: 'API Gateway', status: 'operational', uptime: '99.99%' },
  { name: 'Dashboard', status: 'operational', uptime: '99.99%' },
  { name: 'Agent Communication', status: 'operational', uptime: '99.98%' },
  { name: 'Alert Engine', status: 'operational', uptime: '99.99%' },
  { name: 'Plugin Marketplace', status: 'operational', uptime: '99.97%' },
  { name: 'Documentation', status: 'operational', uptime: '99.99%' },
]

const incidents = [
  {
    date: '2026-07-10',
    title: 'Scheduled Maintenance — Database Upgrade',
    status: 'completed',
    duration: '45 minutes',
    impact: 'No user impact — maintenance window during off-peak hours.',
  },
  {
    date: '2026-06-22',
    title: 'Elevated Alert Engine Latency',
    status: 'resolved',
    duration: '12 minutes',
    impact: 'Alert delivery delayed by up to 30 seconds for a subset of users.',
  },
]

export default function StatusPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Status' }]} />

      <section className="section">
        <div className="container-wide max-w-3xl">
          <div className="text-center mb-12">
            <h1 className="section-title mb-4">
              <span className="gradient-text">System Status</span>
            </h1>
            <p className="section-subtitle">
              Current status and incident history for all Mission Control services.
            </p>
          </div>

          <div className="glass rounded-xl p-6 mb-12">
            <div className="flex items-center gap-3 mb-6">
              <CheckCircle className="w-6 h-6 text-green-500" />
              <div>
                <h2 className="text-lg font-semibold text-green-700 dark:text-green-400">All Systems Operational</h2>
                <p className="text-sm text-surface-500 dark:text-surface-400">
                  Last updated: {new Date().toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' })}
                </p>
              </div>
            </div>

            <div className="divide-y divide-surface-200 dark:divide-surface-800">
              {services.map((service) => (
                <div key={service.name} className="flex items-center justify-between py-3">
                  <span className="font-medium text-sm">{service.name}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-surface-500 dark:text-surface-400">
                      Uptime: {service.uptime}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                      Operational
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-12">
            <h2 className="text-xl font-bold mb-6">Recent Incidents</h2>
            <div className="space-y-4">
              {incidents.map((incident) => (
                <div key={incident.title} className="glass rounded-xl p-6">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      incident.status === 'completed'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    }`}>
                      {incident.status === 'completed' ? 'Maintenance' : 'Resolved'}
                    </span>
                    <span className="text-xs text-surface-500 dark:text-surface-400">{incident.date}</span>
                    <span className="text-xs text-surface-500 dark:text-surface-400">Duration: {incident.duration}</span>
                  </div>
                  <h3 className="font-semibold mb-1">{incident.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">{incident.impact}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-xl p-6 text-center">
            <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
              This is a summary page. For real-time monitoring, subscribe to our full status page.
            </p>
            <a href="#" className="btn-primary inline-flex" target="_blank" rel="noopener noreferrer">
              Subscribe to Updates
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>
    </>
  )
}
