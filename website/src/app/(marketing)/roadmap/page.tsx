import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { roadmapItems } from '@/data/content'
import { CheckCircle, Clock, ArrowRight, Lightbulb, Rocket } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Roadmap',
  description: 'See what we are building next for Mission Control. View completed milestones, current sprint items, upcoming features, and our long-term product vision.',
  canonical: '/roadmap',
})

const statusConfig = {
  completed: {
    label: 'Completed',
    color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    border: 'border-green-200 dark:border-green-800',
    dot: 'bg-green-500',
  },
  'in-progress': {
    label: 'In Progress',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
    dot: 'bg-blue-500',
  },
  upcoming: {
    label: 'Upcoming',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800',
    dot: 'bg-amber-500',
  },
  future: {
    label: 'Future Vision',
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
    border: 'border-slate-200 dark:border-slate-700',
    dot: 'bg-slate-400',
  },
}

const completedItems = [
  { quarter: 'Q1 2025', title: 'Mission Control Core Platform', description: 'Foundation architecture with unified dashboard, agent framework, and REST API.', status: 'completed' as const },
  { quarter: 'Q2 2025', title: 'Linux & Windows Agent', description: 'Full agent support for Linux (deb/rpm) and Windows (MSI) with WMI integration.', status: 'completed' as const },
  { quarter: 'Q3 2025', title: 'Docker & Kubernetes Integration', description: 'Container monitoring, orchestration visibility, and Kubernetes cluster management.', status: 'completed' as const },
  { quarter: 'Q4 2025', title: 'Multi-Site Management', description: 'Manage infrastructure across multiple geographic locations with unified alerting.', status: 'completed' as const },
  { quarter: 'Q1 2026', title: 'Playbook Automation Engine', description: 'Visual playbook editor with 200+ built-in actions and scheduled task execution.', status: 'completed' as const },
  { quarter: 'Q2 2026', title: 'Plugin Framework v1', description: 'First-party and community plugin architecture with sandboxed execution.', status: 'completed' as const },
]

const allItems = [...completedItems, ...roadmapItems]

export default function RoadmapPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Roadmap' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Product Roadmap</span>
            </h1>
            <p className="section-subtitle">
              Our vision for the future of enterprise IT operations. We are committed to building the most capable and reliable platform for managing your infrastructure.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {Object.entries(statusConfig).map(([key, config]) => (
              <div key={key} className="flex items-center gap-2 text-sm">
                <span className={`w-2.5 h-2.5 rounded-full ${config.dot}`} />
                <span className="text-surface-600 dark:text-surface-300">{config.label}</span>
              </div>
            ))}
          </div>

          <div className="relative">
            <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-px bg-surface-200 dark:bg-surface-800" />

            <div className="space-y-8">
              {allItems.map((item, index) => {
                const config = statusConfig[item.status]
                const isLeft = index % 2 === 0

                return (
                  <div key={item.title} className={`relative flex flex-col md:flex-row ${isLeft ? 'md:flex-row' : 'md:flex-row-reverse'}`}>
                    <div className="hidden md:block md:w-1/2" />

                    <div className="absolute left-4 md:left-1/2 -translate-x-1/2 w-3 h-3 rounded-full border-2 border-white dark:border-surface-950 z-10"
                         style={{ top: '1.5rem' }}>
                      <span className={`block w-full h-full rounded-full ${config.dot}`} />
                    </div>

                    <div className={`ml-10 md:ml-0 md:w-1/2 ${isLeft ? 'md:pl-12' : 'md:pr-12'}`}>
                      <div className={`glass rounded-xl p-6 card-hover border ${config.border}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${config.color}`}>
                            {config.label}
                          </span>
                          <span className="text-xs text-surface-500 dark:text-surface-400">
                            {item.quarter}
                          </span>
                        </div>
                        <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                        <p className="text-surface-500 dark:text-surface-400 text-sm">
                          {item.description}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="mt-20 grid md:grid-cols-3 gap-6">
            <div className="glass rounded-xl p-6 text-center">
              <Rocket className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Rapid Delivery</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                We ship major features every quarter with minor releases and patches on a bi-weekly cadence.
              </p>
            </div>
            <div className="glass rounded-xl p-6 text-center">
              <Lightbulb className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Community Driven</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Feature priorities are influenced by customer feedback, community votes, and industry trends.
              </p>
            </div>
            <div className="glass rounded-xl p-6 text-center">
              <CheckCircle className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Transparent Process</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Every item is tracked in public issue trackers so you can follow development progress in real time.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
