import { Metadata } from 'next'
import Link from 'next/link'
import {
  LayoutDashboard, Server, Activity, Gauge, Monitor, Container,
  Box, Users, Cloud, MonitorSmartphone, Zap, BookOpen, Radio,
  Brain, Puzzle, Building2, Globe, FileText, Shield, Code, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { features } from '@/data/features'

export const metadata: Metadata = generateMetadata({
  title: 'Features',
  description:
    'Explore the full capabilities of Mission Control — the unified IT operations platform combining monitoring, infrastructure management, automation, AI-assisted operations, and more.',
  canonical: '/features',
})

const iconMap: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard className="w-6 h-6" />,
  Server: <Server className="w-6 h-6" />,
  Activity: <Activity className="w-6 h-6" />,
  Gauge: <Gauge className="w-6 h-6" />,
  Monitor: <Monitor className="w-6 h-6" />,
  Container: <Container className="w-6 h-6" />,
  Box: <Box className="w-6 h-6" />,
  Users: <Users className="w-6 h-6" />,
  Cloud: <Cloud className="w-6 h-6" />,
  MonitorSmartphone: <MonitorSmartphone className="w-6 h-6" />,
  Zap: <Zap className="w-6 h-6" />,
  BookOpen: <BookOpen className="w-6 h-6" />,
  Radio: <Radio className="w-6 h-6" />,
  Brain: <Brain className="w-6 h-6" />,
  Puzzle: <Puzzle className="w-6 h-6" />,
  Building2: <Building2 className="w-6 h-6" />,
  Globe: <Globe className="w-6 h-6" />,
  FileText: <FileText className="w-6 h-6" />,
  Shield: <Shield className="w-6 h-6" />,
  Code: <Code className="w-6 h-6" />,
}

export default function FeaturesPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Features' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <h1 className="section-title mb-6">
              Everything You Need to <span className="gradient-text">Run Your Infrastructure</span>
            </h1>
            <p className="section-subtitle text-left mx-0">
              Mission Control brings monitoring, infrastructure management, automation, and
              AI-assisted operations together in a single platform — eliminating tool sprawl
              and giving your team complete visibility.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <Link
                key={feature.href}
                href={feature.href}
                className="glass rounded-xl p-6 card-hover group"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-lg bg-mc-500/10 text-mc-600 dark:text-mc-400 group-hover:bg-mc-500/20 transition-colors">
                    {iconMap[feature.icon]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h2 className="text-lg font-semibold mb-2 flex items-center gap-2">
                      {feature.title}
                      <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                    </h2>
                    <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-20 text-center glass rounded-2xl p-10">
            <h2 className="text-2xl font-bold mb-4">Ready to See Mission Control in Action?</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control in your environment and experience the benefits of a unified
              operational workspace. Get started in minutes with our quick-start guide.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started Free
              </Link>
              <Link href="/documentation" className="btn-outline">
                Read the Docs
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
