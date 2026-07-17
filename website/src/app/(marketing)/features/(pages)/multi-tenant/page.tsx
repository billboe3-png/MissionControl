import { Metadata } from 'next'
import Link from 'next/link'
import {
  Building2, Shield, Users, Settings,
  Globe, BarChart3, Key, Lock, ArrowRight,
} from 'lucide-react'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Multi-Tenant Management',
  description:
    'Enterprise multi-tenancy with isolated workspaces, custom branding, role-based access, and tenant-specific policies.',
  canonical: '/features/multi-tenant',
})

const capabilities = [
  {
    icon: <Building2 className="w-5 h-5" />,
    title: 'Tenant Isolation',
    description:
      'Each tenant operates in a fully isolated workspace with separate data, credentials, users, and configurations — ensuring strict separation between business units or clients.',
  },
  {
    icon: <Shield className="w-5 h-5" />,
    title: 'Custom Branding',
    description:
      'Apply tenant-specific logos, color schemes, and domain names to provide a personalized experience for each client or business unit.',
  },
  {
    icon: <Users className="w-5 h-5" />,
    title: 'Tenant-Level RBAC',
    description:
      'Define roles and permissions independently per tenant, with the ability to promote super-administrators who can manage across all tenants.',
  },
  {
    icon: <Settings className="w-5 h-5" />,
    title: 'Policy Templates',
    description:
      'Create and enforce tenant-specific policies for alert thresholds, automation rules, retention periods, and access controls from a centralized admin interface.',
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    title: 'Usage Metering',
    description:
      'Track resource consumption, API calls, and feature usage per tenant for capacity planning, billing, and SLA compliance reporting.',
  },
  {
    icon: <Key className="w-5 h-5" />,
    title: 'Delegated Administration',
    description:
      'Allow tenant-level administrators to manage their own users, credentials, and configurations while the platform administrator retains oversight.',
  },
]

export default function MultiTenantPage() {
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Features', href: '/features' },
          { label: 'Multi-Tenant' },
        ]}
      />

      <section className="section">
        <div className="container-wide">
          <div className="max-w-3xl mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-mc-500/10 text-mc-600 dark:text-mc-400">
                <Building2 className="w-8 h-8" />
              </div>
              <h1 className="section-title">
                <span className="gradient-text">Multi-Tenant</span> Management
              </h1>
            </div>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Mission Control provides enterprise-grade multi-tenancy for managed service
              providers, large enterprises with multiple business units, and organizations
              that need strict separation between environments. Each tenant operates in a
              fully isolated workspace with its own users, credentials, monitoring
              configurations, and operational data.
            </p>
            <p className="text-lg text-surface-600 dark:text-surface-300 leading-relaxed">
              The multi-tenant architecture is built into the platform core — not bolted on as
              an afterthought. Tenant isolation extends to the database layer, credential
              storage, automation engine, and reporting system — ensuring that no data leakage
              is possible between tenants, even through API access or plugin interactions.
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
            <h2 className="text-2xl font-bold mb-4">Built for Managed Service Providers</h2>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed mb-4">
              Managed service providers need to deliver consistent, high-quality IT operations
              across hundreds of client environments while maintaining strict data isolation.
              Mission Control&apos;s multi-tenant architecture provides the separation and
              control MSPs need, with the efficiency of managing everything from a single
              platform instance.
            </p>
            <p className="text-surface-600 dark:text-surface-300 leading-relaxed">
              Tenant administrators can be granted self-service capabilities for managing their
              own users, credentials, and monitoring configurations — reducing the operational
              burden on the MSP&apos;s central team. Usage metering provides the data needed for
              accurate billing, while custom branding ensures each client experiences Mission
              Control as their own platform.
            </p>
          </section>

          <div className="glass rounded-2xl p-10 text-center">
            <h2 className="text-2xl font-bold mb-4">Scale Across Tenants with Confidence</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Deploy Mission Control as your multi-tenant IT operations platform with full
              data isolation, custom branding, and delegated administration.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/downloads" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/solutions/msp" className="btn-outline">
                MSP Solutions
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
