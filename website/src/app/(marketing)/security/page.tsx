import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Shield, Lock, Key, Eye, Server, FileCheck, ArrowRight, CheckCircle } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Security',
  description: 'Mission Control security details. Learn about encryption, authentication, authorization, network security, data protection, and our vulnerability disclosure program.',
  canonical: '/security',
})

const sections = [
  {
    icon: Lock,
    title: 'Encryption',
    items: [
      'TLS 1.3 enforced for all client-server communication',
      'mTLS with short-lived X.509 certificates for agent-server channels',
      'AES-256-GCM encryption for all data at rest',
      'Hardware Security Module (HSM) integration for cryptographic key management',
      'Key rotation policies with automated certificate renewal',
    ],
  },
  {
    icon: Key,
    title: 'Authentication',
    items: [
      'Token-based API authentication with API keys and OAuth 2.0',
      'Multi-factor authentication (TOTP, WebAuthn/FIDO2)',
      'SAML 2.0 and OIDC for SSO integration',
      'Service account authentication for automated workflows',
      'Session management with configurable idle timeout and concurrent session limits',
    ],
  },
  {
    icon: Eye,
    title: 'Authorization',
    items: [
      'Role-based access control (RBAC) with predefined and custom roles',
      'Attribute-based access control (ABAC) for fine-grained policies',
      'Tenant-scoped access isolation in multi-tenant deployments',
      'API endpoint-level permission granularity',
      'Audit logging for all authorization decisions',
    ],
  },
  {
    icon: Server,
    title: 'Network Security',
    items: [
      'Zero-trust network architecture for all service communication',
      'Micro-segmentation between platform components',
      'DDoS protection with automatic traffic analysis and filtering',
      'IP allowlisting for API access',
      'Web Application Firewall (WAF) for web traffic protection',
    ],
  },
  {
    icon: FileCheck,
    title: 'Data Protection',
    items: [
      'Data residency controls with region-specific storage',
      'Automated data retention and lifecycle policies',
      'Point-in-time recovery with encrypted backups',
      'Data classification and labeling support',
      'GDPR data subject request tooling built-in',
    ],
  },
  {
    icon: Shield,
    title: 'Operational Security',
    items: [
      'Continuous security monitoring with SIEM integration',
      'Automated vulnerability scanning in CI/CD pipeline',
      'Regular third-party penetration testing',
      'Security training for all engineering staff',
      'Incident response plan with tabletop exercises',
    ],
  },
]

export default function SecurityPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Security' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Security</span>
            </h1>
            <p className="section-subtitle">
              Mission Control is built with security at every layer. We follow industry best practices and maintain rigorous security standards to protect your infrastructure and data.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-16">
            {sections.map((section) => (
              <div key={section.title} className="glass rounded-xl p-6 card-hover">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center">
                    <section.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                  </div>
                  <h3 className="text-lg font-semibold">{section.title}</h3>
                </div>
                <ul className="space-y-2.5">
                  {section.items.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-surface-600 dark:text-surface-300">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="glass rounded-xl p-8 mb-12">
            <h3 className="text-xl font-semibold mb-4">Bug Bounty Program</h3>
            <p className="text-surface-500 dark:text-surface-400 text-sm mb-6">
              We operate a responsible vulnerability disclosure program through HackerOne. If you discover a security vulnerability in Mission Control, please report it through our program. We are committed to working with security researchers to address issues promptly and transparently.
            </p>
            <div className="grid sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-surface-50 dark:bg-surface-800/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold gradient-text">72h</div>
                <div className="text-xs text-surface-500 dark:text-surface-400">Avg. Response Time</div>
              </div>
              <div className="bg-surface-50 dark:bg-surface-800/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold gradient-text">$500+</div>
                <div className="text-xs text-surface-500 dark:text-surface-400">Bounty Range</div>
              </div>
              <div className="bg-surface-50 dark:bg-surface-800/50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold gradient-text">30 days</div>
                <div className="text-xs text-surface-500 dark:text-surface-400">Fix SLA (Critical)</div>
              </div>
            </div>
            <Link href="/trust-center" className="text-sm text-mc-600 dark:text-mc-400 hover:underline inline-flex items-center gap-1">
              View our full Trust Center <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
