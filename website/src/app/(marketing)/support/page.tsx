import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Headphones, Mail, MessageSquare, Phone, Clock, CheckCircle, ArrowRight } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Support',
  description: 'Get help with Mission Control. Choose from community support, priority email support, or a dedicated support engineer based on your plan.',
  canonical: '/support',
})

const supportPlans = [
  {
    name: 'Community',
    for: 'Community Plan',
    channels: ['Community forum', 'GitHub issues'],
    responseTime: 'Best effort',
    availability: 'Community hours',
    features: [
      'Access to community forum',
      'Browse knowledge base',
      'Submit GitHub issues',
      'Community-driven answers',
    ],
  },
  {
    name: 'Priority',
    for: 'Professional Plan',
    channels: ['Email', 'Community forum', 'GitHub issues'],
    responseTime: '24 hours',
    availability: 'Business hours (EST)',
    features: [
      'Priority email support',
      'Faster response times',
      'Escalation path',
      'Bug fix prioritization',
      'Access to early releases',
    ],
    featured: true,
  },
  {
    name: 'Dedicated',
    for: 'Enterprise Plan',
    channels: ['Dedicated engineer', 'Phone', 'Email', 'Slack'],
    responseTime: '1 hour (critical)',
    availability: '24/7/365',
    features: [
      'Named support engineer',
      'Direct phone support',
      'Private Slack channel',
      'Critical issue escalation',
      'Quarterly business reviews',
      'Custom training sessions',
    ],
  },
]

export default function SupportPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Support' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Support</span>
            </h1>
            <p className="section-subtitle">
              Our team is here to help you succeed with Mission Control. Choose the support level that matches your needs.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-20">
            {supportPlans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl p-8 card-hover flex flex-col ${
                  plan.featured
                    ? 'bg-mc-600 text-white ring-2 ring-mc-500 relative'
                    : 'glass'
                }`}
              >
                {plan.featured && (
                  <span className="absolute -top-3 left-8 bg-white text-mc-600 text-xs font-semibold px-3 py-1 rounded-full">
                    Recommended
                  </span>
                )}
                <h3 className={`text-xl font-bold mb-1 ${plan.featured ? 'text-white' : ''}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm mb-6 ${plan.featured ? 'text-mc-100' : 'text-surface-500 dark:text-surface-400'}`}>
                  {plan.for}
                </p>

                <div className="space-y-3 mb-6">
                  <div className={`flex items-center gap-2 text-sm ${plan.featured ? 'text-mc-100' : 'text-surface-600 dark:text-surface-300'}`}>
                    <Clock className="w-4 h-4 flex-shrink-0" />
                    <span>Response: {plan.responseTime}</span>
                  </div>
                  <div className={`flex items-center gap-2 text-sm ${plan.featured ? 'text-mc-100' : 'text-surface-600 dark:text-surface-300'}`}>
                    <Headphones className="w-4 h-4 flex-shrink-0" />
                    <span>Hours: {plan.availability}</span>
                  </div>
                </div>

                <ul className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.featured ? 'text-mc-200' : 'text-green-500'}`} />
                      <span className={plan.featured ? 'text-mc-50' : 'text-surface-600 dark:text-surface-300'}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <Link
                  href="/contact"
                  className={plan.featured ? 'btn bg-white text-mc-600 hover:bg-mc-50 w-full justify-center' : 'btn-primary w-full justify-center'}
                >
                  Get Support
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-4">Quick Resources</h3>
              <div className="space-y-3">
                {[
                  { label: 'Documentation', href: '/documentation' },
                  { label: 'Knowledge Base', href: '/knowledge-base' },
                  { label: 'Community Forum', href: '/community' },
                  { label: 'API Reference', href: '/api-reference' },
                ].map((resource) => (
                  <Link
                    key={resource.label}
                    href={resource.href}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
                  >
                    <ArrowRight className="w-4 h-4 text-mc-600 dark:text-mc-400" />
                    <span className="font-medium text-sm">{resource.label}</span>
                  </Link>
                ))}
              </div>
            </div>
            <div className="glass rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-4">System Status</h3>
              <p className="text-surface-500 dark:text-surface-400 text-sm mb-4">
                Check the current status of Mission Control services before contacting support.
              </p>
              <div className="space-y-3">
                {['API Gateway', 'Agent Communication', 'Dashboard', 'Alert Engine'].map((service) => (
                  <div key={service} className="flex items-center justify-between p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50">
                    <span className="text-sm font-medium">{service}</span>
                    <span className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                      Operational
                    </span>
                  </div>
                ))}
              </div>
              <Link href="/status" className="text-sm text-mc-600 dark:text-mc-400 hover:underline mt-4 inline-block">
                View full status page →
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
