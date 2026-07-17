import { Metadata } from 'next'
import Link from 'next/link'
import {
  Radio, Shield, Wifi, HardDrive,
  Cpu, RefreshCw, Settings, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Mission Control Agent',
  description:
    'Lightweight agent for secure connectivity, local execution, and data collection across firewalled and air-gapped environments.',
  canonical: '/features/mc-agent',
})

const capabilities = [
  {
    icon: <Radio className="w-5 h-5" />,
    title: 'Lightweight Footprint',
    description:
      'The agent consumes minimal CPU, memory, and disk resources — designed to run alongside production workloads without performance impact.',
  },
  {
    icon: <Wifi className="w-5 h-5" />,
    title: 'Firewall-Friendly',
    description:
      'Connects outbound to Mission Control on a single port, eliminating the need for complex inbound firewall rules or VPN tunnels to managed systems.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Encrypted Communication',
    description:
      'All data transmitted between agent and server is encrypted with TLS 1.3, with certificate pinning and mutual authentication for maximum security.',
  },
  {
    icon: <HardDrive className="w-5 h-5" />,
    title: 'Local Execution',
    description:
      'Execute commands, scripts, and playbooks locally on managed systems without exposing SSH or RDP ports — ideal for air-gapped and high-security environments.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Auto-Update',
    description:
      'Agents automatically update when new versions are available, with staged rollouts and rollback capability to prevent widespread disruption from bad updates.',
  },
  {
    icon: <Cpu className="w-5 h-5" />,
    title: 'System Telemetry',
    description:
      'Collects host-level metrics including CPU, memory, disk, network, processes, and system events — providing deep visibility even for agents-only deployments.',
  },
]

export default function McAgentPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Mission Control Agent' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Radio className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Mission Control</span> Agent
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              The Mission Control Agent provides deep visibility and management capabilities for
              systems that cannot be monitored agentlessly — whether due to firewall
              restrictions, air-gapped networks, or the need for local command execution. The
              agent is a single, lightweight binary that runs on Linux, Windows, and macOS with
              minimal resource overhead.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Unlike traditional monitoring agents that consume significant resources and require
              complex configuration, the Mission Control Agent is designed for simplicity. A
              single configuration file and a registration token are all that is needed to bring
              a system under management. The agent connects outbound to the Mission Control
              server, eliminating the need for inbound firewall rules or VPN access to managed
              endpoints.
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
            <h2 className="text-2xl font-bold mb-4">Built for Restricted Environments</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Many enterprises operate networks with strict segmentation that prevents
              traditional agentless monitoring from reaching all systems. The Mission Control
              Agent solves this by establishing a single outbound connection to the Mission
              Control server, through which commands, configurations, and updates are delivered.
              No inbound ports need to be opened, and no VPN tunnels need to be established.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              For air-gapped environments, the agent supports offline operation with local data
              buffering. Metrics and events are collected and stored locally when the connection
              is unavailable, then transmitted to the server when connectivity is restored —
              ensuring complete data capture even in intermittently connected environments.
              The agent&apos;s binary is self-contained with no external dependencies, making
              deployment straightforward in restricted environments.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Deploy Agents in Minutes</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Install the Mission Control Agent on any Linux, Windows, or macOS system with a
              single command and bring it under management in seconds.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Download Agent
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/documentation" className="btn-outline">
                Agent Documentation
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
