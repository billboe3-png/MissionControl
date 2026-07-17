import { Metadata } from 'next'
import Link from 'next/link'
import {
  Monitor, Cpu, HardDrive, ArrowRightLeft,
  Shield, BarChart3, Settings, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Hyper-V Management',
  description:
    'Full lifecycle management for Hyper-V hosts and VMs including provisioning, migration, replication, and backup orchestration.',
  canonical: '/features/hyper-v',
})

const capabilities = [
  {
    icon: <Monitor className="w-5 h-5" />,
    title: 'Host & Cluster Management',
    description:
      'Manage standalone Hyper-V hosts and Failover Clusters from a single console with real-time health status, resource utilization, and failover readiness checks.',
  },
  {
    icon: <Cpu className="w-5 h-5" />,
    title: 'VM Lifecycle Operations',
    description:
      'Create, configure, start, stop, snapshot, and remove virtual machines through a guided interface — with template support for rapid, consistent provisioning.',
  },
  {
    icon: <ArrowRightLeft className="w-5 h-5" />,
    title: 'Live Migration',
    description:
      'Initiate live migrations between hosts with zero downtime, automatic VM placement recommendations, and bandwidth-aware scheduling for production workloads.',
  },
  {
    icon: <HardDrive className="w-5 h-5" />,
    title: 'Storage Management',
    description:
      'Monitor and manage VHDX files, storage pools, SMB shares, and Cluster Shared Volumes with thin provisioning, deduplication reporting, and capacity forecasting.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Replication & Backup',
    description:
      'Configure Hyper-V Replica for disaster recovery and orchestrate backup jobs with major Veeam and Windows Server Backup integrations.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Performance Insights',
    description:
      'Track per-VM CPU, memory, disk I/O, and network throughput with historical trends, right-sizing recommendations, and density optimization analysis.',
  },
]

export default function HyperVPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Hyper-V' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Monitor className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Hyper-V</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides comprehensive lifecycle management for Microsoft Hyper-V
              environments — from single-host deployments to multi-node Failover Clusters. View
              every host, virtual machine, and storage resource in a unified interface that goes
              beyond what Hyper-V Manager and Failover Cluster Manager offer natively.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Manage virtual machines across your entire Hyper-V estate without switching
              between remote desktop sessions or PowerShell windows. Mission Control connects
              via WMI and the Hyper-V API to provide full CRUD operations, performance data,
              and configuration management — all secured through the credential vault with
              complete audit logging.
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
            <h2 className="text-2xl font-bold mb-4">Hyper-V at Enterprise Scale</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Managing Hyper-V at scale requires more than the native Windows tools provide.
              Mission Control aggregates data across hundreds of hosts, surfaces cluster health
              in a single dashboard, and automates routine operations like VM provisioning,
              template deployment, and snapshot cleanup. Role-based access controls ensure that
              junior administrators can perform approved operations without access to sensitive
              cluster configuration.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Integration with Active Directory enables automatic assignment of VM ownership,
              while the automation engine can enforce naming conventions, resource limits, and
              tagging policies as virtual machines are created — preventing configuration drift
              before it starts.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Streamline Your Hyper-V Operations</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Connect Mission Control to your Hyper-V environment and manage hosts, VMs, and
              clusters from one unified platform.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/proxmox" className="btn-outline">
                Explore Proxmox
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
