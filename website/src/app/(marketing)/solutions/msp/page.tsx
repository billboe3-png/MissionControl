import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Server,
  ArrowRight,
  CheckCircle2,
  Users,
  LayoutDashboard,
  Shield,
  Bell,
  Settings,
  Layers,
  Workflow,
  AlertTriangle,
  Repeat,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Managed Service Providers',
  description:
    'Mission Control empowers MSPs with multi-tenant management, white-label dashboards, automated service delivery, and centralized monitoring across all client environments.',
  canonical: '/solutions/msp',
})

const challenges = [
  {
    icon: AlertTriangle,
    title: 'Client Sprawl',
    description:
      'Managing dozens or hundreds of client environments means juggling separate tools, credentials, and alerting pipelines — a recipe for missed incidents and burned-out technicians.',
  },
  {
    icon: Repeat,
    title: 'Repetitive Onboarding',
    description:
      'Every new client requires the same setup: deploy agents, configure monitoring, set up alerting, create dashboards. Without automation, onboarding takes days instead of minutes.',
  },
  {
    icon: Shield,
    title: 'Tenant Isolation',
    description:
      'Clients demand that their data and access remain strictly separated. Traditional multi-account setups are expensive and difficult to maintain at scale.',
  },
  {
    icon: Bell,
    title: 'Alert Fatigue',
    description:
      'When alerts from hundreds of clients flood a single NOC, technicians stop paying attention. Critical issues get buried under a mountain of warnings and informational events.',
  },
]

const benefits = [
  {
    icon: Layers,
    title: 'True Multi-Tenancy',
    description:
      'Each client gets isolated data, credentials, and access policies within a single Mission Control instance. Switch between client contexts in one click.',
  },
  {
    icon: LayoutDashboard,
    title: 'White-Label Dashboards',
    description:
      'Brand client-facing dashboards with your MSP logo and colors. Deliver polished, professional reporting that reinforces your brand with every interaction.',
  },
  {
    icon: Settings,
    title: 'Template-Driven Provisioning',
    description:
      'Create standardized onboarding templates for common client profiles. Deploy agents, configure monitors, and set up alerting in minutes, not days.',
  },
  {
    icon: Workflow,
    title: 'Automated Service Delivery',
    description:
      'Automate patch management, backup verification, security scans, and routine maintenance across every client from a single operations center.',
  },
  {
    icon: Bell,
    title: 'Intelligent Alert Routing',
    description:
      'Route alerts based on client priority, severity, and technician assignment. Escalation chains ensure nothing falls through the cracks.',
  },
  {
    icon: Users,
    title: 'Technician Role Management',
    description:
      'Assign technicians to specific client portfolios with scoped access. Junior techs see only what they need; senior engineers get full visibility.',
  },
]

const useCases = [
  'Regional MSP managing 300+ SMB clients from a unified operations center',
  'Cloud MSP automating Azure and AWS infrastructure monitoring for enterprise clients',
  'Security-focused MSP delivering managed SIEM and compliance reporting as a service',
  'Break-fix provider transitioning to proactive managed services with automated maintenance',
]

export default function MSPSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Managed Service Providers' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Server className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Managed Service Providers
              </span>
            </div>
            <h1 className="section-title mb-6">
              Manage Every Client from{' '}
              <span className="gradient-text">One Platform</span>
            </h1>
            <p className="section-subtitle !mx-0">
              Mission Control was built for the way MSPs actually work. Multi-
              tenant by design, not retrofitted. Every client is isolated, every
              technician is scoped, and every workflow is automatable — so you
              can scale your practice without scaling your headcount.
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
                MSP Use Cases
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
                MSP Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">300+</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Clients managed per MSP technician on average
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">85%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in new client onboarding time
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">40%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Increase in recurring revenue per technician
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
            Ready to Scale Your MSP Practice?
          </h2>
          <p className="section-subtitle mb-8">
            See how Mission Control helps MSPs deliver more services to more
            clients without growing their team.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Book an MSP Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/pricing" className="btn-outline">
              View MSP Pricing
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
