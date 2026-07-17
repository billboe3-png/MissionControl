import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Target, Users, Globe, Heart, ArrowRight, CheckCircle } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'About',
  description: 'Learn about Mission Control, our mission, the team behind the platform, and our commitment to transforming IT operations for organizations worldwide.',
  canonical: '/about',
})

const values = [
  {
    icon: Target,
    title: 'Mission-Driven',
    description: 'We believe every IT operations team deserves a unified, intelligent platform that reduces toil and amplifies their impact.',
  },
  {
    icon: Users,
    title: 'Customer First',
    description: 'Every feature we build starts with a real customer problem. We obsess over reliability, performance, and user experience.',
  },
  {
    icon: Globe,
    title: 'Open Foundation',
    description: 'Mission Control is built on open standards and open-source foundations. We contribute back to the communities we depend on.',
  },
  {
    icon: Heart,
    title: 'Operational Excellence',
    description: 'We hold ourselves to the same standards we help our customers achieve. Our platform runs on itself.',
  },
]

const milestones = [
  { year: '2024', event: 'Mission Control founded with the vision of unifying IT operations.' },
  { year: '2024', event: 'Core platform architecture designed and first agent released as open source.' },
  { year: '2025', event: 'Platform reaches 1,000 deployments across 30 countries.' },
  { year: '2025', event: 'Linux and Windows agents released with full production support.' },
  { year: '2026', event: 'Mission Control 3.0 launches with AI operations and enterprise multi-tenancy.' },
  { year: '2026', event: 'Platform exceeds 50,000 monitored infrastructure nodes worldwide.' },
]

export default function AboutPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'About' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">About Mission Control</span>
            </h1>
            <p className="section-subtitle">
              We are building the unified IT operations platform that the industry deserves. Mission Control combines monitoring, management, automation, and AI into a single operational workspace.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 mb-20 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-6">Our Story</h2>
              <div className="space-y-4 text-surface-600 dark:text-surface-300">
                <p>
                  Mission Control was born from a simple observation: IT operations teams were drowning in tools. A typical enterprise might use a dozen or more disconnected platforms for monitoring, configuration management, remote access, automation, and reporting.
                </p>
                <p>
                  We set out to build a single platform that brings all of these capabilities together — not as a superficial integration layer, but as a deeply unified system where monitoring data flows directly into automation, where alerts trigger playbooks, and where AI assists operators in making faster, better decisions.
                </p>
                <p>
                  Today, Mission Control manages over 50,000 infrastructure nodes across 99 countries, serving enterprises, managed service providers, government agencies, and educational institutions.
                </p>
              </div>
            </div>
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-6">Key Milestones</h3>
              <div className="space-y-4">
                {milestones.map((milestone) => (
                  <div key={milestone.event} className="flex gap-4">
                    <span className="text-sm font-mono font-semibold text-mc-600 dark:text-mc-400 w-12 flex-shrink-0">
                      {milestone.year}
                    </span>
                    <span className="text-sm text-surface-600 dark:text-surface-300">{milestone.event}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mb-20">
            <h2 className="text-3xl font-bold text-center mb-10">Our Values</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {values.map((value) => (
                <div key={value.title} className="glass rounded-xl p-6 card-hover text-center">
                  <div className="w-12 h-12 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mx-auto mb-4">
                    <value.icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                  </div>
                  <h3 className="font-semibold mb-2">{value.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">{value.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-xl p-12 text-center">
            <h2 className="text-2xl font-bold mb-4">Join Us</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-xl mx-auto">
              We are always looking for talented engineers, designers, and operations professionals who share our passion for building exceptional IT operations tools.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/contact" className="btn-primary">
                Get in Touch
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/documentation" className="btn-secondary">
                Read the Docs
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
