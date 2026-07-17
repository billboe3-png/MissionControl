import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { BookOpen, Search, Server, Shield, Cpu, Zap, Settings, Terminal, FileText } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Documentation',
  description: 'Comprehensive documentation for Mission Control including installation guides, configuration references, API documentation, and best practices for enterprise IT operations.',
  canonical: '/documentation',
})

const docCategories = [
  {
    icon: Zap,
    title: 'Getting Started',
    description: 'Quick start guides, installation, and initial configuration for Mission Control.',
    articles: [
      'Quick Start Guide',
      'System Requirements',
      'Installation Overview',
      'First Steps Dashboard',
      'Adding Your First Server',
    ],
  },
  {
    icon: Server,
    title: 'Infrastructure Management',
    description: 'Manage servers, virtual machines, containers, and cloud resources from a unified interface.',
    articles: [
      'Linux Agent Setup',
      'Windows Agent Setup',
      'Docker Integration',
      'Kubernetes Monitoring',
      'Hyper-V Management',
      'Proxmox Integration',
      'Cloud Provider Setup',
    ],
  },
  {
    icon: Shield,
    title: 'Security & Access Control',
    description: 'Configure authentication, authorization, credential vault, and compliance auditing.',
    articles: [
      'Role-Based Access Control',
      'Multi-Factor Authentication',
      'Credential Vault Setup',
      'SSO Integration',
      'Audit Logging',
      'Session Recording',
    ],
  },
  {
    icon: Cpu,
    title: 'AI Operations',
    description: 'Leverage AI-assisted alerting, root cause analysis, and automated remediation.',
    articles: [
      'AI Incident Response Engine',
      'Predictive Alerting',
      'Root Cause Analysis',
      'Automated Remediation',
      'Custom ML Models',
    ],
  },
  {
    icon: Settings,
    title: 'Automation & Playbooks',
    description: 'Create and manage automation playbooks, scheduled tasks, and workflow orchestration.',
    articles: [
      'Playbook Editor',
      'Built-in Actions',
      'Scheduled Tasks',
      'Workflow Templates',
      'Custom Plugins',
    ],
  },
  {
    icon: Terminal,
    title: 'REST API',
    description: 'Complete API reference for integrating Mission Control with your existing tools and workflows.',
    articles: [
      'Authentication',
      'Endpoints Reference',
      'Webhooks',
      'Rate Limiting',
      'SDKs & Libraries',
    ],
  },
]

export default function DocumentationPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Documentation' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Documentation</span>
            </h1>
            <p className="section-subtitle">
              Everything you need to deploy, configure, and operate Mission Control across your entire infrastructure.
            </p>
          </div>

          <div className="max-w-2xl mx-auto mb-16">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="text"
                placeholder="Search documentation..."
                className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-lg"
                readOnly
              />
              <kbd className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-1 rounded bg-surface-100 dark:bg-surface-800 text-surface-500 text-xs font-mono">
                ⌘K
              </kbd>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {docCategories.map((category) => (
              <div
                key={category.title}
                className="glass rounded-xl p-6 card-hover"
              >
                <div className="w-12 h-12 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mb-4">
                  <category.icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{category.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 text-sm mb-4">
                  {category.description}
                </p>
                <ul className="space-y-2">
                  {category.articles.map((article) => (
                    <li key={article}>
                      <Link
                        href="/documentation"
                        className="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-300 hover:text-mc-600 dark:hover:text-mc-400 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                        {article}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-16 glass rounded-xl p-8 text-center">
            <h3 className="text-xl font-semibold mb-3">Can&apos;t find what you&apos;re looking for?</h3>
            <p className="text-surface-500 dark:text-surface-400 mb-6">
              Our support team and community are here to help.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/support" className="btn-primary">
                Contact Support
              </Link>
              <Link href="/community" className="btn-secondary">
                Community Forum
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
