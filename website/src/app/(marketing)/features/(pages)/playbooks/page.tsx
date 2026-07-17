import { Metadata } from 'next'
import Link from 'next/link'
import {
  BookOpen, GitBranch, Shield, Zap,
  Users, FileText, CheckCircle, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Playbooks',
  description:
    'Pre-built and custom playbooks for incident response, maintenance tasks, and operational procedures with version control.',
  canonical: '/features/playbooks',
})

const capabilities = [
  {
    icon: <BookOpen className="w-5 h-5" />,
    title: 'Pre-Built Templates',
    description:
      'Start with a library of battle-tested playbooks covering common scenarios: service restart, disk cleanup, certificate renewal, disaster recovery, and more.',
  },
  {
    icon: <GitBranch className="w-5 h-5" />,
    title: 'Version Control',
    description:
      'Track every change to a playbook with full version history, compare versions side-by-side, and roll back to any previous state with a single click.',
  },
  {
    icon: <Zap className="w-5 h-5" />,
    title: 'One-Click Execution',
    description:
      'Execute playbooks from the dashboard, from an alert context, or via API — with parameterized inputs, progress tracking, and real-time output streaming.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Approval Gates',
    description:
      'Require authorization before executing high-impact playbooks with configurable approval workflows, SLA timers, and automatic escalation.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'Team Collaboration',
    description:
      'Co-author playbooks with your team, comment on specific steps, assign ownership, and maintain a shared knowledge base of operational procedures.',
  },
  {
    icon: <CheckCircle className="w-5 h-5" />,
    title: 'Execution Auditing',
    description:
      'Review who executed which playbook, when, with what inputs, and what the outcome was — with complete execution logs and post-run reporting.',
  },
]

export default function PlaybooksPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Playbooks' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <BookOpen className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Playbooks</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control playbooks capture your team&apos;s operational knowledge in
              executable, version-controlled procedures. Instead of relying on tribal knowledge
              or wiki pages that quickly become outdated, playbooks provide step-by-step
              instructions that can be executed with one click, scheduled in advance, or
              triggered automatically by monitoring alerts.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Every playbook execution is logged with full audit trails, creating an institutional
              record of how incidents were resolved, maintenance was performed, and changes were
              executed. This documentation becomes invaluable for training new team members,
              satisfying compliance audits, and continuously improving your operational
              procedures.
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
            <h2 className="text-2xl font-bold mb-4">Institutional Knowledge, Codified</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              When a senior engineer leaves, they take critical operational knowledge with them.
              Playbooks prevent this brain drain by capturing procedures as executable workflows
              that anyone on the team can run with confidence. Each step is documented,
              parameterized, and tested — ensuring consistent execution regardless of who runs
              the playbook.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The playbook library includes templates for common scenarios across infrastructure,
              security, and compliance. Customize these templates for your environment, or
              author entirely new playbooks using the visual editor. Every change is versioned,
              and the comparison tool makes it easy to review modifications before they are
              promoted to production use.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Codify Your Operational Excellence</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Create, version, and execute operational playbooks that capture your team&apos;s
              expertise — with full audit trails and approval workflows.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/automation" className="btn-outline">
                Explore Automation
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
