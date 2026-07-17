import { Metadata } from 'next'
import Link from 'next/link'
import {
  Container, Cpu, HardDrive, ArrowRightLeft,
  Shield, BarChart3, Network, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Proxmox Management',
  description:
    'Manage Proxmox clusters with unified VM/CT operations, storage management, HA configuration, and live migration support.',
  canonical: '/features/proxmox',
})

const capabilities = [
  {
    icon: <Container className="w-5 h-5" />,
    title: 'VM & Container Management',
    description:
      'Manage both KVM virtual machines and LXC containers from a unified interface — create, start, stop, clone, and configure resources without switching tools.',
  },
  {
    icon: <Cpu className="w-5 h-5" />,
    title: 'Cluster Operations',
    description:
      'Monitor Proxmox cluster health, quorum status, and node resource usage across multi-node clusters with real-time status and historical trend data.',
  },
  {
    icon: <ArrowRightLeft className="w-5 h-5" />,
    title: 'Live Migration',
    description:
      'Migrate running VMs and containers between nodes with zero downtime, with automatic placement recommendations based on resource availability.',
  },
  {
    icon: <HardDrive className="w-5 h-5" />,
    title: 'Storage Management',
    description:
      'View and manage ZFS pools, Ceph storage, local storage, and NFS/iSCSI targets with capacity monitoring, thin provisioning status, and snapshot management.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'High Availability',
    description:
      'Configure HA groups, fencing policies, and failover priorities — then monitor HA status and automatic recovery events from a centralized dashboard.',
  },
  {
    icon: <Network className="w-5 h-5" />,
    title: 'Network Configuration',
    description:
      'Manage virtual bridges, VLANs, and SDN zones across Proxmox nodes with topology visualization and configuration comparison between nodes.',
  },
]

export default function ProxmoxPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Proxmox' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Container className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Proxmox</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control brings enterprise-grade management capabilities to your Proxmox
              VE clusters. Manage virtual machines, LXC containers, storage pools, and network
              configurations from a single interface — whether you are running a single-node
              homelab or a multi-site production cluster.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              Connect via the Proxmox REST API to gain full visibility into your cluster topology,
              resource utilization, and virtual machine lifecycle. Mission Control normalizes
              Proxmox data alongside other platforms in your environment, giving your team a
              consistent operational view regardless of the underlying hypervisor.
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
            <h2 className="text-2xl font-bold mb-4">Proxmox Without the Complexity</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Proxmox VE offers powerful virtualization at a fraction of the cost of commercial
              alternatives, but managing it at scale through the web UI alone becomes tedious.
              Mission Control automates routine operations like VM provisioning from templates,
              scheduled backups, snapshot rotation, and certificate management — while providing
              alerting and monitoring that Proxmox does not include natively.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              For mixed environments, Mission Control presents Proxmox alongside Hyper-V, VMware,
              and container platforms in a unified view. Your operations team can manage all
              virtualization platforms from one place, with consistent role-based access controls
              and audit logging across every platform.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Manage Proxmox at Scale</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Connect your Proxmox cluster to Mission Control and gain enterprise management
              capabilities including monitoring, automation, and role-based access control.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/docker" className="btn-outline">
                Explore Docker
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
