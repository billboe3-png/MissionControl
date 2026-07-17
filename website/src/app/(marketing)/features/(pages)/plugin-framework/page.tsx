import { Metadata } from 'next'
import Link from 'next/link'
import {
  Puzzle, Code, GitBranch, Shield,
  BarChart3, Download, Settings, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Plugin Framework',
  description:
    'Extensible plugin architecture with SDK, marketplace, and community-contributed integrations for custom workflows.',
  canonical: '/features/plugin-framework',
})

const capabilities = [
  {
    icon: <Puzzle className="w-5 h-5" />,
    title: 'Modular Architecture',
    description:
      'Every feature in Mission Control is delivered as a plugin, ensuring clean separation of concerns and the ability to enable, disable, or replace capabilities independently.',
  },
  {
    icon: <Code className="w-5 h-5" />,
    title: 'Developer SDK',
    description:
      'Build custom plugins using the TypeScript SDK with comprehensive documentation, type definitions, and development tools for rapid plugin authoring.',
  },
  {
    icon: <Download className="w-5 h-5" />,
    title: 'Plugin Marketplace',
    description:
      'Browse and install community-contributed and officially maintained plugins from the marketplace, with ratings, reviews, and compatibility information.',
  },
  {
    icon: <GitBranch className="w-5 h-5" />,
    title: 'Version Management',
    description:
      'Install, update, and rollback plugins independently with version pinning, dependency resolution, and compatibility checking across your plugin stack.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Security Sandboxing',
    description:
      'Third-party plugins run in isolated sandboxes with explicit permission declarations, ensuring they can only access the APIs and data they are authorized for.',
  },
  {
    icon: <Settings className="w-5 h-5" />,
    title: 'Configuration UI',
    description:
      'Each plugin provides its own configuration interface that integrates seamlessly with the Mission Control admin console — no manual config file editing required.',
  },
]

export default function PluginFrameworkPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Plugin Framework' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Puzzle className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Plugin</span> Framework
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control is built on a plugin architecture that ensures the platform
              remains extensible, maintainable, and adaptable to your specific needs. Every
              feature — from monitoring and automation to infrastructure management — is
              delivered as a plugin that can be independently updated, replaced, or extended.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The plugin framework empowers your team to build custom integrations using the
              TypeScript SDK, install community-contributed plugins from the marketplace, or
              modify the behavior of existing features. Plugins run in security sandboxes with
              explicit permission boundaries, ensuring that third-party code cannot access
              unauthorized data or APIs.
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
            <h2 className="text-2xl font-bold mb-4">Extend Without Limits</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The plugin SDK provides a comprehensive API for building new integrations,
              custom dashboards, automation actions, and reporting modules. Plugins can register
              new data sources, define custom UI components, expose REST API endpoints, and
              hook into the event system to respond to monitoring alerts, infrastructure
              changes, and user actions.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The marketplace hosts plugins from both the Mission Control team and the
              community, with automated compatibility testing, security scanning, and code
              review before publication. Each plugin declares its permissions, dependencies,
              and configuration requirements — and Mission Control enforces these declarations
              at runtime, providing defense-in-depth against malicious or buggy third-party
              code.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Build the Platform You Need</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Use the plugin SDK to extend Mission Control with custom integrations, or browse
              the marketplace for community-contributed plugins.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/documentation" className="btn-primary">
                Plugin SDK Docs
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/rest-api" className="btn-outline">
                REST API
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
