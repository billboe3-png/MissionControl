import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Download, Server, Monitor, Terminal, Package, Shield, CheckCircle } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Downloads',
  description: 'Download Mission Control components including the server platform, Linux agent, Windows agent, and source code. Available for all supported platforms.',
  canonical: '/downloads',
})

const downloads = [
  {
    icon: Package,
    title: 'Docker Deployment',
    description: 'Deploy Mission Control using Docker Compose or Kubernetes. Includes the full platform with all services pre-configured for production use.',
    versions: [
      { name: 'Docker Compose', version: '3.0.0', size: '~850 MB', os: 'Any Docker Host' },
      { name: 'Kubernetes Helm Chart', version: '3.0.0', size: '~1.2 GB', os: 'Kubernetes 1.25+' },
    ],
    recommended: true,
    command: 'docker pull missioncontrol/server:latest',
  },
  {
    icon: Server,
    title: 'Linux Agent',
    description: 'The Mission Control agent for Linux servers. Monitors system metrics, manages services, and enables remote operations.',
    versions: [
      { name: '.deb (Ubuntu/Debian)', version: '3.0.0', size: '~28 MB', os: 'Ubuntu 20.04+, Debian 11+' },
      { name: '.rpm (RHEL/CentOS)', version: '3.0.0', size: '~30 MB', os: 'RHEL 8+, CentOS 8+, Rocky 8+' },
      { name: '.rpm (SUSE)', version: '3.0.0', size: '~30 MB', os: 'SUSE Linux Enterprise 15+' },
    ],
    recommended: false,
    command: 'curl -fsSL https://get.missioncontrol.io/agent/linux | sudo bash',
  },
  {
    icon: Monitor,
    title: 'Windows Agent',
    description: 'The Mission Control agent for Windows servers and workstations. Full WMI integration, service management, and remote PowerShell support.',
    versions: [
      { name: 'Windows Server 2019/2022/2025', version: '3.0.0', size: '~35 MB', os: 'Windows Server 2019+' },
      { name: 'Windows 10/11', version: '3.0.0', size: '~35 MB', os: 'Windows 10 21H2+' },
    ],
    recommended: false,
    command: 'msiexec /i mc-agent-windows-x64.msi /quiet',
  },
  {
    icon: Terminal,
    title: 'Source Code',
    description: 'Build Mission Control from source. Full access to the codebase, build tools, and development environment setup instructions.',
    versions: [
      { name: 'GitHub Repository', version: 'v3.0.0', size: 'Source', os: 'All Platforms' },
      { name: 'Release Tarball', version: '3.0.0', size: '~45 MB', os: 'All Platforms' },
    ],
    recommended: false,
    command: 'git clone https://github.com/missioncontrol/missioncontrol.git',
  },
]

export default function DownloadsPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Downloads' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Download Mission Control</span>
            </h1>
            <p className="section-subtitle">
              Get started with Mission Control in minutes. Deploy via Docker, install the agent on your servers, or build from source.
            </p>
          </div>

          <div className="grid gap-8">
            {downloads.map((item) => (
              <div
                key={item.title}
                className={`glass rounded-xl p-8 card-hover ${
                  item.recommended ? 'ring-2 ring-mc-500 relative' : ''
                }`}
              >
                {item.recommended && (
                  <span className="absolute -top-3 left-8 bg-mc-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Recommended
                  </span>
                )}
                <div className="flex flex-col lg:flex-row gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center">
                        <item.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                      </div>
                      <h3 className="text-xl font-semibold">{item.title}</h3>
                    </div>
                    <p className="text-surface-500 dark:text-surface-400 mb-4">
                      {item.description}
                    </p>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {item.versions.map((v) => (
                        <div
                          key={v.name}
                          className="flex items-start gap-2 text-sm"
                        >
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-medium">{v.name}</span>
                            <span className="text-surface-400 ml-2">{v.version}</span>
                            <span className="text-surface-400 ml-1">({v.size}, {v.os})</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="lg:w-96 flex-shrink-0">
                    <code className="block p-4 rounded-lg bg-surface-900 dark:bg-surface-950 text-green-400 text-sm font-mono overflow-x-auto mb-4">
                      {item.command}
                    </code>
                    <Link href="/contact" className="btn-primary w-full justify-center">
                      <Download className="w-4 h-4" />
                      Download
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-16 grid md:grid-cols-3 gap-6">
            <div className="glass rounded-xl p-6 text-center">
              <Shield className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Verified Builds</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                All downloads are cryptographically signed and verified against SHA-256 checksums.
              </p>
            </div>
            <div className="glass rounded-xl p-6 text-center">
              <Server className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">System Requirements</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Minimum 2 CPU cores, 4 GB RAM, 20 GB disk. See full requirements in our documentation.
              </p>
            </div>
            <div className="glass rounded-xl p-6 text-center">
              <Terminal className="w-8 h-8 text-mc-600 dark:text-mc-400 mx-auto mb-3" />
              <h4 className="font-semibold mb-2">Quick Install</h4>
              <p className="text-sm text-surface-500 dark:text-surface-400">
                Follow the quick start guide for a step-by-step walkthrough of your first deployment.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
