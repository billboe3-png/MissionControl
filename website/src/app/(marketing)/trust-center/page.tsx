import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Shield, Lock, Eye, FileCheck, Server, Bug, CheckCircle, ArrowRight } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Trust Center',
  description: 'Mission Control Trust Center. Learn about our security practices, encryption standards, compliance certifications, architecture, and vulnerability disclosure policy.',
  canonical: '/trust-center',
})

const pillars = [
  {
    icon: Lock,
    title: 'Encryption',
    description: 'All data is encrypted in transit and at rest. We use TLS 1.3 for transport encryption, AES-256 for data at rest, and mTLS for agent communication.',
    details: [
      'TLS 1.3 for all API and web traffic',
      'AES-256-GCM for data at rest encryption',
      'mTLS with short-lived certificates for agent communication',
      'Hardware Security Module (HSM) for key management',
    ],
  },
  {
    icon: Shield,
    title: 'Security Architecture',
    description: 'Defense-in-depth security architecture with network segmentation, least-privilege access, and continuous monitoring.',
    details: [
      'Zero-trust network architecture',
      'Micro-segmented service communication',
      'Least-privilege service accounts',
      'Continuous security monitoring and alerting',
      'Regular penetration testing by independent firms',
    ],
  },
  {
    icon: FileCheck,
    title: 'Compliance',
    description: 'Mission Control supports compliance with major regulatory frameworks. We maintain our own certifications and provide tools to help you achieve yours.',
    details: [
      'SOC 2 Type II certified',
      'ISO 27001 certified',
      'GDPR compliant with data residency controls',
      'HIPAA BAA available for healthcare customers',
      'FedRAMP authorization in progress',
    ],
  },
  {
    icon: Eye,
    title: 'Transparency',
    description: 'We believe in full transparency about our security practices, incident response, and data handling.',
    details: [
      'Public status page with real-time updates',
      'Security incident notification within 24 hours',
      'Annual third-party security audit reports',
      'Transparent data processing agreements',
    ],
  },
  {
    icon: Server,
    title: 'Infrastructure',
    description: 'Our production infrastructure is designed for resilience and security at every layer.',
    details: [
      'Multi-region deployment with active-active failover',
      'Automated infrastructure patching and hardening',
      'Network intrusion detection and prevention',
      'DDoS protection and rate limiting',
      'Immutable infrastructure with zero-downtime deployments',
    ],
  },
  {
    icon: Bug,
    title: 'Vulnerability Disclosure',
    description: 'We operate a responsible vulnerability disclosure program and maintain a bug bounty for security researchers.',
    details: [
      'Coordinated vulnerability disclosure policy',
      'Bug bounty program via HackerOne',
      'Security advisories published for all CVEs',
      'Average remediation time: 72 hours for critical issues',
    ],
  },
]

export default function TrustCenterPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Trust Center' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Trust Center</span>
            </h1>
            <p className="section-subtitle">
              Security and trust are foundational to Mission Control. We invest heavily in protecting our platform, our customers, and their data.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {pillars.map((pillar) => (
              <div key={pillar.title} className="glass rounded-xl p-6 card-hover">
                <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mb-4">
                  <pillar.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{pillar.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 text-sm mb-4">
                  {pillar.description}
                </p>
                <ul className="space-y-2">
                  {pillar.details.map((detail) => (
                    <li key={detail} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-3.5 h-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-surface-600 dark:text-surface-300">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="glass rounded-xl p-12 text-center">
            <h2 className="text-2xl font-bold mb-4">Security Questions?</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-xl mx-auto">
              If you have questions about our security practices, need a copy of our SOC 2 report, or want to report a vulnerability, our security team is here to help.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/security" className="btn-primary">
                Security Details
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/contact" className="btn-secondary">
                Contact Security Team
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
