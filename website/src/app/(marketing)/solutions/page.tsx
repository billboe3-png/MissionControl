import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Building2,
  Server,
  GraduationCap,
  Landmark,
  HeartPulse,
  Banknote,
  Factory,
  Store,
  ArrowRight,
  CheckCircle2,
  Shield,
  Zap,
  BarChart3,
  Globe,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Solutions',
  description:
    'Mission Control delivers tailored IT operations solutions for every industry — from enterprise data centers to small businesses, MSPs, education, government, healthcare, finance, and manufacturing.',
  canonical: '/solutions',
})

const solutions = [
  {
    icon: Building2,
    title: 'Enterprise',
    href: '/solutions/enterprise',
    description:
      'Unified visibility across complex, multi-site infrastructure with role-based access, compliance tooling, and enterprise-grade security.',
  },
  {
    icon: Server,
    title: 'Managed Service Providers',
    href: '/solutions/msp',
    description:
      'Multi-tenant operations, white-label dashboards, and automated service delivery to manage hundreds of client environments from one pane of glass.',
  },
  {
    icon: GraduationCap,
    title: 'Education',
    href: '/solutions/education',
    description:
      'Simplify campus IT management with centralized monitoring for labs, dorms, classrooms, and administrative systems on constrained budgets.',
  },
  {
    icon: Landmark,
    title: 'Government',
    href: '/solutions/government',
    description:
      'Meet strict compliance requirements with FedRAMP-ready architecture, audit trails, and air-gapped deployment options for public sector agencies.',
  },
  {
    icon: HeartPulse,
    title: 'Healthcare',
    href: '/solutions/healthcare',
    description:
      'Ensure 99.99% uptime for critical clinical systems with HIPAA-aware monitoring, automated incident response, and real-time alerting.',
  },
  {
    icon: Banknote,
    title: 'Finance',
    href: '/solutions/finance',
    description:
      'Protect transaction integrity with sub-second latency monitoring, real-time fraud detection hooks, and SOC 2 compliance reporting.',
  },
  {
    icon: Factory,
    title: 'Manufacturing',
    href: '/solutions/manufacturing',
    description:
      'Monitor OT and IT convergence with edge-aware agents, SCADA integration, and predictive maintenance workflows for production environments.',
  },
  {
    icon: Store,
    title: 'Small Business',
    href: '/solutions/small-business',
    description:
      'Enterprise-grade monitoring without the enterprise price tag — get started in minutes with a lightweight agent and pre-built dashboards.',
  },
]

const capabilities = [
  {
    icon: Shield,
    title: 'Security-First Design',
    description:
      'Every deployment inherits end-to-end encryption, RBAC, SSO integration, and credential vaulting out of the box.',
  },
  {
    icon: Zap,
    title: 'Automated Remediation',
    description:
      'Playbooks and AI-assisted operations detect and resolve common issues before they reach human operators.',
  },
  {
    icon: BarChart3,
    title: 'Actionable Reporting',
    description:
      'Executive-ready dashboards and scheduled reports keep stakeholders informed without manual data wrangling.',
  },
  {
    icon: Globe,
    title: 'Multi-Site, Multi-Cloud',
    description:
      'Manage on-premises, hybrid, and multi-cloud estates from a single operational workspace — no matter how distributed.',
  },
]

export default function SolutionsPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Solutions' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h1 className="section-title mb-6">
              IT Operations Solutions for{' '}
              <span className="gradient-text">Every Industry</span>
            </h1>
            <p className="section-subtitle">
              Mission Control adapts to the unique demands of your sector.
              Whether you run a global enterprise or a growing small business,
              our platform scales to meet your compliance, performance, and
              operational requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
            {solutions.map((solution) => {
              const Icon = solution.icon
              return (
                <Link
                  key={solution.href}
                  href={solution.href}
                  className="glass rounded-xl p-6 card-hover group"
                >
                  <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center mb-4 group-hover:bg-mc-500/20 transition-colors">
                    <Icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{solution.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
                    {solution.description}
                  </p>
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-mc-600 dark:text-mc-400 group-hover:gap-2.5 transition-all">
                    Learn more <ArrowRight className="w-4 h-4" />
                  </span>
                </Link>
              )
            })}
          </div>

          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
              Why Organizations Choose Mission Control
            </h2>
            <p className="text-surface-500 dark:text-surface-400">
              Regardless of industry, every Mission Control deployment delivers
              the same foundational capabilities that modern IT teams demand.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {capabilities.map((cap) => {
              const Icon = cap.icon
              return (
                <div key={cap.title} className="glass rounded-xl p-6">
                  <Icon className="w-8 h-8 text-mc-600 dark:text-mc-400 mb-4" />
                  <h3 className="font-semibold mb-2">{cap.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    {cap.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide text-center">
          <h2 className="section-title mb-4">
            Ready to Transform Your IT Operations?
          </h2>
          <p className="section-subtitle mb-8">
            Explore how Mission Control addresses the specific challenges of
            your industry.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Schedule a Consultation
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/pricing" className="btn-outline">
              View Pricing
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
