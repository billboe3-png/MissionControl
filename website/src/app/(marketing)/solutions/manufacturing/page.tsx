import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Factory,
  ArrowRight,
  CheckCircle2,
  Shield,
  Activity,
  Clock,
  Server,
  Users,
  AlertTriangle,
  Cpu,
  Gauge,
  Wifi,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Manufacturing IT Operations',
  description:
    'Mission Control bridges IT and OT in manufacturing environments — monitoring production systems, edge infrastructure, SCADA networks, and predictive maintenance workflows from a single platform.',
  canonical: '/solutions/manufacturing',
})

const challenges = [
  {
    icon: AlertTriangle,
    title: 'IT/OT Convergence',
    description:
      'Manufacturing environments blend enterprise IT systems with operational technology — PLCs, HMIs, SCADA, and industrial networks. These domains have different protocols, priorities, and security requirements.',
  },
  {
    icon: Gauge,
    title: 'Production Uptime Pressure',
    description:
      'Every minute of unplanned downtime costs thousands in lost production. Traditional monitoring tools are too slow to catch issues before they halt production lines.',
  },
  {
    icon: Wifi,
    title: 'Edge and Remote Sites',
    description:
      'Factories, warehouses, and remote facilities often have limited connectivity. Monitoring tools that require constant cloud connectivity fail in these environments.',
  },
  {
    icon: Cpu,
    title: 'Legacy Industrial Systems',
    description:
      'Industrial control systems run on older operating systems that modern monitoring agents cannot support. Yet these systems are critical to production operations.',
  },
]

const benefits = [
  {
    icon: Activity,
    title: 'Production Line Monitoring',
    description:
      'Monitor OEE (Overall Equipment Effectiveness), cycle times, and production throughput in real-time. Correlate IT infrastructure health with production output metrics.',
  },
  {
    icon: Server,
    title: 'Edge-Aware Agent Deployment',
    description:
      'MC Agents operate at the edge with local buffering and store-and-forward capabilities. Monitoring continues even when connectivity to the central platform is interrupted.',
  },
  {
    icon: Shield,
    title: 'OT Network Isolation',
    description:
      'Maintain strict network segmentation between IT and OT environments. Mission Control respects Purdue model boundaries while providing unified visibility.',
  },
  {
    icon: Cpu,
    title: 'Legacy Protocol Support',
    description:
      'Monitor industrial systems via Modbus, OPC-UA, SNMP, and serial connections. Bridge legacy equipment into modern dashboards without replacing installed systems.',
  },
  {
    icon: Gauge,
    title: 'Predictive Maintenance',
    description:
      'Track equipment health metrics and usage patterns. Use historical trends to predict failures and schedule maintenance during planned production stops.',
  },
  {
    icon: Wifi,
    title: 'Multi-Site Factory Management',
    description:
      'Manage monitoring across dozens of factories from a single operations center. Compare performance metrics across sites and identify best practices.',
  },
]

const useCases = [
  'Automotive manufacturer monitoring production lines across 12 plants worldwide',
  'Food and beverage company tracking cold chain compliance from factory to warehouse',
  'Pharmaceutical manufacturer ensuring GMP compliance with continuous environmental monitoring',
  'Electronics manufacturer correlating SMT line performance with upstream supply chain data',
]

export default function ManufacturingSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Manufacturing' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Factory className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Manufacturing
              </span>
            </div>
            <h1 className="section-title mb-6">
              Bridge IT and OT for{' '}
              <span className="gradient-text">Uninterrupted Production</span>
            </h1>
            <p className="section-subtitle !mx-0">
              Manufacturing environments demand a different kind of monitoring.
              Mission Control understands the intersection of enterprise IT and
              operational technology, providing unified visibility from the
              factory floor to the executive dashboard — without compromising
              network segmentation or production safety.
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
                Manufacturing Use Cases
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
                Manufacturing Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">18%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Improvement in OEE through proactive infrastructure monitoring
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">45 min</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Average early warning before production-impacting failures
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">35%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in unplanned maintenance through predictive alerts
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
            Ready to Optimize Your Production Environment?
          </h2>
          <p className="section-subtitle mb-8">
            Mission Control understands the unique demands of manufacturing IT
            and OT. Let us show you how to bridge the gap.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Schedule a Manufacturing Demo
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
