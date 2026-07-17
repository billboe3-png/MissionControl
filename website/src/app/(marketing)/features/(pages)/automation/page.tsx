import { Metadata } from 'next'
import Link from 'next/link'
import {
  Zap, GitBranch, Clock, BarChart3,
  Puzzle, Shield, RefreshCw, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Automation Engine',
  description:
    'Event-driven automation engine with visual workflow builder, scheduling, and cross-system orchestration.',
  canonical: '/features/automation',
})

const capabilities = [
  {
    icon: <Zap className="w-5 h-5" />,
    title: 'Event-Driven Triggers',
    description:
      'Initiate automation workflows from monitoring alerts, infrastructure changes, scheduled timers, API webhooks, or manual triggers with conditional branching logic.',
  },
  {
    icon: <GitBranch className="w-5 h-5" />,
    title: 'Visual Workflow Builder',
    description:
      'Design complex automation workflows visually with drag-and-drop steps, conditional logic, loops, error handling, and human approval gates — no scripting required.',
  },
  {
    icon: <Clock className="w-5 h-5" />,
    title: 'Scheduling & Cron',
    description:
      'Schedule recurring tasks with cron expressions, calendar-based triggers, or maintenance window awareness — with timezone support for global operations.',
  },
  {
    icon: <Puzzle className="w-5 h-5" />,
    title: 'Cross-System Orchestration',
    description:
      'Coordinate actions across multiple systems in a single workflow — restart a service on Server A, update a DNS record, notify via Slack, and create a ticket.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Approval Workflows',
    description:
      'Require human approval before executing sensitive operations with role-based approval routing, SLA timers, and automatic escalation for overdue approvals.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Execution Analytics',
    description:
      'Track workflow execution history, success rates, duration trends, and failure patterns to identify optimization opportunities and measure operational efficiency.',
  },
]

export default function AutomationPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Automation' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Zap className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Automation</span> Engine
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control includes a powerful, event-driven automation engine that eliminates
              repetitive manual tasks and accelerates incident response. Build workflows that
              respond to monitoring alerts, enforce operational policies, orchestrate multi-system
              changes, and automate routine maintenance — all from a visual builder that requires
              no scripting expertise.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The automation engine integrates with every module in Mission Control, so workflows
              can trigger on infrastructure changes, monitoring events, credential rotations,
              scheduled timers, or external API calls. Each workflow execution is logged with
              full audit trails, and approval gates ensure that sensitive operations receive
              human oversight before execution.
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
            <h2 className="text-2xl font-bold mb-4">From Scripts to Systems</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Most operations teams start automation with ad-hoc scripts that work until the
              author leaves the team. Mission Control replaces that fragility with a centralized,
              version-controlled automation platform where workflows are documented, testable,
              and maintainable by anyone on the team. The visual builder makes it easy to see
              exactly what a workflow does, where it can fail, and how errors are handled.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Common use cases include automatic restart of failed services, disk cleanup when
              storage thresholds are breached, offboarding users across AD and Microsoft 365,
              certificate renewal, and infrastructure provisioning from templates. Each workflow
              can include conditional logic, error handling, and notification steps — ensuring
              that automated actions are reliable, auditable, and reversible.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Automate the Repetitive, Focus on the Critical</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Build reliable, auditable automation workflows in minutes with Mission
              Control&apos;s visual builder — no scripting required.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/playbooks" className="btn-outline">
                Explore Playbooks
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
