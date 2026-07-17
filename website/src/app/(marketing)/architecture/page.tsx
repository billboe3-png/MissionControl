import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import {
  ArrowRight,
  Shield,
  Zap,
  Server,
  Users,
  Brain,
  Workflow,
  BarChart3,
  Globe,
  Lock,
  Layers,
  Database,
  Monitor,
  Wifi,
  Cog,
} from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Platform Architecture',
  description:
    'Explore Mission Control\'s layered architecture — from user interface through API gateway, processing agents, infrastructure integration, AI operations engine, automation workflows, and reporting pipeline.',
  canonical: '/architecture',
})

const layers = [
  {
    icon: Users,
    title: 'Users',
    color: 'bg-blue-500',
    lightColor: 'bg-blue-500/10 dark:bg-blue-500/20',
    textColor: 'text-blue-600 dark:text-blue-400',
    description:
      'Web UI, CLI, and REST API consumers access the platform through authenticated sessions with role-based access control.',
  },
  {
    icon: Monitor,
    title: 'Mission Control',
    color: 'bg-mc-500',
    lightColor: 'bg-mc-500/10 dark:bg-mc-500/20',
    textColor: 'text-mc-600 dark:text-mc-400',
    description:
      'The central platform serves as the operational workspace — correlating data, orchestrating actions, and presenting unified visibility.',
  },
  {
    icon: Server,
    title: 'Agents',
    color: 'bg-emerald-500',
    lightColor: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    textColor: 'text-emerald-600 dark:text-emerald-400',
    description:
      'MC Agents deployed across Linux, Windows, and macOS hosts collect telemetry, execute commands, and relay data back to the platform.',
  },
  {
    icon: Globe,
    title: 'Infrastructure',
    color: 'bg-amber-500',
    lightColor: 'bg-amber-500/10 dark:bg-amber-500/20',
    textColor: 'text-amber-600 dark:text-amber-400',
    description:
      'Servers, databases, network devices, cloud services, and containers — the heterogeneous infrastructure that agents discover and monitor.',
  },
  {
    icon: Brain,
    title: 'AI Operations',
    color: 'bg-violet-500',
    lightColor: 'bg-violet-500/10 dark:bg-violet-500/20',
    textColor: 'text-violet-600 dark:text-violet-400',
    description:
      'Machine learning models analyze patterns, detect anomalies, predict failures, and suggest remediation actions across the entire stack.',
  },
  {
    icon: Workflow,
    title: 'Automation',
    color: 'bg-rose-500',
    lightColor: 'bg-rose-500/10 dark:bg-rose-500/20',
    textColor: 'text-rose-600 dark:text-rose-400',
    description:
      'Playbooks and automated workflows execute remediation, provisioning, patching, and maintenance tasks without human intervention.',
  },
  {
    icon: BarChart3,
    title: 'Reporting',
    color: 'bg-cyan-500',
    lightColor: 'bg-cyan-500/10 dark:bg-cyan-500/20',
    textColor: 'text-cyan-600 dark:text-cyan-400',
    description:
      'Dashboards, scheduled reports, compliance evidence, and executive summaries surface the insights stakeholders need.',
  },
]

const principles = [
  {
    icon: Shield,
    title: 'Security by Default',
    description:
      'End-to-end encryption, credential vaulting, RBAC, and audit logging are not optional add-ons — they are fundamental to every component.',
  },
  {
    icon: Layers,
    title: 'Modular Plugin Architecture',
    description:
      'Every integration is a plugin. New infrastructure types, cloud providers, and protocols are added without modifying core platform code.',
  },
  {
    icon: Zap,
    title: 'Edge-First Data Collection',
    description:
      'MC Agents process and buffer data locally. The platform remains operational even when individual sites lose connectivity.',
  },
  {
    icon: Lock,
    title: 'Tenant Isolation',
    description:
      'Multi-tenant deployments enforce strict data separation at the database level. No cross-tenant data leakage is architecturally possible.',
  },
  {
    icon: Database,
    title: 'Scalable Storage',
    description:
      'Time-series metrics, log data, and audit records are stored in purpose-built backends designed for high-throughput writes and fast queries.',
  },
  {
    icon: Cog,
    title: 'API-First Design',
    description:
      'Every platform capability is exposed through the REST API. If you can do it in the UI, you can automate it through the API.',
  },
]

const components = [
  {
    title: 'MC Agent',
    items: [
      'Linux, Windows, macOS, FreeBSD support',
      'OS-level metrics (CPU, memory, disk, network)',
      'Service discovery and process monitoring',
      'Remote shell execution and file transfer',
      'Package management and configuration drift detection',
      'Local telemetry buffering with store-and-forward',
    ],
  },
  {
    title: 'Plugin Framework',
    items: [
      'REST API integrations for cloud providers',
      'SNMP polling for network infrastructure',
      'WMI/WinRM for Windows environments',
      'SSH-based Linux/Unix monitoring',
      'Custom protocol adapters via plugin SDK',
      'Community plugin marketplace',
    ],
  },
  {
    title: 'AI Operations Engine',
    items: [
      'Anomaly detection across all metric streams',
      'Root cause correlation across dependencies',
      'Predictive failure analysis with trend modeling',
      'Natural language query for operational data',
      'Automated runbook generation from incident history',
      'Continuous learning from operator feedback',
    ],
  },
  {
    title: 'Automation Engine',
    items:
      [
        'YAML-based playbook definitions',
        'Event-driven and schedule-driven triggers',
        'Role-based execution with approval gates',
        'Rollback and idempotency guarantees',
        'Integration with Ansible, Terraform, and Puppet',
        'Audit trail for every automated action',
      ],
  },
]

export default function ArchitecturePage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Architecture' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h1 className="section-title mb-6">
              Platform{' '}
              <span className="gradient-text">Architecture</span>
            </h1>
            <p className="section-subtitle">
              Mission Control is built on a layered architecture that separates
              concerns while enabling deep integration across every component.
              Understanding the architecture helps you design deployments that
              match your operational requirements.
            </p>
          </div>
        </div>
      </section>

      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <h2 className="text-2xl font-bold text-center mb-12">
            Data Flow Architecture
          </h2>
          <p className="text-center text-surface-500 dark:text-surface-400 mb-12 max-w-2xl mx-auto">
            Data flows through Mission Control in a clear, directional pipeline
            — from user interactions at the top, through the platform core,
            down to agents and infrastructure, then back up through AI analysis,
            automation execution, and reporting output.
          </p>

          <div className="max-w-4xl mx-auto mb-16">
            {layers.map((layer, index) => {
              const Icon = layer.icon
              return (
                <div key={layer.title}>
                  <div className="glass rounded-xl p-6 flex items-center gap-6 card-hover">
                    <div
                      className={`w-14 h-14 rounded-xl ${layer.lightColor} flex items-center justify-center flex-shrink-0`}
                    >
                      <Icon className={`w-7 h-7 ${layer.textColor}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="font-semibold text-lg">
                          {layer.title}
                        </h3>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400">
                          Layer {index + 1}
                        </span>
                      </div>
                      <p className="text-sm text-surface-500 dark:text-surface-400">
                        {layer.description}
                      </p>
                    </div>
                  </div>
                  {index < layers.length - 1 && (
                    <div className="flex justify-center py-2">
                      <div className="w-px h-8 bg-gradient-to-b from-surface-300 to-surface-200 dark:from-surface-600 dark:to-surface-700" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <div className="glass rounded-xl p-8 max-w-3xl mx-auto">
            <h3 className="text-lg font-bold mb-4 text-center">
              Cross-Cutting Concerns
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                <Lock className="w-5 h-5 text-mc-600 dark:text-mc-400 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium">Authentication</div>
                  <div className="text-xs text-surface-500 dark:text-surface-400">
                    SSO, SAML, OIDC, API Keys
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                <Shield className="w-5 h-5 text-mc-600 dark:text-mc-400 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium">Encryption</div>
                  <div className="text-xs text-surface-500 dark:text-surface-400">
                    TLS 1.3 in transit, AES-256 at rest
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                <BarChart3 className="w-5 h-5 text-mc-600 dark:text-mc-400 flex-shrink-0" />
                <div>
                  <div className="text-sm font-medium">Audit Logging</div>
                  <div className="text-xs text-surface-500 dark:text-surface-400">
                    Tamper-evident, cryptographic
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container-wide">
          <h2 className="text-2xl font-bold mb-8 text-center">
            Core Components
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {components.map((component) => (
              <div key={component.title} className="glass rounded-xl p-6">
                <h3 className="font-semibold text-lg mb-4">
                  {component.title}
                </h3>
                <ul className="space-y-2">
                  {component.items.map((item, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-surface-600 dark:text-surface-300"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-mc-500 mt-2 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <h2 className="text-2xl font-bold mb-8 text-center">
            Architecture Principles
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {principles.map((principle) => {
              const Icon = principle.icon
              return (
                <div
                  key={principle.title}
                  className="glass rounded-xl p-6 card-hover"
                >
                  <Icon className="w-8 h-8 text-mc-600 dark:text-mc-400 mb-4" />
                  <h3 className="font-semibold mb-2">{principle.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">
                    {principle.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container-wide text-center">
          <h2 className="section-title mb-4">
            See the Architecture in Action
          </h2>
          <p className="section-subtitle mb-8">
            Deploy Mission Control in your environment and explore the full
            platform architecture with a hands-on evaluation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/downloads" className="btn-primary">
              Download and Deploy
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/documentation" className="btn-outline">
              Read the Documentation
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
