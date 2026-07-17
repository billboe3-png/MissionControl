import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Store,
  ArrowRight,
  CheckCircle2,
  Shield,
  Zap,
  Clock,
  Server,
  Users,
  AlertTriangle,
  Settings,
  DollarSign,
  Rocket,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Small Business IT Operations',
  description:
    'Mission Control brings enterprise-grade monitoring to small businesses — affordable pricing, zero learning curve, pre-built dashboards, and automated maintenance that keeps your systems running.',
  canonical: '/solutions/small-business',
})

const challenges = [
  {
    icon: DollarSign,
    title: 'Budget Constraints',
    description:
      'Enterprise monitoring platforms charge per-host fees that quickly exceed a small business IT budget. Free tools lack the depth and reliability needed for production systems.',
  },
  {
    icon: Users,
    title: 'No Dedicated IT Staff',
    description:
      'Many small businesses rely on the owner or a generalist employee to handle IT. Complex monitoring tools with steep learning curves go unused or misconfigured.',
  },
  {
    icon: Clock,
    title: 'Downtime Is Devastating',
    description:
      'Without redundant systems or backup infrastructure, even a brief outage can mean lost revenue, missed deadlines, and damaged customer relationships.',
  },
  {
    icon: Settings,
    title: 'Too Many Tools to Manage',
    description:
      'Small businesses often cobble together free tools for different needs — one for uptime, one for backups, one for endpoints. This patchwork creates gaps and wastes time.',
  },
]

const benefits = [
  {
    icon: Zap,
    title: 'Five-Minute Setup',
    description:
      'Install the MC Agent, connect to Mission Control, and start monitoring immediately. Pre-built templates for common small business services mean you don\'t configure anything from scratch.',
  },
  {
    icon: Settings,
    title: 'Pre-Built Dashboards',
    description:
      'Out-of-the-box dashboards for Windows servers, Linux hosts, network devices, and cloud services show you what matters without any configuration.',
  },
  {
    icon: Shield,
    title: 'Automated Patch Management',
    description:
      'Keep systems updated without manual intervention. Schedule patching windows, approve updates, and verify compliance from a single interface.',
  },
  {
    icon: Rocket,
    title: 'Grows with You',
    description:
      'Start monitoring 5 devices. Scale to 50, 500, or 5,000 without re-architecting. Mission Control\'s pricing and architecture grow alongside your business.',
  },
  {
    icon: Server,
    title: 'Backup Monitoring',
    description:
      'Verify that backups complete successfully and test restore procedures automatically. Get alerted before backup failures become data loss incidents.',
  },
  {
    icon: AlertTriangle,
    title: 'Proactive Alerting',
    description:
      'Receive email, SMS, or Slack alerts when disk space runs low, services stop, or security events occur — before your customers notice the problem.',
  },
]

const useCases = [
  'Local accounting firm monitoring 20-server environment with zero dedicated IT staff',
  'Retail chain tracking POS system health across 8 store locations and a central office',
  'Professional services company automating patch management for 100 employee workstations',
  'E-commerce startup monitoring cloud infrastructure with budget-conscious tooling',
]

export default function SmallBusinessSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Small Business' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Store className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Small Business
              </span>
            </div>
            <h1 className="section-title mb-6">
              Enterprise-Grade Monitoring at{' '}
              <span className="gradient-text">Small Business Prices</span>
            </h1>
            <p className="section-subtitle !mx-0">
              You don&apos;t need a massive IT team or an enterprise budget to
              keep your systems healthy. Mission Control gives small businesses
              the same visibility and automation that large organizations rely on
              — at a price point that makes sense for growing companies.
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
                Small Business Use Cases
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
                Small Business Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">5 min</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    From installation to full operational visibility
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">75%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in after-hours emergency IT calls
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">$0</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Additional IT staff required for Mission Control operations
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
            Ready to Stop Worrying About IT?
          </h2>
          <p className="section-subtitle mb-8">
            Start with our Community Edition — free for up to 50 monitored
            devices. Upgrade when you need enterprise features.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/downloads" className="btn-primary">
              Download Community Edition
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
