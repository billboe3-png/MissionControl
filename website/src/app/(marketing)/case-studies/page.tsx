import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Building2, ArrowRight, TrendingUp, Clock, Server, Shield } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Case Studies',
  description: 'See how organizations use Mission Control to transform their IT operations. Real-world case studies from enterprises, MSPs, and government agencies.',
  canonical: '/case-studies',
})

const caseStudies = [
  {
    company: 'GlobalTech Financial Services',
    industry: 'Financial Services',
    icon: Shield,
    summary: 'How a leading financial institution reduced MTTR by 65% and achieved SOC 2 compliance with Mission Control.',
    challenge: 'GlobalTech Financial managed over 3,000 servers across three data centers using a combination of legacy tools and manual processes. Alert fatigue was causing missed incidents, and compliance auditing required weeks of manual evidence gathering.',
    result: 'After deploying Mission Control, GlobalTech consolidated their toolchain, automated compliance evidence collection, and reduced mean time to resolution from 4 hours to 85 minutes.',
    metrics: [
      { label: 'MTTR Reduction', value: '65%' },
      { label: 'Servers Managed', value: '3,000+' },
      { label: 'Compliance Audit Time', value: '75% faster' },
    ],
  },
  {
    company: 'Horizon Managed Services',
    industry: 'Managed Service Provider',
    icon: Building2,
    summary: 'How an MSP scaled from 50 to 500 clients without adding operational headcount.',
    challenge: 'Horizon Managed Services was hitting the limits of their existing monitoring stack. Managing 50 clients required a 12-person operations team, and each new client added significant operational overhead.',
    result: 'With Mission Control multi-tenancy and automation, Horizon now manages 500 clients with 14 operations staff. Playbook automation handles routine provisioning and incident response.',
    metrics: [
      { label: 'Clients Scaled', value: '50 to 500' },
      { label: 'Headcount Growth', value: 'Only 17%' },
      { label: 'Automation Savings', value: '$400K/year' },
    ],
  },
  {
    company: 'State Department of Education',
    industry: 'Government',
    icon: Server,
    summary: 'A state government agency modernized legacy infrastructure monitoring while meeting FedRAMP requirements.',
    challenge: 'The Department of Education operated aging monitoring systems that could not provide visibility into their cloud migration. They needed a FedRAMP-aligned solution that could span on-premises and AWS.',
    result: 'Mission Control provided unified visibility across their hybrid environment with FedRAMP-aligned security controls. The agent-based architecture simplified deployment across distributed school district networks.',
    metrics: [
      { label: 'Endpoints Managed', value: '12,000+' },
      { label: 'Environments Unified', value: 'On-prem + AWS' },
      { label: 'Alert Noise Reduction', value: '80%' },
    ],
  },
]

export default function CaseStudiesPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Case Studies' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Customer Case Studies</span>
            </h1>
            <p className="section-subtitle">
              Learn how leading organizations across industries are using Mission Control to transform their IT operations.
            </p>
          </div>

          <div className="space-y-8">
            {caseStudies.map((study) => (
              <div key={study.company} className="glass rounded-xl p-8 card-hover">
                <div className="flex flex-col lg:flex-row gap-8">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center">
                        <study.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                      </div>
                      <div>
                        <span className="text-xs text-surface-500 dark:text-surface-400 uppercase tracking-wide">
                          {study.industry}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-xl font-bold mb-3">{study.company}</h3>
                    <p className="text-mc-600 dark:text-mc-400 font-medium text-sm mb-4">
                      {study.summary}
                    </p>
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-sm font-semibold mb-1">Challenge</h4>
                        <p className="text-sm text-surface-500 dark:text-surface-400">{study.challenge}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold mb-1">Result</h4>
                        <p className="text-sm text-surface-500 dark:text-surface-400">{study.result}</p>
                      </div>
                    </div>
                  </div>
                  <div className="lg:w-64 flex-shrink-0">
                    <div className="space-y-4">
                      {study.metrics.map((metric) => (
                        <div key={metric.label} className="bg-surface-50 dark:bg-surface-800/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold gradient-text">{metric.value}</div>
                          <div className="text-xs text-surface-500 dark:text-surface-400 mt-1">{metric.label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-16 text-center">
            <h3 className="text-xl font-semibold mb-4">Have a Story to Share?</h3>
            <p className="text-surface-500 dark:text-surface-400 mb-6 max-w-xl mx-auto">
              We are always looking for customers willing to share their Mission Control success story. Reach out to learn about our customer advocacy program.
            </p>
            <Link href="/contact" className="btn-primary">
              Get in Touch
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
