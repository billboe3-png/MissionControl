import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Code, Key, Server, Webhook, Shield, BookOpen, ArrowRight } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'API Reference',
  description: 'Complete REST API reference for Mission Control. Integrate monitoring, alerting, and infrastructure management into your existing workflows and tools.',
  canonical: '/api-reference',
})

const endpoints = [
  { method: 'GET', path: '/api/v2/nodes', description: 'List all monitored infrastructure nodes' },
  { method: 'GET', path: '/api/v2/nodes/:id', description: 'Get details for a specific node' },
  { method: 'POST', path: '/api/v2/alerts', description: 'Create or manage alert rules' },
  { method: 'GET', path: '/api/v2/alerts', description: 'List all active and historical alerts' },
  { method: 'GET', path: '/api/v2/metrics/:nodeId', description: 'Retrieve metric data for a node' },
  { method: 'POST', path: '/api/v2/playbooks/:id/execute', description: 'Trigger a playbook execution' },
  { method: 'GET', path: '/api/v2/tenants', description: 'List tenants (Enterprise only)' },
  { method: 'GET', path: '/api/v2/health', description: 'System health check endpoint' },
]

const methodColors: Record<string, string> = {
  GET: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  POST: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  PUT: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  DELETE: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

const features = [
  {
    icon: Key,
    title: 'Authentication',
    description: 'Token-based authentication with API keys, OAuth 2.0, and service account support.',
  },
  {
    icon: Shield,
    title: 'Rate Limiting',
    description: 'Configurable rate limits per endpoint with burst support and graceful degradation.',
  },
  {
    icon: Webhook,
    title: 'Webhooks',
    description: 'Real-time event notifications for alerts, status changes, and custom triggers.',
  },
  {
    icon: Code,
    title: 'SDKs',
    description: 'Official client libraries for Python, Go, TypeScript, and Java.',
  },
]

export default function ApiReferencePage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'API Reference' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">REST API Reference</span>
            </h1>
            <p className="section-subtitle">
              Integrate Mission Control with your existing tools and workflows. Full programmatic access to monitoring, alerting, automation, and administration.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6 mb-16">
            {features.map((feature) => (
              <div key={feature.title} className="glass rounded-xl p-6 card-hover text-center">
                <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mx-auto mb-3">
                  <feature.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="font-semibold text-sm mb-2">{feature.title}</h3>
                <p className="text-xs text-surface-500 dark:text-surface-400">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="max-w-3xl mx-auto mb-16">
            <h2 className="text-2xl font-bold mb-6">Endpoint Reference</h2>
            <div className="glass rounded-xl overflow-hidden">
              <div className="p-4 border-b border-surface-200 dark:border-surface-800">
                <code className="text-sm font-mono text-surface-600 dark:text-surface-300">
                  Base URL: https://your-instance.missioncontrol.io/api/v2
                </code>
              </div>
              <div className="divide-y divide-surface-200 dark:divide-surface-800">
                {endpoints.map((endpoint) => (
                  <div key={endpoint.path + endpoint.method} className="px-4 py-3 flex items-center gap-3 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold font-mono ${methodColors[endpoint.method]}`}>
                      {endpoint.method}
                    </span>
                    <code className="text-sm font-mono text-surface-900 dark:text-surface-100">
                      {endpoint.path}
                    </code>
                    <span className="text-sm text-surface-500 dark:text-surface-400 hidden sm:inline ml-auto">
                      {endpoint.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-sm text-surface-500 dark:text-surface-400 mt-4 text-center">
              Full OpenAPI specification available at <code className="text-mc-600 dark:text-mc-400">/api/v2/openapi.json</code>
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-3">Quick Start</h3>
              <p className="text-surface-500 dark:text-surface-400 text-sm mb-4">
                Get up and running with the Mission Control API in under 5 minutes.
              </p>
              <code className="block p-4 rounded-lg bg-surface-900 dark:bg-surface-950 text-green-400 text-sm font-mono mb-4 overflow-x-auto">
{`curl -H "Authorization: Bearer mc_api_key" \\
  https://your-instance.missioncontrol.io/api/v2/nodes`}
              </code>
              <Link href="/documentation" className="text-sm text-mc-600 dark:text-mc-400 hover:underline flex items-center gap-1">
                View full getting started guide <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-3">SDKs & Libraries</h3>
              <p className="text-surface-500 dark:text-surface-400 text-sm mb-4">
                Official client libraries for popular programming languages.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {['Python', 'Go', 'TypeScript', 'Java'].map((lang) => (
                  <div key={lang} className="flex items-center gap-2 p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                    <Code className="w-4 h-4 text-mc-600 dark:text-mc-400" />
                    <span className="text-sm font-medium">{lang}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
