import { Metadata } from 'next'
import Link from 'next/link'
import {
  Box, Layers, Globe, Activity,
  Settings, RefreshCw, Shield, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Docker Management',
  description:
    'Container lifecycle management with image registries, compose deployments, swarm clusters, and real-time container monitoring.',
  canonical: '/features/docker',
})

const capabilities = [
  {
    icon: <Box className="w-5 h-5" />,
    title: 'Container Lifecycle',
    description:
      'Start, stop, restart, and remove containers with real-time log streaming, resource limits, and environment variable management from a single interface.',
  },
  {
    icon: <Layers className="w-5 h-5" />,
    title: 'Compose Deployments',
    description:
      'Deploy and manage multi-container Docker Compose stacks with visual service dependency mapping, environment overrides, and rolling update support.',
  },
  {
    icon: <Globe className="w-5 h-5" />,
    title: 'Swarm & Cluster Management',
    description:
      'Monitor Docker Swarm clusters with node status, service distribution, overlay network health, and automatic rescheduling for failed containers.',
  },
  {
    icon: <Activity className="w-5 h-5" />,
    title: 'Real-Time Monitoring',
    description:
      'Track CPU, memory, network, and disk usage per container with configurable alerts, historical trends, and resource usage breakdowns across your entire cluster.',
  },
  {
    icon: <RefreshCw className="w-5 h-5" />,
    title: 'Image Registry Management',
    description:
      'Browse and manage images across local and remote registries, track image versions, monitor registry storage, and automate image cleanup policies.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Security Scanning',
    description:
      'Scan container images for known vulnerabilities, enforce image signing policies, and generate compliance reports for your container estate.',
  },
]

export default function DockerPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Docker' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Box className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Docker</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides a comprehensive management layer for Docker environments,
              giving your operations team full visibility and control over containers, images,
              networks, and volumes across standalone hosts and Swarm clusters. Whether you run
              a handful of development containers or thousands of production services, Mission
              Control scales to meet your needs.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The Docker integration connects via the Docker Engine API and supports both
              Linux and Windows containers. Mission Control normalizes container metrics alongside
              your broader infrastructure monitoring, so a sudden spike in container CPU usage
              can be correlated with host-level resource contention, storage latency, or network
              saturation — eliminating blind spots.
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
            <h2 className="text-2xl font-bold mb-4">Container Operations at Scale</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              As container deployments grow, managing them through CLI or the Docker Desktop UI
              becomes impractical. Mission Control provides centralized visibility across all
              your Docker hosts, with role-based access controls that let developers manage
              their own containers while operations retains control over infrastructure-level
              configuration and networking.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Automated container health checks, restart policies, and resource quota enforcement
              help maintain service stability without manual intervention. When containers
              misbehave, Mission Control automatically captures logs, creates incident records,
              and can trigger remediation playbooks — reducing mean time to resolution from
              hours to minutes.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Master Your Container Estate</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Connect your Docker hosts and Swarm clusters to Mission Control for unified
              monitoring, management, and automated operations.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/features/mc-agent" className="btn-outline">
                Agent Deployment
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
