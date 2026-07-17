import Link from 'next/link'
import {
  Server, Shield, Zap, Globe, Users, Box, Cloud, Monitor, Gauge,
  Container, Brain, Puzzle, Building2, FileText, Code, BookOpen,
  Radio, MonitorSmartphone, LayoutDashboard, ChevronRight, ArrowRight,
  Download, Github, Activity, BarChart3, Layers, Network, Terminal,
  Lock, RefreshCw, AlertTriangle, TrendingUp, Cpu, HardDrive, Wifi,
  Sliders, Grid, Map, PieChart, Eye, Search, Bell, Settings,
  ExternalLink, Star, Clock, Check,
} from 'lucide-react'
import { siteConfig } from '@/lib/site'
import { features } from '@/data/features'
import { pricingPlans, supportedPlatforms, blogPosts, roadmapItems } from '@/data/content'
import { Hero } from '@/components/marketing/Hero'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { FeatureCard } from '@/components/ui/FeatureCard'
import { PricingCard } from '@/components/ui/PricingCard'
import { StatsSection } from '@/components/ui/StatsSection'
import { CTA } from '@/components/ui/CTA'
import { TechnologyGrid } from '@/components/ui/TechnologyGrid'

import type { LucideIcon } from 'lucide-react'

const featureIconMap: Record<string, LucideIcon> = {
  LayoutDashboard, Server, Activity, Gauge, Monitor, Container, Users,
  Cloud, MonitorSmartphone, Zap, BookOpen, Radio, Brain, Puzzle,
  Building2, Globe, FileText, Shield, Code,
}

const integrations = [
  { name: 'Zabbix', description: 'Unified metrics, events, and topology with automated remediation.', icon: Gauge },
  { name: 'Prometheus', description: 'Scrape and query Prometheus metrics with native dashboard integration.', icon: Activity },
  { name: 'Grafana', description: 'Embed Grafana dashboards and share alerting rules across platforms.', icon: BarChart3 },
  { name: 'Ansible', description: 'Trigger playbooks, manage inventories, and track execution results.', icon: Terminal },
  { name: 'Terraform', description: 'Import state, visualize infrastructure drift, and manage drift detection.', icon: Layers },
  { name: 'VMware vSphere', description: 'Full lifecycle management for VMware hosts, VMs, and clusters.', icon: Server },
]

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <Hero />

      {/* Stats */}
      <StatsSection />

      {/* Trusted Technologies */}
      <TechnologyGrid />

      {/* Feature Highlights */}
      <section className="section">
        <div className="container-wide">
          <SectionHeader
            title="Everything You Need to Operate at Scale"
            subtitle="From real-time monitoring to AI-assisted incident response, Mission Control gives your operations team the tools to manage complex infrastructure with confidence."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.slice(0, 9).map((feature) => {
              const Icon = featureIconMap[feature.icon] || Server
              return (
                <FeatureCard
                  key={feature.href}
                  icon={Icon}
                  title={feature.title}
                  description={feature.description}
                  href={feature.href}
                />
              )
            })}
          </div>
          <div className="text-center mt-12">
            <Link href="/features" className="btn-outline">
              View All Features
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <SectionHeader
            title="A Unified Command Center"
            subtitle="Your entire infrastructure at a glance. Customizable dashboards, real-time metrics, and intelligent alerting — all in one pane of glass."
          />
          <div className="relative rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl shadow-mc-500/10 overflow-hidden bg-white dark:bg-surface-900">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-surface-50 dark:bg-surface-800">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <span className="text-xs text-surface-400 flex-1 text-center">Mission Control Dashboard</span>
            </div>
            <div className="aspect-[16/9] bg-gradient-to-br from-surface-50 to-surface-100 dark:from-surface-900 dark:to-surface-800 p-6 sm:p-8">
              <div className="grid grid-cols-4 gap-4 h-full">
                {/* Sidebar */}
                <div className="col-span-1 rounded-xl bg-white dark:bg-surface-700 p-4 shadow-sm border border-gray-100 dark:border-gray-700 hidden md:block">
                  <div className="space-y-3">
                    {['Dashboard', 'Infrastructure', 'Monitoring', 'Automation', 'Settings'].map((item, i) => (
                      <div
                        key={item}
                        className={`px-3 py-2 rounded-lg text-sm ${
                          i === 0
                            ? 'bg-mc-50 dark:bg-mc-950/50 text-mc-700 dark:text-mc-300 font-medium'
                            : 'text-surface-500'
                        }`}
                      >
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
                {/* Main content */}
                <div className="col-span-4 md:col-span-3 space-y-4">
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { label: 'Total Nodes', value: '1,247', change: '+12', color: 'text-mc-600' },
                      { label: 'Active Alerts', value: '3', change: '-5', color: 'text-green-600' },
                      { label: 'Uptime', value: '99.99%', change: '+0.01%', color: 'text-green-600' },
                      { label: 'Automations', value: '24', change: '+2', color: 'text-mc-600' },
                    ].map((stat) => (
                      <div key={stat.label} className="rounded-xl bg-white dark:bg-surface-700 p-3 shadow-sm border border-gray-100 dark:border-gray-700">
                        <div className="text-xs text-surface-500">{stat.label}</div>
                        <div className={`text-xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
                        <div className="text-xs text-surface-400 mt-0.5">{stat.change}</div>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-xl bg-white dark:bg-surface-700 p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                      <div className="text-sm font-semibold mb-3">Resource Utilization</div>
                      <div className="space-y-2">
                        {[
                          { label: 'CPU', value: 67, color: 'bg-mc-500' },
                          { label: 'Memory', value: 82, color: 'bg-orange-500' },
                          { label: 'Disk', value: 45, color: 'bg-green-500' },
                          { label: 'Network', value: 23, color: 'bg-blue-500' },
                        ].map((item) => (
                          <div key={item.label} className="flex items-center gap-2">
                            <span className="text-xs text-surface-500 w-14">{item.label}</span>
                            <div className="flex-1 h-2 bg-surface-100 dark:bg-surface-600 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                            </div>
                            <span className="text-xs text-surface-400 w-8 text-right">{item.value}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl bg-white dark:bg-surface-700 p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                      <div className="text-sm font-semibold mb-3">Recent Activity</div>
                      <div className="space-y-2">
                        {[
                          { text: 'Server web-prod-03 recovered', time: '2m ago', color: 'text-green-500' },
                          { text: 'New alert: CPU threshold', time: '5m ago', color: 'text-orange-500' },
                          { text: 'Playbook "Deploy" completed', time: '12m ago', color: 'text-mc-500' },
                          { text: 'Agent updated on 24 nodes', time: '1h ago', color: 'text-surface-400' },
                        ].map((item) => (
                          <div key={item.text} className="flex items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${item.color.replace('text-', 'bg-')}`} />
                            <span className="text-xs text-surface-600 dark:text-surface-300 flex-1">{item.text}</span>
                            <span className="text-xs text-surface-400">{item.time}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="section">
        <div className="container-wide">
          <SectionHeader
            title="Enterprise-Grade Architecture"
            subtitle="Built from the ground up for reliability, scalability, and security. Mission Control handles the complexity of modern hybrid infrastructure."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Layers,
                title: 'Modular Design',
                description: 'Each capability — monitoring, automation, AI — operates as an independent module that can be enabled, scaled, or replaced without affecting the rest of the platform.',
              },
              {
                icon: Shield,
                title: 'Security First',
                description: 'End-to-end encryption, role-based access control, credential vaulting, audit logging, and compliance reporting built into every layer of the platform.',
              },
              {
                icon: Globe,
                title: 'Multi-Site Ready',
                description: 'Centralized management for geographically distributed sites with WAN-aware operations, local caching, and automatic failover for offline resilience.',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="p-8 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover"
              >
                <div className="w-14 h-14 rounded-xl bg-mc-50 dark:bg-mc-500/10 flex items-center justify-center mb-5">
                  <item.icon className="w-7 h-7 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Link href="/architecture" className="btn-outline">
              Explore Architecture
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Supported Platforms */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <SectionHeader
            title="Supported Platforms"
            subtitle="Deploy Mission Control across your entire hybrid environment — from bare metal to cloud-native containers."
          />
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {supportedPlatforms.map((platform) => (
              <div
                key={platform.name}
                className="flex flex-col items-center p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover text-center"
              >
                <span className="text-sm font-medium">{platform.name}</span>
                <span className="text-xs text-surface-400 mt-1">{platform.category}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported Integrations */}
      <section className="section">
        <div className="container-wide">
          <SectionHeader
            title="Integrations That Matter"
            subtitle="Connect with the tools your team relies on every day. Mission Control integrates with industry-standard platforms out of the box."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {integrations.map((integration) => (
              <div
                key={integration.name}
                className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-mc-50 dark:bg-mc-500/10 flex items-center justify-center">
                    <integration.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                  </div>
                  <h3 className="font-semibold">{integration.name}</h3>
                </div>
                <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
                  {integration.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Operations */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-mc-50 dark:bg-mc-950/50 text-mc-700 dark:text-mc-300 text-sm font-medium mb-6">
                <Brain className="w-4 h-4" />
                AI-Powered Operations
              </div>
              <h2 className="section-title text-left mb-6">
                Smarter Operations with{' '}
                <span className="gradient-text">AI Assistance</span>
              </h2>
              <p className="text-lg text-surface-500 dark:text-surface-400 mb-8 leading-relaxed">
                Mission Control leverages machine learning to analyze patterns across your infrastructure,
                predict incidents before they occur, and recommend remediation steps based on historical data
                and industry best practices.
              </p>
              <ul className="space-y-4 mb-8">
                {[
                  { icon: TrendingUp, text: 'Predictive alerting reduces mean time to detection by 60%' },
                  { icon: Search, text: 'Automated root cause analysis across correlated events' },
                  { icon: Bell, text: 'Intelligent noise reduction filters false-positive alerts' },
                  { icon: RefreshCw, text: 'Self-learning models improve accuracy over time' },
                ].map((item) => (
                  <li key={item.text} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-md bg-mc-100 dark:bg-mc-900/50 flex items-center justify-center shrink-0 mt-0.5">
                      <item.icon className="w-4 h-4 text-mc-600 dark:text-mc-400" />
                    </div>
                    <span className="text-surface-600 dark:text-surface-300">{item.text}</span>
                  </li>
                ))}
              </ul>
              <Link href="/features/ai-operations" className="btn-primary">
                Explore AI Operations
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="relative">
              <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 p-6 shadow-xl shadow-mc-500/5">
                <div className="flex items-center gap-2 mb-4">
                  <Brain className="w-5 h-5 text-mc-500" />
                  <span className="font-semibold text-sm">AI Incident Analysis</span>
                </div>
                <div className="space-y-3">
                  {[
                    { severity: 'critical', label: 'Critical', message: 'Database cluster failover detected — auto-remediation initiated', time: '12s ago' },
                    { severity: 'warning', label: 'Warning', message: 'Memory utilization trending upward on web-prod-01 through web-prod-05', time: '3m ago' },
                    { severity: 'info', label: 'Info', message: 'Predictive model: 87% probability of disk capacity alert within 72h', time: '15m ago' },
                  ].map((alert, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg border ${
                        alert.severity === 'critical'
                          ? 'border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20'
                          : alert.severity === 'warning'
                          ? 'border-yellow-200 dark:border-yellow-900/50 bg-yellow-50 dark:bg-yellow-950/20'
                          : 'border-blue-200 dark:border-blue-900/50 bg-blue-50 dark:bg-blue-950/20'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-semibold ${
                          alert.severity === 'critical'
                            ? 'text-red-600 dark:text-red-400'
                            : alert.severity === 'warning'
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-blue-600 dark:text-blue-400'
                        }`}>{alert.label}</span>
                        <span className="text-xs text-surface-400">{alert.time}</span>
                      </div>
                      <p className="text-sm text-surface-600 dark:text-surface-300">{alert.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mission Control Agent */}
      <section className="section">
        <div className="container-wide">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 p-6 shadow-xl shadow-mc-500/5">
                <div className="flex items-center gap-2 mb-4">
                  <Radio className="w-5 h-5 text-mc-500" />
                  <span className="font-semibold text-sm">Agent Fleet Status</span>
                </div>
                <div className="space-y-3">
                  {[
                    { name: 'mc-agent-prod-east', status: 'online', version: '3.0.1', uptime: '45d 12h' },
                    { name: 'mc-agent-prod-west', status: 'online', version: '3.0.1', uptime: '45d 12h' },
                    { name: 'mc-agent-staging', status: 'online', version: '3.0.1', uptime: '12d 6h' },
                    { name: 'mc-agent-dr-site', status: 'standby', version: '3.0.0', uptime: '30d 8h' },
                  ].map((agent) => (
                    <div
                      key={agent.name}
                      className="flex items-center justify-between p-3 rounded-lg bg-surface-50 dark:bg-surface-800"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${agent.status === 'online' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                        <div>
                          <div className="text-sm font-medium font-mono">{agent.name}</div>
                          <div className="text-xs text-surface-400">v{agent.version}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-surface-400">Uptime</div>
                        <div className="text-sm font-medium">{agent.uptime}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-mc-50 dark:bg-mc-950/50 text-mc-700 dark:text-mc-300 text-sm font-medium mb-6">
                <Radio className="w-4 h-4" />
                Mission Control Agent
              </div>
              <h2 className="section-title text-left mb-6">
                Secure Connectivity,{' '}
                <span className="gradient-text">Anywhere</span>
              </h2>
              <p className="text-lg text-surface-500 dark:text-surface-400 mb-8 leading-relaxed">
                The Mission Control Agent establishes a secure, persistent connection from your infrastructure
                back to the platform. Deploy in firewalled, air-gapped, or remote environments with full local
                execution capabilities.
              </p>
              <ul className="space-y-4 mb-8">
                {[
                  { icon: Lock, text: 'Encrypted tunnel with certificate-based mutual authentication' },
                  { icon: Terminal, text: 'Local command execution without exposing SSH or RDP' },
                  { icon: HardDrive, text: 'Local cache for offline resilience and data buffering' },
                  { icon: Wifi, text: 'Operates over any network — including satellite and cellular' },
                ].map((item) => (
                  <li key={item.text} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-md bg-mc-100 dark:bg-mc-900/50 flex items-center justify-center shrink-0 mt-0.5">
                      <item.icon className="w-4 h-4 text-mc-600 dark:text-mc-400" />
                    </div>
                    <span className="text-surface-600 dark:text-surface-300">{item.text}</span>
                  </li>
                ))}
              </ul>
              <Link href="/features/mc-agent" className="btn-primary">
                Learn About the Agent
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Automation */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <SectionHeader
            title="Automate Everything"
            subtitle="Event-driven automation with visual workflows, scheduling, and cross-system orchestration. Reduce manual toil and respond to incidents in seconds."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Zap,
                title: 'Event-Driven',
                description: 'Trigger automations based on alerts, metric thresholds, log patterns, or API events.',
              },
              {
                icon: Settings,
                title: 'Visual Workflow Builder',
                description: 'Design complex automation flows with a drag-and-drop interface. No coding required.',
              },
              {
                icon: Clock,
                title: 'Scheduling',
                description: 'Schedule recurring tasks, maintenance windows, and batch operations across your fleet.',
              },
              {
                icon: Network,
                title: 'Cross-System Orchestration',
                description: 'Coordinate actions across multiple systems, sites, and platforms in a single workflow.',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover text-center"
              >
                <div className="w-12 h-12 rounded-xl bg-mc-50 dark:bg-mc-500/10 flex items-center justify-center mb-4 mx-auto">
                  <item.icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-12 text-center">
            <Link href="/features/automation" className="btn-outline">
              Explore Automation
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Plugin Marketplace */}
      <section className="section">
        <div className="container-wide">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-mc-50 dark:bg-mc-950/50 text-mc-700 dark:text-mc-300 text-sm font-medium mb-6">
                <Puzzle className="w-4 h-4" />
                Plugin Marketplace
              </div>
              <h2 className="section-title text-left mb-6">
                Extend Mission Control with{' '}
                <span className="gradient-text">Plugins</span>
              </h2>
              <p className="text-lg text-surface-500 dark:text-surface-400 mb-8 leading-relaxed">
                Build custom integrations with the Plugin SDK, or browse the marketplace for community-contributed
                plugins. Every plugin runs in a sandboxed environment with fine-grained permission controls.
              </p>
              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  { label: 'Official Plugins', value: '40+' },
                  { label: 'Community Plugins', value: '120+' },
                  { label: 'SDK Languages', value: 'TypeScript, Go, Python' },
                  { label: 'Sandbox Security', value: 'Isolated Execution' },
                ].map((item) => (
                  <div key={item.label} className="p-4 rounded-xl bg-surface-50 dark:bg-surface-800">
                    <div className="text-sm text-surface-500">{item.label}</div>
                    <div className="text-lg font-bold mt-1">{item.value}</div>
                  </div>
                ))}
              </div>
              <Link href="/features/plugin-framework" className="btn-primary">
                Explore Plugins
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 p-6 shadow-xl shadow-mc-500/5">
              <div className="flex items-center gap-2 mb-4">
                <Puzzle className="w-5 h-5 text-mc-500" />
                <span className="font-semibold text-sm">Plugin Marketplace</span>
              </div>
              <div className="space-y-3">
                {[
                  { name: 'AWS CloudWatch', author: 'Mission Control', rating: 4.9, installs: '12.4k', category: 'Cloud' },
                  { name: 'Azure Monitor', author: 'Mission Control', rating: 4.8, installs: '9.2k', category: 'Cloud' },
                  { name: 'CrowdStrike Falcon', author: 'SecurityTeam', rating: 4.7, installs: '5.1k', category: 'Security' },
                  { name: 'ServiceNow ITSM', author: 'IntegrationsCo', rating: 4.6, installs: '7.8k', category: 'ITSM' },
                  { name: 'Slack Notifications', author: 'Mission Control', rating: 4.9, installs: '21.3k', category: 'Notifications' },
                ].map((plugin) => (
                  <div
                    key={plugin.name}
                    className="flex items-center justify-between p-3 rounded-lg bg-surface-50 dark:bg-surface-800"
                  >
                    <div>
                      <div className="text-sm font-medium">{plugin.name}</div>
                      <div className="text-xs text-surface-400">{plugin.author}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-700 text-surface-500">
                        {plugin.category}
                      </span>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                        <span className="text-xs font-medium">{plugin.rating}</span>
                      </div>
                      <span className="text-xs text-surface-400">{plugin.installs}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <SectionHeader
            title="Product Roadmap"
            subtitle="We are building the future of IT operations. Here is what is coming next."
          />
          <div className="relative max-w-3xl mx-auto">
            <div className="absolute left-4 sm:left-1/2 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-800 -translate-x-1/2" />
            <div className="space-y-8">
              {roadmapItems.map((item, i) => (
                <div
                  key={item.quarter}
                  className={`relative flex flex-col sm:flex-row ${
                    i % 2 === 0 ? 'sm:flex-row' : 'sm:flex-row-reverse'
                  } gap-6`}
                >
                  <div className={`flex-1 ${i % 2 === 0 ? 'sm:text-right' : 'sm:text-left'}`}>
                    <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover inline-block text-left">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-semibold text-mc-600 dark:text-mc-400">
                          {item.quarter}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            item.status === 'in-progress'
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                              : item.status === 'upcoming'
                              ? 'bg-mc-100 dark:bg-mc-900/30 text-mc-700 dark:text-mc-400'
                              : 'bg-surface-100 dark:bg-surface-800 text-surface-500'
                          }`}
                        >
                          {item.status === 'in-progress' ? 'In Progress' : item.status === 'upcoming' ? 'Upcoming' : 'Future'}
                        </span>
                      </div>
                      <h3 className="font-semibold mb-1">{item.title}</h3>
                      <p className="text-sm text-surface-500 dark:text-surface-400">{item.description}</p>
                    </div>
                  </div>
                  <div className="absolute left-4 sm:left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-mc-500 border-4 border-white dark:border-surface-950 z-10" />
                  <div className="flex-1 hidden sm:block" />
                </div>
              ))}
            </div>
            <div className="text-center mt-12">
              <Link href="/roadmap" className="btn-outline">
                View Full Roadmap
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Latest Release */}
      <section className="section">
        <div className="container-wide">
          <SectionHeader
            title="Latest Release"
            subtitle="Mission Control 3.0 is here with AI-assisted operations, expanded plugin framework, and enterprise multi-tenancy."
          />
          <div className="max-w-3xl mx-auto">
            <div className="p-8 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover">
              <div className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 rounded-full bg-mc-100 dark:bg-mc-900/50 text-mc-700 dark:text-mc-300 text-sm font-semibold">
                  v3.0.0
                </span>
                <span className="text-sm text-surface-400">Released July 1, 2026</span>
              </div>
              <h3 className="text-xl font-bold mb-4">Mission Control 3.0</h3>
              <p className="text-surface-500 dark:text-surface-400 mb-6 leading-relaxed">
                The biggest release in Mission Control history introduces AI-assisted operations for predictive
                incident detection and automated root cause analysis. The expanded plugin framework now supports
                TypeScript, Go, and Python with a new marketplace for community-contributed integrations. Enterprise
                multi-tenancy provides isolated workspaces with custom branding and tenant-specific policies.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                {[
                  { icon: Brain, label: 'AI Operations Engine' },
                  { icon: Puzzle, label: 'Plugin Marketplace v2' },
                  { icon: Building2, label: 'Multi-Tenant Support' },
                  { icon: Lock, label: 'Zero-Trust Security' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2 p-2 rounded-lg bg-surface-50 dark:bg-surface-800">
                    <item.icon className="w-4 h-4 text-mc-500 shrink-0" />
                    <span className="text-xs font-medium">{item.label}</span>
                  </div>
                ))}
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link href="/release-notes" className="btn-primary">
                  <FileText className="w-4 h-4" />
                  Release Notes
                </Link>
                <Link href={siteConfig.links.download} className="btn-secondary">
                  <Download className="w-4 h-4" />
                  Download v3.0.0
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Latest Blog Posts */}
      <section className="section bg-surface-50 dark:bg-surface-900/50">
        <div className="container-wide">
          <SectionHeader
            title="From the Blog"
            subtitle="Insights, tutorials, and updates from the Mission Control team."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {blogPosts.map((post) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className="group block rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 overflow-hidden card-hover"
              >
                <div className="aspect-video bg-gradient-to-br from-mc-100 to-mc-200 dark:from-mc-900 dark:to-mc-800 flex items-center justify-center">
                  <FileText className="w-10 h-10 text-mc-400 dark:text-mc-500" />
                </div>
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    {post.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-500"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <h3 className="font-semibold text-sm mb-2 group-hover:text-mc-600 dark:group-hover:text-mc-400 transition-colors line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-xs text-surface-500 dark:text-surface-400 line-clamp-2 mb-3">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center justify-between text-xs text-surface-400">
                    <span>{post.author}</span>
                    <span>{new Date(post.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          <div className="text-center mt-12">
            <Link href="/blog" className="btn-outline">
              View All Posts
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="section">
        <div className="container-wide">
          <SectionHeader
            title="Simple, Transparent Pricing"
            subtitle="Start for free with the Community edition. Scale to Enterprise when you are ready."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {pricingPlans.map((plan) => (
              <PricingCard key={plan.name} {...plan} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTA />
    </>
  )
}
