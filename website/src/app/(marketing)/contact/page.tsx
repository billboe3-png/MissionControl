import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { Mail, Phone, MapPin, Clock, MessageSquare, Headphones, Building2 } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Contact',
  description: 'Get in touch with Mission Control. Reach our sales team, support engineers, or partnership team. We respond to all inquiries within one business day.',
  canonical: '/contact',
})

const contacts = [
  {
    icon: Mail,
    title: 'General Inquiries',
    description: 'Questions about Mission Control or our platform?',
    value: 'hello@missioncontrol.io',
    responseTime: 'Within 24 hours',
  },
  {
    icon: Headphones,
    title: 'Technical Support',
    description: 'Need help with an issue? Our support team is standing by.',
    value: 'support@missioncontrol.io',
    responseTime: '24 hours (Professional)',
  },
  {
    icon: Building2,
    title: 'Sales',
    description: 'Interested in Enterprise or have a custom requirement?',
    value: 'sales@missioncontrol.io',
    responseTime: 'Within 4 hours',
  },
  {
    icon: MessageSquare,
    title: 'Partnerships',
    description: 'Want to become a partner or discuss integration?',
    value: 'partners@missioncontrol.io',
    responseTime: 'Within 48 hours',
  },
]

export default function ContactPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Contact' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Contact Us</span>
            </h1>
            <p className="section-subtitle">
              We would love to hear from you. Reach out to the right team and we will get back to you promptly.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="glass rounded-xl p-8">
              <h2 className="text-xl font-semibold mb-6">Send Us a Message</h2>
              <form className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">First Name</label>
                    <input
                      type="text"
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Last Name</label>
                    <input
                      type="text"
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm"
                      placeholder="Smith"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Work Email</label>
                  <input
                    type="email"
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm"
                    placeholder="john@company.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Company</label>
                  <input
                    type="text"
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm"
                    placeholder="Acme Corporation"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Subject</label>
                  <select className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm">
                    <option>General Inquiry</option>
                    <option>Sales</option>
                    <option>Technical Support</option>
                    <option>Partnership</option>
                    <option>Press</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Message</label>
                  <textarea
                    rows={5}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 text-surface-900 dark:text-surface-100 focus:outline-none focus:ring-2 focus:ring-mc-500 focus:border-transparent text-sm resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>
                <button type="submit" className="btn-primary w-full justify-center">
                  Send Message
                </button>
              </form>
            </div>

            <div className="space-y-6">
              {contacts.map((contact) => (
                <div key={contact.title} className="glass rounded-xl p-6 card-hover">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center flex-shrink-0">
                      <contact.icon className="w-5 h-5 text-mc-600 dark:text-mc-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{contact.title}</h3>
                      <p className="text-sm text-surface-500 dark:text-surface-400 mb-1">
                        {contact.description}
                      </p>
                      <a href={`mailto:${contact.value}`} className="text-sm text-mc-600 dark:text-mc-400 hover:underline">
                        {contact.value}
                      </a>
                      <p className="text-xs text-surface-400 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {contact.responseTime}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
