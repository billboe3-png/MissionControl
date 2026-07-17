import { Metadata } from 'next'
import Link from 'next/link'
import {
  Brain, TrendingUp, AlertTriangle, Lightbulb,
  BarChart3, Shield, RefreshCw, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'AI Operations',
  description:
    'AI-assisted incident analysis, root cause recommendation, anomaly prediction, and automated remediation suggestions.',
  canonical: '/features/ai-operations',
})

const capabilities = [
  {
    icon: <Brain className="w-5 h-5" />,
    title: 'Incident Analysis',
    description:
      'AI analyzes incident context including related alerts, recent changes, and historical patterns to identify the most probable root cause in seconds.',
  },
  {
    icon: <TrendingUp className="w-5 h-5" />,
    title: 'Anomaly Prediction',
    description:
      'Machine learning models trained on your environment detect deviations from normal behavior and predict potential issues before they impact services.',
  },
  {
    icon: <Lightbulb className="w-5 h-5" />,
    title: 'Remediation Suggestions',
    description:
      'Receive actionable remediation recommendations based on the incident type, affected systems, and your organization&apos;s documented procedures and playbooks.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Pattern Recognition',
    description:
      'Identify recurring incidents, correlated events, and systemic issues across your infrastructure that human analysis would miss in complex environments.',
  },
  {
    icon: <AlertTriangle className="w-5 h-5" />,
    title: 'Noise Reduction',
    description:
      'AI-driven alert correlation and deduplication separates meaningful signals from noise, reducing alert fatigue and focusing your team on what matters.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Continuous Learning',
    description:
      'The AI models improve over time as they learn from your team&apos;s resolution patterns, custom playbooks, and environment-specific behaviors.',
  },
]

export default function AIOperationsPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'AI Operations' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Brain className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">AI Operations</span>
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control integrates AI-assisted analysis directly into your operational
              workflow, helping your team resolve incidents faster by providing instant root
              cause analysis, anomaly detection, and remediation recommendations. The AI operates
              on the rich context that Mission Control collects — infrastructure topology,
              monitoring data, configuration changes, and historical incident patterns.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Unlike generic AI tools that lack operational context, Mission Control&apos;s AI
              understands your specific environment. It knows which services depend on which
              servers, what changes were made recently, and how similar incidents were resolved
              in the past. This contextual intelligence enables recommendations that are
              actionable and relevant — not generic suggestions that require significant
              adaptation.
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
            <h2 className="text-2xl font-bold mb-4">AI That Understands Your Infrastructure</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Most AI operations tools offer generic recommendations based on public knowledge
              bases. Mission Control&apos;s AI is different — it analyzes your specific
              environment, including your infrastructure topology, recent changes, historical
              incident patterns, and the playbooks your team has built. This means
              recommendations reference your actual systems, your actual procedures, and your
              actual resolution history.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              The anomaly detection engine establishes baselines for every monitored metric in
              your environment and continuously compares current values against expected
              behavior. When it detects a deviation — even a subtle one — it surfaces the
              anomaly with contextual information about what changed, what might have caused it,
              and what the historical pattern suggests will happen if the trend continues.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Resolve Incidents Faster with AI</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Mission Control&apos;s AI operations analyzes your environment in context to
              provide actionable root cause analysis and remediation recommendations.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/monitoring" className="btn-outline">
                Explore Monitoring
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
