import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Building2,
  ArrowRight,
  CheckCircle2,
  Shield,
  Globe,
  Users,
  BarChart3,
  Server,
  Lock,
  Workflow,
  AlertTriangle,
  Layers,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Enterprise IT Operations',
  description:
    'Mission Control provides enterprise organizations with unified infrastructure visibility, RBAC, compliance reporting, and AI-assisted operations across multi-site, multi-cloud environments.',
  canonical: '/solutions/enterprise',
})

const challenges = [
  {
    icon: AlertTriangle,
    title: 'Fragmented Tooling',
    description:
      'Large organizations accumulate dozens of monitoring and management tools over time, creating blind spots and alert fatigue as data lives in disconnected silos.',
  },
  {
    icon: Layers,
    title: 'Multi-Cloud Complexity',
    description:
      'Hybrid and multi-cloud strategies introduce sprawl. Teams struggle to maintain a coherent operational picture across AWS, Azure, GCP, and on-premises data centers.',
  },
  {
    icon: Users,
    title: 'Scale and Access Control',
    description:
      'Thousands of servers and hundreds of engineers demand granular role-based access control, audit trails, and delegation models that legacy tools cannot provide.',
  },
  {
    icon: Shield,
    title: 'Compliance Burden',
    description:
      'SOC 2, ISO 27001, and industry-specific regulations require continuous evidence collection, which pulls engineers away from value-adding work.',
  },
]

const benefits = [
  {
    icon: Globe,
    title: 'Single Pane of Glass',
    description:
      'Aggregate metrics, logs, and configuration state from every cloud provider, data center, and edge location into one unified operational workspace.',
  },
  {
    icon: Lock,
    title: 'Enterprise-Grade Security',
    description:
      'SSO via SAML and OIDC, granular RBAC with team scoping, credential vaulting, and full audit logging satisfy the strictest security reviews.',
  },
  {
    icon: BarChart3,
    title: 'Executive Reporting',
    description:
      'Automated SLA dashboards, executive summaries, and compliance reports keep leadership informed without manual effort from engineering teams.',
  },
  {
    icon: Workflow,
    title: 'AI-Assisted Operations',
    description:
      'Mission Control Agent correlates events across the entire stack, surfaces root causes, and suggests remediation steps — reducing mean time to resolution by up to 60%.',
  },
  {
    icon: Server,
    title: 'Agent-Based Architecture',
    description:
      'Deploy the MC Agent across Linux, Windows, and macOS hosts for deep OS-level telemetry, package management, and remote shell access without VPN dependencies.',
  },
  {
    icon: Layers,
    title: 'Plugin Extensibility',
    description:
      'Extend Mission Control with custom plugins for proprietary systems, homegrown applications, and vendor-specific integrations via the open plugin framework.',
  },
]

const useCases = [
  'Global financial services firm consolidating 14 monitoring tools into Mission Control',
  'Manufacturing conglomerate gaining real-time visibility across 200+ factory floor servers',
  'Telecommunications provider automating patch compliance across 15,000 endpoints',
  'Retail enterprise correlating POS system health with supply chain infrastructure',
]

export default function EnterpriseSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Enterprise' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Building2 className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Enterprise
              </span>
            </div>
            <h1 className="section-title mb-6">
              Unified IT Operations for{' '}
              <span className="gradient-text">Complex Enterprises</span>
            </h1>
            <p className="section-subtitle !mx-0">
              Enterprise IT environments span continents, clouds, and thousands
              of assets. Mission Control replaces fragmented toolchains with a
              single operational platform that scales from your first data center
              to your hundredth.
            </p>
          </div>
        </div>
      </section>

      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <h2 className="text-2xl font-bold mb-8">
            The Challenges You Face
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {challenges.map((challenge) => {
              const Icon = challenge.icon
              return (
                <div
                  key={challenge.title}
                  className="glass rounded-xl p-6 flex gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-red-500/10 dark:bg-red-500/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{challenge.title}</h3>
                    <p className="text-sm text-surface-500 dark:text-surface-400">
                      {challenge.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container-wide">
          <h2 className="text-2xl font-bold mb-8">
            How Mission Control Solves It
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((benefit) => {
              const Icon = benefit.icon
              return (
                <div key={benefit.title} className="glass rounded-xl p-6 card-hover">
                  <Icon className="w-8 h-8 text-mc-600 dark:text-mc-400 mb-4" />
                  <h3 className="font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    {benefit.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-2xl font-bold mb-6">
                Enterprise Use Cases
              </h2>
              <ul className="space-y-4">
                {useCases.map((useCase, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-mc-600 dark:text-mc-400 mt-0.5 flex-shrink-0" />
                    <span className="text-surface-600 dark:text-surface-300">
                      {useCase}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-bold mb-4">
                Enterprise by the Numbers
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">60%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in mean time to resolution
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">14x</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Average tools consolidated per enterprise deployment
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">99.99%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Platform uptime SLA for enterprise customers
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container-wide text-center">
          <h2 className="section-title mb-4">
            Ready to Unify Your Enterprise IT?
          </h2>
          <p className="section-subtitle mb-8">
            Talk to our solutions engineering team about a tailored deployment
            plan for your organization.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Book an Enterprise Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/architecture" className="btn-outline">
              View Architecture
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
