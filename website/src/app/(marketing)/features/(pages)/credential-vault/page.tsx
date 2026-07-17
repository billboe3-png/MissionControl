import { Metadata } from 'next'
import Link from 'next/link'
import {
  Shield, Key, RefreshCw, FileText,
  Lock, Eye, Users, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Credential Vault',
  description:
    'Enterprise-grade credential management with encryption, rotation policies, access auditing, and secrets injection.',
  canonical: '/features/credential-vault',
})

const capabilities = [
  {
    icon: <Lock className="w-5 h-5" />,
    title: 'AES-256 Encryption',
    description:
      'All credentials are encrypted at rest with AES-256 and in transit with TLS 1.3. The encryption key is stored separately from the data with hardware security module support.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Automatic Rotation',
    description:
      'Define rotation policies that automatically update credentials on a schedule, with integration to Active Directory, Linux PAM, and third-party secret managers.',
  },
  {
    icon: <Eye className="w-5 h-5" />,
    title: 'Access Auditing',
    description:
      'Every credential access is logged with operator identity, timestamp, purpose, and the specific secret retrieved — providing a complete audit trail for compliance.',
  },
  {
    icon: <Key className="w-5 h-5" />,
    title: 'Secrets Injection',
    description:
      'Inject credentials directly into automation workflows and remote sessions without exposing them to operators — supporting passwords, SSH keys, certificates, and API tokens.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'Access Policies',
    description:
      'Define who can access which credentials based on role, environment, site, and system type — with time-limited access and approval workflows for sensitive secrets.',
  },
  {
    icon: <AlertTriangle className="w-5 h-5" />,
    title: 'Expiry Monitoring',
    description:
      'Monitor certificate expirations, password ages, and API token validity — with proactive alerts before credentials expire and automated renewal where supported.',
  },
]

export default function CredentialVaultPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Credential Vault' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Shield className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Credential</span> Vault
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control includes an enterprise-grade credential vault that eliminates the
              security risks of managing passwords, SSH keys, certificates, and API tokens
              manually. Every secret is encrypted at rest, accessed only through controlled
              APIs, and logged for compliance — providing the security and auditability that
              modern IT operations demand.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The credential vault integrates with every module in Mission Control. Remote
              operations sessions authenticate using vault-stored credentials without exposing
              passwords to operators. Automation workflows inject secrets into scripts and API
              calls securely. Monitoring connections use vault-managed service accounts with
              automatic password rotation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {capabilities.map((cap) => (
              <div key={cap.title} className="glass rounded-xl p-6 card-hover">
                <div className="p-2.5 rounded-lg bg-mc-500/10 text-mc-600 dark:text-mc-400 w-fit mb-4">
                  {cap.icon}
                </div>
                <h3 className="font-semibold mb-2">{cap.title}</h3>
                <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
                  {cap.description}
                </p>
              </div>
            ))}
          </div>

          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-4">Zero-Trust Credential Management</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The credential vault implements zero-trust principles for secrets management.
              No operator ever sees or handles the raw credential value — credentials are
              injected directly into the target system through secure APIs. Access is granted
              only to authenticated, authorized operators for specific systems and specific
              purposes, and every access event is logged with full context.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Rotation policies ensure that credentials are regularly updated, reducing the
              window of exposure if a secret is compromised. The vault supports multiple
              rotation strategies including scheduled rotation, event-triggered rotation, and
              manual rotation with approval workflows. Integration with Active Directory,
              Linux PAM, and external secret managers like HashiCorp Vault provides flexibility
              to match your existing credential management practices.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Secure Every Credential</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control&apos;s credential vault to encrypt, rotate, and audit every
              secret across your infrastructure — without the overhead of a separate secrets
              management platform.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/remote-operations" className="btn-outline">
                Remote Operations
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
