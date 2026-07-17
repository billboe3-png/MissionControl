import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata as genMeta } from '@/lib/seo'
import { blogPosts } from '@/data/content'
import { Calendar, User, Tag, ArrowLeft } from 'lucide-react'

export function generateStaticParams() {
  return blogPosts.map((post) => ({
    slug: post.slug,
  }))
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const post = blogPosts.find((p) => p.slug === params.slug)
  if (!post) return {}

  return genMeta({
    title: post.title,
    description: post.excerpt,
    canonical: `/blog/${post.slug}`,
    ogType: 'article',
    publishedTime: post.date,
    authors: [post.author],
    tags: post.tags,
  })
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = blogPosts.find((p) => p.slug === params.slug)

  if (!post) {
    notFound()
  }

  const postContent: Record<string, string> = {
    'introducing-mission-control-3': `
      <p>We are thrilled to announce the general availability of Mission Control 3.0, the most significant release in our platform's history. This version introduces AI-assisted operations, a completely redesigned plugin framework, and enterprise-grade multi-tenancy — all built on a foundation of security and reliability.</p>
      <h2>AI-Assisted Operations</h2>
      <p>The new AI Incident Response Engine analyzes alert patterns in real time, correlating data across your entire infrastructure to identify root causes automatically. Machine learning models trained on thousands of production incidents reduce mean time to resolution by up to 60%.</p>
      <h2>Plugin Framework v2</h2>
      <p>Our redesigned plugin architecture supports community-contributed plugins with sandboxed execution, version management, and a rich API surface. The new plugin marketplace enables discovery, rating, and one-click installation of community extensions.</p>
      <h2>Enterprise Multi-Tenancy</h2>
      <p>Organizations managing multiple clients or business units can now fully isolate tenants with separate dashboards, alert channels, user pools, and data retention policies — all from a single Mission Control deployment.</p>
    `,
    'ai-incident-management': `
      <p>Artificial intelligence is fundamentally changing how IT operations teams detect, diagnose, and resolve incidents. Traditional threshold-based alerting generates noise; AI-driven incident management generates signal.</p>
      <h2>Predictive Alerting</h2>
      <p>Rather than waiting for a metric to breach a static threshold, predictive models learn the normal behavior patterns of each metric over time. When a deviation from the learned pattern is detected, an alert is raised before the threshold is ever reached.</p>
      <h2>Automated Root Cause Analysis</h2>
      <p>When an incident occurs, correlating alerts across dozens or hundreds of metrics is a manual and time-consuming process. AI engines ingest alert streams and infrastructure topology to surface the most probable root cause within seconds.</p>
      <h2>Impact on MTTR</h2>
      <p>Organizations that have adopted AI-assisted incident management report reductions in mean time to resolution ranging from 40% to 70%. The combination of predictive alerting and automated root cause analysis means teams spend less time triaging and more time resolving.</p>
    `,
    'multi-tenant-best-practices': `
      <p>Managed Service Providers face a unique challenge: managing infrastructure for dozens or hundreds of clients from a single operational platform while maintaining strict data isolation and access control.</p>
      <h2>Tenant Isolation Architecture</h2>
      <p>Mission Control's multi-tenant architecture provides logical isolation at every layer — from data storage and alert routing to user authentication and API access. Each tenant operates as an independent environment within the shared platform.</p>
      <h2>Role-Based Access Control</h2>
      <p>Define granular roles that control what each team member can see and do across tenants. Client-specific administrators can be scoped to only their tenant, while MSP operations staff maintain full visibility across all clients.</p>
      <h2>Scaling Efficiently</h2>
      <p>The key to profitable MSP operations is scaling without proportional headcount growth. Mission Control's automation playbooks, template-based provisioning, and cross-tenant reporting enable a single operations team to manage thousands of endpoints across multiple clients.</p>
    `,
    'securing-remote-operations': `
      <p>Remote server access is essential for modern IT operations, but it introduces significant security and compliance risks if not properly managed. Mission Control provides a comprehensive framework for secure remote operations.</p>
      <h2>Session Recording</h2>
      <p>Every remote session is recorded and stored in an immutable audit log. Recordings capture the complete terminal session including input, output, and timestamps for full forensic visibility.</p>
      <h2>Zero-Trust Agent Communication</h2>
      <p>The Mission Control agent communicates with the server over mTLS-encrypted channels. Every connection is authenticated using short-lived certificates, and the agent verifies the server identity before transmitting any data.</p>
      <h2>Compliance Auditing</h2>
      <p>Built-in compliance frameworks for SOC 2, HIPAA, PCI DSS, and ISO 27001 automatically map your security controls to regulatory requirements. Audit reports are generated on-demand for internal review or external assessment.</p>
    `,
  }

  const content = postContent[post.slug] || `<p>${post.excerpt}</p>`

  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Blog', href: '/blog' },
          { label: post.title },
        ]}
      />

      <article className="section">
        <div className="container-wide max-w-4xl">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-surface-500 hover:text-mc-600 dark:hover:text-mc-400 transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Blog
          </Link>

          <div className="flex flex-wrap gap-2 mb-4">
            {post.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 text-xs font-medium"
              >
                {tag}
              </span>
            ))}
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
            {post.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-surface-500 dark:text-surface-400 mb-8 pb-8 border-b border-surface-200 dark:border-surface-800">
            <span className="flex items-center gap-1.5">
              <User className="w-4 h-4" />
              {post.author}
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              {new Date(post.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>

          <div
            className="prose prose-lg dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />

          <div className="mt-16 pt-8 border-t border-surface-200 dark:border-surface-800">
            <div className="glass rounded-xl p-8 text-center">
              <h3 className="text-xl font-semibold mb-3">Interested in Mission Control?</h3>
              <p className="text-surface-500 dark:text-surface-400 mb-6">
                See how Mission Control can transform your IT operations.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link href="/demo" className="btn-primary">
                  Request a Demo
                </Link>
                <Link href="/pricing" className="btn-secondary">
                  View Pricing
                </Link>
              </div>
            </div>
          </div>
        </div>
      </article>
    </>
  )
}
