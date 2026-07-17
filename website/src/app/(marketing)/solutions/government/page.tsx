import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  Landmark,
  ArrowRight,
  CheckCircle2,
  Shield,
  FileCheck,
  Lock,
  Server,
  Users,
  AlertTriangle,
  Eye,
  ClipboardList,
  Network,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Government IT Operations',
  description:
    'Mission Control provides government agencies with compliant, auditable IT operations — supporting FedRAMP-aligned controls, air-gapped deployments, and comprehensive audit trails.',
  canonical: '/solutions/government',
})

const challenges = [
  {
    icon: Shield,
    title: 'Rigid Compliance Mandates',
    description:
      'Government agencies must adhere to NIST, FISMA, FedRAMP, and agency-specific security frameworks. Demonstrating continuous compliance requires extensive documentation and evidence collection.',
  },
  {
    icon: Lock,
    title: 'Air-Gapped Environments',
    description:
      'Classified and sensitive networks cannot reach the public internet. Most commercial monitoring tools require cloud connectivity, making them unusable in restricted environments.',
  },
  {
    icon: Eye,
    title: 'Audit Trail Requirements',
    description:
      'Every action on government infrastructure must be logged, attributable, and retrievable. Auditors demand detailed records of who accessed what, when, and why.',
  },
  {
    icon: Network,
    title: 'Legacy System Integration',
    description:
      'Government IT includes decades-old mainframes, custom applications, and systems that predate modern APIs. Monitoring tools must bridge the gap between old and new.',
  },
]

const benefits = [
  {
    icon: Server,
    title: 'On-Premises Deployment',
    description:
      'Deploy Mission Control entirely within your network boundary. No data leaves your environment. Supports classified networks and air-gapped installations.',
  },
  {
    icon: ClipboardList,
    title: 'Continuous Compliance Reporting',
    description:
      'Automated evidence collection maps platform activities to NIST and FISMA controls. Generate audit-ready reports in hours instead of weeks.',
  },
  {
    icon: Lock,
    title: 'Cryptographic Audit Logging',
    description:
      'Every user action, configuration change, and API call is logged with tamper-evident audit trails. Cryptographic signatures prevent log alteration.',
  },
  {
    icon: Users,
    title: 'Granular Access Control',
    description:
      'Map access policies to government organizational structures. Support for clearance-based scoping, duty-officer rotations, and multi-level security labels.',
  },
  {
    icon: FileCheck,
    title: 'System Authorization Support',
    description:
      'Mission Control ships with ATO documentation templates, security configuration guides, and risk assessment templates to accelerate your authorization process.',
  },
  {
    icon: Server,
    title: 'Heterogeneous Infrastructure',
    description:
      'Monitor mainframes, UNIX servers, Windows systems, and custom applications through a unified interface. The MC Agent supports legacy operating systems and protocols.',
  },
]

const useCases = [
  'Federal agency consolidating monitoring across 50 data centers with air-gapped deployment',
  'State government automating FISMA compliance evidence collection for annual audits',
  'Defense contractor managing classified and unclassified networks from separate Mission Control instances',
  'Municipal government monitoring citizen-facing services and internal administrative systems',
]

export default function GovernmentSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Government' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <Landmark className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Government
              </span>
            </div>
            <h1 className="section-title mb-6">
              Secure, Compliant IT Operations for{' '}
              <span className="gradient-text">Government Agencies</span>
            </h1>
            <p className="section-subtitle !mx-0">
              Mission Control is designed for the unique demands of government
              IT. Deploy on-premises, meet compliance frameworks out of the box,
              and maintain complete audit visibility — whether you manage
              civilian services or classified networks.
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
                Government Use Cases
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
                Government Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">75%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in audit preparation time and cost
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">100%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    On-premises deployment with zero external data dependencies
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">30 days</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Average time from deployment to full operational visibility
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
            Ready to Modernize Government IT?
          </h2>
          <p className="section-subtitle mb-8">
            Our government solutions team understands public sector procurement,
            compliance requirements, and deployment constraints.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Contact Government Sales
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/security" className="btn-outline">
              View Security Posture
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
