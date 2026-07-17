import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Banknote,
  ArrowRight,
  CheckCircle2,
  Shield,
  Activity,
  Clock,
  Server,
  Users,
  AlertTriangle,
  Lock,
  TrendingUp,
  FileCheck,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Financial Services IT Operations',
  description:
    'Mission Control delivers real-time infrastructure monitoring for financial institutions — protecting transaction integrity, ensuring SOC 2 compliance, and minimizing latency across trading and banking platforms.',
  canonical: '/solutions/finance',
})

const challenges = [
  {
    icon: TrendingUp,
    title: 'Latency-Sensitive Operations',
    description:
      'Trading platforms, payment processors, and real-time risk systems operate on sub-millisecond timescales. Infrastructure degradation directly translates to financial losses.',
  },
  {
    icon: Lock,
    title: 'Regulatory Compliance',
    description:
      'SOX, PCI DSS, SOC 2, and Basel III requirements demand continuous monitoring, detailed access controls, and comprehensive evidence of operational controls.',
  },
  {
    icon: Shield,
    title: 'Fraud Detection Infrastructure',
    description:
      'Real-time fraud detection systems depend on low-latency data pipelines. Any infrastructure issue in these pipelines creates blind spots that fraudsters can exploit.',
  },
  {
    icon: Clock,
    title: 'Market Hours Constraints',
    description:
      'Scheduled maintenance windows are extremely limited. Infrastructure changes must be validated and deployed with zero risk of disrupting live trading or payment processing.',
  },
]

const benefits = [
  {
    icon: Activity,
    title: 'Sub-Second Latency Monitoring',
    description:
      'Track response times across trading engines, payment gateways, and API endpoints with millisecond precision. Detect latency anomalies before they impact transaction throughput.',
  },
  {
    icon: Shield,
    title: 'PCI DSS & SOC 2 Compliance',
    description:
      'Automated evidence collection for PCI DSS Requirement 10 (logging) and SOC 2 CC6.1 (logical access). Generate audit reports that satisfy external auditors.',
  },
  {
    icon: Server,
    title: 'Transaction Pipeline Monitoring',
    description:
      'Monitor message queues, data streams, and API chains that carry financial transactions. Alert on throughput drops, error rate spikes, and queue depth anomalies.',
  },
  {
    icon: Lock,
    title: 'Immutable Audit Trails',
    description:
      'Every configuration change, access event, and remediation action is logged with cryptographic integrity. Tamper-evident logs satisfy regulatory evidence requirements.',
  },
  {
    icon: Users,
    title: 'Segregation of Duties',
    description:
      'Role-based access enforces separation between development, operations, and audit functions. No single user can modify monitoring and hide their tracks.',
  },
  {
    icon: Clock,
    title: 'Zero-Downtime Change Management',
    description:
      'Validate configuration changes against production baselines before deployment. Automated rollback triggers if monitoring detects post-change anomalies.',
  },
]

const useCases = [
  'Investment bank monitoring trading infrastructure across 5 global data centers',
  'Payment processor ensuring PCI DSS compliance for cardholder data environments',
  'Insurance company automating SOX compliance evidence for financial reporting systems',
  'Fintech startup monitoring API gateway performance for real-time payment authorization',
]

export default function FinanceSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Finance' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Banknote className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Financial Services
              </span>
            </div>
            <h1 className="section-title mb-6">
              Protect Every Transaction with{' '}
              <span className="gradient-text">Real-Time Visibility</span>
            </h1>
            <p className="section-subtitle !mx-0">
              In financial services, infrastructure performance is business
              performance. Mission Control provides the real-time monitoring,
              compliance automation, and change management rigor that banks,
              insurers, and fintech companies need to operate with confidence.
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
                Financial Services Use Cases
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
                Financial Services Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">&lt;5ms</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Monitoring overhead on transaction processing latency
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">90%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Faster audit evidence collection for PCI DSS and SOC 2
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">$2M+</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Average annual savings from reduced downtime incidents
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
            Ready to Secure Your Financial Infrastructure?
          </h2>
          <p className="section-subtitle mb-8">
            Our financial services team understands the regulatory landscape and
            operational demands of the industry. Let&apos;s discuss your
            requirements.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Contact Financial Solutions
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/security" className="btn-outline">
              View Security & Compliance
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
