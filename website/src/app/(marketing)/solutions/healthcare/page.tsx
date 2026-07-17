import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  HeartPulse,
  ArrowRight,
  CheckCircle2,
  Shield,
  Activity,
  Clock,
  Server,
  Users,
  AlertTriangle,
  Lock,
  Stethoscope,
  FileCheck,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Healthcare IT Operations',
  description:
    'Mission Control keeps healthcare systems running with HIPAA-aware monitoring, automated incident response, real-time clinical system alerting, and comprehensive audit logging.',
  canonical: '/solutions/healthcare',
})

const challenges = [
  {
    icon: AlertTriangle,
    title: 'Zero Tolerance for Downtime',
    description:
      'EHR systems, PACS imaging, lab interfaces, and pharmacy systems directly impact patient care. Even minutes of downtime can delay treatment and endanger lives.',
  },
  {
    icon: Lock,
    title: 'HIPAA Compliance',
    description:
      'Protected health information must be encrypted at rest and in transit. Access to systems containing PHI requires detailed audit trails and strict access controls.',
  },
  {
    icon: Activity,
    title: 'Complex Integration Landscape',
    description:
      'Healthcare IT spans HL7 interfaces, FHIR APIs, DICOM networks, and legacy systems. Monitoring these integrations requires deep protocol awareness.',
  },
  {
    icon: Clock,
    title: '24/7/365 Operations',
    description:
      'Hospitals never close. IT teams must maintain monitoring coverage across all shifts with clear escalation paths, even during holidays and weekends.',
  },
]

const benefits = [
  {
    icon: HeartPulse,
    title: 'Clinical System Monitoring',
    description:
      'Monitor EHR availability, HL7 message flow, DICOM transfer rates, and pharmacy interface health in real-time. Detect degradation before it impacts patient care.',
  },
  {
    icon: Shield,
    title: 'HIPAA-Compliant Architecture',
    description:
      'All data encrypted with AES-256 at rest and TLS 1.3 in transit. Role-based access control ensures only authorized personnel access PHI-containing system data.',
  },
  {
    icon: Clock,
    title: '24/7 Automated Response',
    description:
      'Playbooks automatically restart failed services, clear backed-up message queues, and escalate to on-call staff based on severity and time of day.',
  },
  {
    icon: FileCheck,
    title: 'Audit-Ready Compliance',
    description:
      'Every access, change, and configuration modification is logged with user identity and timestamp. Generate HIPAA audit reports on demand.',
  },
  {
    icon: Stethoscope,
    title: 'Medical Device Integration',
    description:
      'Monitor network-connected medical devices — infusion pumps, patient monitors, ventilators — through passive network discovery and SNMP polling.',
  },
  {
    icon: Users,
    title: 'Department-Level Visibility',
    description:
      'Organize monitoring by department, floor, or care unit. Clinical engineers see only the systems relevant to their area of responsibility.',
  },
]

const useCases = [
  'Regional hospital system monitoring EHR, PACS, and lab systems across 5 facilities',
  'Health network automating HL7 interface monitoring and alerting for 200+ integration points',
  'Telehealth provider ensuring sub-second video consultation availability during peak hours',
  'Clinical research lab tracking temperature-sensitive storage and LIMS system uptime',
]

export default function HealthcareSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Healthcare' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <HeartPulse className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Healthcare
              </span>
            </div>
            <h1 className="section-title mb-6">
              Keep Clinical Systems Running{' '}
              <span className="gradient-text">Without Interruption</span>
            </h1>
            <p className="section-subtitle !mx-0">
              In healthcare, IT failures don&apos;t just cost money — they
              impact patient outcomes. Mission Control provides the real-time
              visibility, automated response, and compliance documentation that
              healthcare organizations need to keep critical systems online
              around the clock.
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
                Healthcare Use Cases
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
                Healthcare Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">99.99%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    EHR uptime achieved across monitored hospital systems
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">3 min</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Average detection-to-response time for clinical system failures
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">100%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    HIPAA audit pass rate for monitored environments
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
            Ready to Protect Patient Care?
          </h2>
          <p className="section-subtitle mb-8">
            Mission Control understands the unique demands of healthcare IT.
            Let us show you how to achieve zero-downtime clinical operations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Schedule a Healthcare Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/security" className="btn-outline">
              View HIPAA Compliance
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
