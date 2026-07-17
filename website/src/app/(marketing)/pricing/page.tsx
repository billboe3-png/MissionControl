import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { pricingPlans } from '@/data/content'
import { CheckCircle, ArrowRight, HelpCircle } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Pricing',
  description: 'Mission Control pricing plans for teams of every size. Start free with the Community plan, scale with Professional, or go Enterprise for unlimited infrastructure.',
  canonical: '/pricing',
})

const faqs = [
  {
    question: 'How are nodes counted?',
    answer: 'A node is any server, virtual machine, container, or cloud instance that the Mission Control agent monitors. Each agent instance counts as one node regardless of how many services run on it.',
  },
  {
    question: 'Is there a free trial for the Professional plan?',
    answer: 'Yes. The Professional plan includes a 30-day free trial with full feature access. No credit card is required to start the trial.',
  },
  {
    question: 'Can I switch plans at any time?',
    answer: 'You can upgrade or downgrade your plan at any time. Upgrades take effect immediately with prorated billing. Downgrades take effect at the end of the current billing cycle.',
  },
  {
    question: 'What support is included?',
    answer: 'Community plan includes community forum access. Professional plan includes priority email support with 24-hour response time. Enterprise plan includes a dedicated support engineer with SLA guarantees.',
  },
  {
    question: 'Do you offer volume discounts?',
    answer: 'Yes. Volume discounts are available for deployments exceeding 1,000 nodes. Contact our sales team for a custom quote.',
  },
  {
    question: 'Is Mission Control available as a hosted SaaS?',
    answer: 'Mission Control can be deployed on-premises or as a managed cloud instance. We offer managed cloud hosting for Professional and Enterprise plans.',
  },
]

export default function PricingPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Pricing' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Simple, Transparent Pricing</span>
            </h1>
            <p className="section-subtitle">
              Start free and scale as you grow. No hidden fees, no per-seat charges, no surprises.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-20">
            {pricingPlans.map((plan) => (
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
                    Most Popular
                  </span>
                )}
                <h3 className={`text-xl font-bold mb-1 ${plan.featured ? 'text-white' : ''}`}>
                  {plan.name}
                </h3>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period && (
                    <span className={`text-sm ${plan.featured ? 'text-mc-100' : 'text-surface-500 dark:text-surface-400'}`}>
                      {plan.period}
                    </span>
                  )}
                </div>
                <p className={`text-sm mb-6 ${plan.featured ? 'text-mc-100' : 'text-surface-500 dark:text-surface-400'}`}>
                  {plan.description}
                </p>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm">
                      <CheckCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.featured ? 'text-mc-200' : 'text-green-500'}`} />
                      <span className={plan.featured ? 'text-mc-50' : 'text-surface-600 dark:text-surface-300'}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.href}
                  className={plan.featured ? 'btn bg-white text-mc-600 hover:bg-mc-50 w-full justify-center' : 'btn-primary w-full justify-center'}
                >
                  {plan.cta}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>

          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-10">Frequently Asked Questions</h2>
            <div className="space-y-6">
              {faqs.map((faq) => (
                <div key={faq.question} className="glass rounded-xl p-6">
                  <h3 className="font-semibold mb-2 flex items-start gap-2">
                    <HelpCircle className="w-5 h-5 text-mc-600 dark:text-mc-400 flex-shrink-0 mt-0.5" />
                    {faq.question}
                  </h3>
                  <p className="text-surface-500 dark:text-surface-400 text-sm pl-7">
                    {faq.answer}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
