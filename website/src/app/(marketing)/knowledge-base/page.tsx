import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Search, BookOpen, Lightbulb, Server, Shield, Zap, Settings, ArrowRight } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Knowledge Base',
  description: 'Searchable knowledge base with answers to common questions, troubleshooting guides, and best practices for Mission Control.',
  canonical: '/knowledge-base',
})

const categories = [
  {
    icon: Zap,
    title: 'Getting Started',
    count: 24,
    articles: [
      'How to install Mission Control with Docker Compose',
      'Configuring your first agent',
      'Setting up alert notifications',
      'Understanding the dashboard',
    ],
  },
  {
    icon: Server,
    title: 'Infrastructure Monitoring',
    count: 42,
    articles: [
      'Linux agent troubleshooting guide',
      'Windows WMI collection configuration',
      'Docker container metrics reference',
      'Custom metric definitions',
    ],
  },
  {
    icon: Shield,
    title: 'Security & Authentication',
    count: 18,
    articles: [
      'Configuring SSO with SAML 2.0',
      'Setting up the credential vault',
      'Role-based access control reference',
      'Enabling session recording',
    ],
  },
  {
    icon: Settings,
    title: 'Automation & Playbooks',
    count: 31,
    articles: [
      'Creating your first playbook',
      'Built-in actions reference',
      'Scheduling recurring tasks',
      'Error handling in playbooks',
    ],
  },
  {
    icon: Lightbulb,
    title: 'AI Operations',
    count: 15,
    articles: [
      'Configuring predictive alerting',
      'Root cause analysis walkthrough',
      'Training custom anomaly detectors',
      'AI engine performance tuning',
    ],
  },
  {
    icon: BookOpen,
    title: 'API & Integrations',
    count: 27,
    articles: [
      'REST API authentication guide',
      'Webhook configuration',
      'Prometheus exporter setup',
      'Grafana data source plugin',
    ],
  },
]

export default function KnowledgeBasePage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Knowledge Base' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Knowledge Base</span>
            </h1>
            <p className="section-subtitle">
              Find answers to common questions, step-by-step guides, and troubleshooting articles.
            </p>
          </div>

          <div className="max-w-2xl mx-auto mb-16">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="text"
                placeholder="Search the knowledge base..."
                className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-lg"
                readOnly
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category) => (
              <div key={category.title} className="glass rounded-xl p-6 card-hover">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center">
                    <category.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{category.title}</h3>
                    <span className="text-xs text-surface-500 dark:text-surface-400">{category.count} articles</span>
                  </div>
                </div>
                <ul className="space-y-2">
                  {category.articles.map((article) => (
                    <li key={article}>
                      <Link
                        href="/knowledge-base"
                        className="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-300 hover:text-mc-600 dark:hover:text-mc-400 transition-colors"
                      >
                        <ArrowRight className="w-3 h-3 flex-shrink-0" />
                        {article}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
