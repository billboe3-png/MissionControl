import { Metadata } from 'next'
import Link from 'next/link'
import {
  Activity, Bell, AlertTriangle, TrendingUp,
  Clock, CheckCircle, Zap, Settings, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Monitoring',
  description:
    'Real-time monitoring with intelligent alerting, anomaly detection, and automated incident response across all systems.',
  canonical: '/features/monitoring',
})

const capabilities = [
  {
    icon: <Activity className="w-5 h-5" />,
    title: 'Multi-Protocol Collection',
    description:
      'Monitor systems using SNMP, WMI, SSH, agent-based, and agentless methods simultaneously — adapting to whatever protocol each device supports natively.',
  },
  {
    icon: <AlertTriangle className="w-5 h-5" />,
    title: 'Intelligent Alerting',
    description:
      'Configure thresholds, escalation chains, and notification channels per alert type. Alerts are deduplicated and correlated so your team receives actionable signals, not noise.',
  },
  {
    icon: <TrendingUp className="w-5 h-5" />,
    title: 'Anomaly Detection',
    description:
      'Machine-learning baseline analysis identifies unusual patterns in CPU, memory, disk, and network usage before they become incidents — flagging drift that static thresholds miss.',
  },
  {
    icon: <Clock className="w-5 h-5" />,
    title: 'Uptime Tracking',
    description:
      'Track service availability with SLA monitoring, maintenance window scheduling, and detailed uptime reports that satisfy compliance and audit requirements.',
  },
  {
    icon: <Bell className="w-5 h-5" />,
    title: 'Multi-Channel Notifications',
    description:
      'Route alerts via email, SMS, Slack, Microsoft Teams, PagerDuty, or webhooks — with per-contact schedules and escalation policies.',
  },
  {
    icon: <Zap className="w-5 h-5" />,
    title: 'Automated Response',
    description:
      'Trigger automated remediation workflows directly from alerts — restarting services, clearing queues, or creating tickets without human intervention.',
  },
]

export default function MonitoringPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Monitoring' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Activity className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                Real-Time <span className="gradient-text">Monitoring</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides continuous, real-time monitoring across every layer of
              your infrastructure — from hardware sensors and network interfaces to application
              endpoints and user-facing services. Data is collected at configurable intervals,
              processed through a rules engine, and presented in dashboards and alerts that
              keep your operations team informed and focused.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Unlike standalone monitoring tools that require separate correlation, Mission
              Control integrates monitoring data with your full infrastructure context. When an
              alert fires, your team immediately sees the affected asset, its dependencies, its
              recent change history, and any related playbooks — dramatically reducing mean
              time to resolution.
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
            <h2 className="text-2xl font-bold mb-4">From Metrics to Action in Seconds</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Most monitoring tools stop at alerting. Mission Control takes the next step by
              connecting every alert to context — the asset owner, the last configuration change,
              related incidents, and recommended playbooks. This contextual awareness means your
              on-call engineers spend less time gathering information and more time resolving
              issues.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The monitoring engine supports custom metric collection through scripts, APIs, and
              log parsing, so you can track business-specific KPIs alongside infrastructure
              health. Thresholds can be configured as static values, percentage-based, or
              dynamically derived from historical baselines — ensuring alerts adapt to the
              natural rhythm of your environment.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Never Miss a Critical Event</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Mission Control monitors every system in real time and routes alerts to the right
              people through the right channels — before problems become outages.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Start Monitoring
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/zabbix" className="btn-outline">
                Zabbix Integration
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
