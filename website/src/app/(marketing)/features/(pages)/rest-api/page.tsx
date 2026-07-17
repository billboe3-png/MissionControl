import { Metadata } from 'next'
import Link from 'next/link'
import {
  Code, FileText, Shield, Webhook,
  Gauge, Book, ArrowRight, Terminal,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'REST API',
  description:
    'Comprehensive REST API with OpenAPI specification, rate limiting, webhooks, and SDK support for custom integrations.',
  canonical: '/features/rest-api',
})

const capabilities = [
  {
    icon: <Code className="w-5 h-5" />,
    title: 'Complete REST API',
    description:
      'Every feature in Mission Control is accessible through a RESTful API, enabling full programmatic control over monitoring, automation, infrastructure, and administration.',
  },
  {
    icon: <FileText className="w-5 h-5" />,
    title: 'OpenAPI Specification',
    description:
      'The API is fully documented with an OpenAPI 3.0 specification, enabling auto-generated client libraries, interactive documentation, and testing tools.',
  },
  {
    icon: <Gauge className="w-5 h-5" />,
    title: 'Rate Limiting',
    description:
      'Configurable rate limits protect the platform from abuse while allowing legitimate integration workloads to operate at the throughput they need.',
  },
  {
    icon: <Webhook className="w-5 h-5" />,
    title: 'Webhooks',
    description:
      'Subscribe to events via webhooks to receive real-time notifications for alerts, infrastructure changes, and operational events in external systems.',
  },
  {
    icon: <Terminal className="w-5 h-5" />,
    title: 'SDK & Client Libraries',
    description:
      'Official client libraries for TypeScript, Python, Go, and PowerShell provide type-safe, ergonomic access to the API for rapid integration development.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'API Key Management',
    description:
      'Create scoped API keys with granular permissions, expiration dates, and usage tracking — ensuring integrations have only the access they need.',
  },
]

export default function RestApiPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'REST API' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Code className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">REST</span> API
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control exposes a comprehensive REST API that provides programmatic
              access to every feature in the platform. Whether you are building custom
              integrations, automating operational workflows, or embedding Mission Control
              data into your own applications, the API provides a clean, well-documented
              interface for every operation.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The API follows RESTful conventions with JSON payloads, standard HTTP methods,
              and consistent error handling. Every endpoint is documented in the interactive
              API reference with request/response examples, and the OpenAPI specification
              enables auto-generation of client libraries in any language.
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
            <h2 className="text-2xl font-bold mb-4">Integrate with Everything</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The Mission Control API is designed for extensibility. Webhooks deliver real-time
              event notifications to your existing tools — ServiceNow, Jira, Slack, custom
              dashboards, or any HTTP-capable system. The API enables bidirectional
              integration, so external systems can both receive data from Mission Control and
              trigger operations within it.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Official SDKs for TypeScript, Python, Go, and PowerShell provide type-safe
              clients that handle authentication, pagination, error handling, and rate limiting
              automatically. These SDKs are used internally by Mission Control&apos;s own
              plugins, ensuring they are thoroughly tested and production-ready. Custom API
              keys with scoped permissions enable third-party integrations to access only the
              data and operations they require.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Build on a Solid Foundation</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Explore the interactive API reference, browse the SDK documentation, and start
              building integrations with Mission Control in minutes.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/api-reference" className="btn-primary">
                API Reference
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/plugin-framework" className="btn-outline">
                Plugin Framework
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
