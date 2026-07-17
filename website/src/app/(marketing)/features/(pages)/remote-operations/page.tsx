import { Metadata } from 'next'
import Link from 'next/link'
import {
  MonitorSmartphone, Shield, FileText, Users,
  Terminal, Video, Key, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Remote Operations',
  description:
    'Secure remote desktop, SSH, and PowerShell access with session recording, RBAC, and audit logging for compliance.',
  canonical: '/features/remote-operations',
})

const capabilities = [
  {
    icon: <Terminal className="w-5 h-5" />,
    title: 'SSH & PowerShell Access',
    description:
      'Open terminal sessions directly from the browser to any Linux or Windows system — no SSH client or RDP tool installation required on operator workstations.',
  },
  {
    icon: <MonitorSmartphone className="w-5 h-5" />,
    title: 'Remote Desktop',
    description:
      'Access Windows desktops and servers through browser-based RDP with audio support, clipboard sharing, and drive mapping — secured through the credential vault.',
  },
  {
    icon: <Video className="w-5 h-5" />,
    title: 'Session Recording',
    description:
      'Record every remote session with full playback capability, providing an auditable trail of all administrative actions taken across your infrastructure.',
  },
  {
    icon: <Key className="w-5 h-5" />,
    title: 'Credential Injection',
    description:
      'Authenticate to remote systems using vault-stored credentials without ever exposing passwords to operators — supporting keyboard-interactive and key-based authentication.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'Role-Based Access',
    description:
      'Control who can connect to which systems with granular RBAC policies that support per-environment, per-site, and per-system access restrictions.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Audit & Compliance',
    description:
      'Generate compliance reports covering every remote session with operator identity, timestamp, duration, commands executed, and files transferred.',
  },
]

export default function RemoteOperationsPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Remote Operations' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <MonitorSmartphone className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Remote Operations</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides secure, browser-based remote access to every system in
              your infrastructure — eliminating the need for operators to install SSH clients,
              RDP tools, or VPN connections on their workstations. Every session is brokered
              through Mission Control, with credentials injected from the vault and full
              session recording for compliance.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Whether your team needs to SSH into a Linux server, connect to a Windows
              desktop via RDP, or execute PowerShell commands on a remote system, Mission
              Control provides a consistent, auditable experience. Sessions are tunneled
              through the platform rather than directly from the operator&apos;s workstation,
              adding a security boundary that prevents lateral movement and credential exposure.
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
            <h2 className="text-2xl font-bold mb-4">Secure by Design</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control&apos;s remote access architecture is designed around the principle
              of least privilege. Operators authenticate to Mission Control, which then brokers
              the connection to the target system using vault-stored credentials. The operator
              never sees or handles the target system&apos;s password, eliminating the most
              common vector for credential leakage.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Session recording captures every keystroke, command, and screen update — providing
              a complete audit trail that satisfies SOC 2, ISO 27001, HIPAA, and PCI DSS
              requirements. Recordings are stored encrypted and can be replayed through the
              browser for incident investigation, training, or compliance verification.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Secure Remote Access, Simplified</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Give your team secure, auditable remote access to every system — with session
              recording and credential vault integration — without deploying VPNs or managing
              SSH keys.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/credential-vault" className="btn-outline">
                Credential Vault
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
