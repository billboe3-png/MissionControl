import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Handshake, Building2, Code, GraduationCap, ArrowRight, CheckCircle } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Partners',
  description: 'Join the Mission Control partner program. Technology partners, resellers, MSPs, and system integrators — grow your business with the leading IT operations platform.',
  canonical: '/partners',
})

const partnerTypes = [
  {
    icon: Building2,
    title: 'Reseller Partners',
    description: 'Sell Mission Control to your customers with competitive margins, sales enablement, and co-marketing support.',
    benefits: [
      'Up to 35% margin on new deals',
      'Dedicated partner account manager',
      'Co-branded marketing materials',
      'Lead sharing and referrals',
    ],
  },
  {
    icon: Code,
    title: 'Technology Partners',
    description: 'Integrate your product with Mission Control through our plugin framework and reach thousands of IT operations teams.',
    benefits: [
      'Access to plugin SDK and APIs',
      'Joint solution engineering',
      'Listing in the plugin marketplace',
      'Co-development opportunities',
    ],
  },
  {
    icon: GraduationCap,
    title: 'Training Partners',
    description: 'Deliver Mission Control certification and training programs to IT professionals worldwide.',
    benefits: [
      'Certified trainer program',
      'Training curriculum and materials',
      'Exam and certification platform',
      'Global training directory listing',
    ],
  },
]

const stats = [
  { value: '200+', label: 'Active Partners' },
  { value: '45', label: 'Countries' },
  { value: '98%', label: 'Partner Satisfaction' },
  { value: '3x', label: 'Revenue Growth' },
]

export default function PartnersPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Partners' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Partner Program</span>
            </h1>
            <p className="section-subtitle">
              Build your business on the Mission Control platform. We partner with resellers, technology vendors, and system integrators to deliver exceptional IT operations solutions.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6 mb-20">
            {stats.map((stat) => (
              <div key={stat.label} className="glass rounded-xl p-6 text-center">
                <div className="text-3xl font-bold gradient-text mb-1">{stat.value}</div>
                <div className="text-sm text-surface-500 dark:text-surface-400">{stat.label}</div>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-20">
            {partnerTypes.map((partner) => (
              <div key={partner.title} className="glass rounded-xl p-8 card-hover">
                <div className="w-12 h-12 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mb-4">
                  <partner.icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{partner.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 text-sm mb-6">
                  {partner.description}
                </p>
                <ul className="space-y-2.5">
                  {partner.benefits.map((benefit) => (
                    <li key={benefit} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-surface-600 dark:text-surface-300">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="glass rounded-xl p-12 text-center">
            <Handshake className="w-12 h-12 text-mc-600 dark:text-mc-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-4">Ready to Become a Partner?</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-2xl mx-auto">
              Our partner team will work with you to find the right engagement model for your business. We provide the tools, training, and support you need to succeed.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/contact" className="btn-primary">
                Apply Now
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/documentation" className="btn-secondary">
                Partner Documentation
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
