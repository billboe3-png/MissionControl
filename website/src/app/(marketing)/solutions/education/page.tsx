import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  GraduationCap,
  ArrowRight,
  CheckCircle2,
  Monitor,
  Wifi,
  DollarSign,
  Shield,
  Users,
  Server,
  AlertTriangle,
  Clock,
  Settings,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Education IT Management',
  description:
    'Mission Control helps educational institutions monitor labs, campus networks, and administrative systems with centralized management, budget-friendly pricing, and automated maintenance.',
  canonical: '/solutions/education',
})

const challenges = [
  {
    icon: DollarSign,
    title: 'Tight Budgets',
    description:
      'Educational institutions operate with limited IT budgets and often rely on student workers. Enterprise monitoring tools are prohibitively expensive and require specialized training.',
  },
  {
    icon: Clock,
    title: 'Seasonal Demand Spikes',
    description:
      'Registration, exam periods, and the start of each semester create sudden surges in network and system load. Without proactive monitoring, outages disrupt learning.',
  },
  {
    icon: Wifi,
    title: 'Distributed Campus Infrastructure',
    description:
      'Computer labs, lecture halls, dormitories, libraries, and administrative buildings each present unique networking and systems challenges that span multiple buildings and floors.',
  },
  {
    icon: Users,
    title: 'Limited IT Staff',
    description:
      'Many institutions have lean IT teams stretched across campus. Manual monitoring and maintenance consume time that should be spent on strategic projects.',
  },
]

const benefits = [
  {
    icon: Monitor,
    title: 'Lab Health Monitoring',
    description:
      'Track the availability and performance of every workstation, printer, and projector across campus labs. Automated remediation restarts frozen machines and clears print queues.',
  },
  {
    icon: Server,
    title: 'LMS and Portal Monitoring',
    description:
      'Monitor learning management systems, student portals, and email services from the same dashboard. Get alerted before students notice problems during exam submissions.',
  },
  {
    icon: Settings,
    title: 'Automated Lab Setup',
    description:
      'Use playbooks to prepare computer labs for each semester — install required software, apply configurations, and verify readiness without visiting each room.',
  },
  {
    icon: Shield,
    title: 'Student Data Protection',
    description:
      'Role-based access ensures student workers only see what they need. Full audit logging supports FERPA compliance requirements without administrative overhead.',
  },
  {
    icon: Wifi,
    title: 'Network Health Visibility',
    description:
      'Monitor Wi-Fi access points, switches, and DNS across every building. Correlate user-reported issues with real-time infrastructure metrics to resolve problems faster.',
  },
  {
    icon: AlertTriangle,
    title: 'Predictive Capacity Planning',
    description:
      'Track resource utilization trends across academic calendars. Forecast when storage, bandwidth, or compute capacity will be exhausted and plan upgrades proactively.',
  },
]

const useCases = [
  'University IT department monitoring 2,000+ lab workstations across 40 buildings',
  'Community college automating software deployment to 500 computer labs each semester',
  'School district managing Chromebook fleets and Wi-Fi infrastructure across 25 campuses',
  'Research institution tracking high-performance computing clusters and storage arrays',
]

export default function EducationSolutionPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Solutions', href: '/solutions' },
          { label: 'Education' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-lg bg-mc-500/10 dark:bg-mc-500/20 flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-mc-600 dark:text-mc-400" />
              </div>
              <span className="text-sm font-medium text-mc-600 dark:text-mc-400 uppercase tracking-wider">
                Education
              </span>
            </div>
            <h1 className="section-title mb-6">
              IT Operations for{' '}
              <span className="gradient-text">Educational Institutions</span>
            </h1>
            <p className="section-subtitle !mx-0">
              From computer labs to campus-wide networks, Mission Control gives
              educational IT teams the visibility and automation they need to
              keep students and faculty connected — all within budget constraints
              that schools actually face.
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
                Education Use Cases
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
                Education Success Metrics
              </h3>
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold gradient-text">92%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Reduction in lab-related help desk tickets
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">4 hrs</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Saved per week on manual lab health checks
                  </p>
                </div>
                <div>
                  <div className="text-3xl font-bold gradient-text">70%</div>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    Faster semester deployment with automated playbooks
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
            Ready to Modernize Campus IT?
          </h2>
          <p className="section-subtitle mb-8">
            Mission Control offers discounted pricing for educational
            institutions. Get started with a free pilot in your largest lab.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Request an Education Pilot
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/pricing" className="btn-outline">
              View Education Pricing
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
