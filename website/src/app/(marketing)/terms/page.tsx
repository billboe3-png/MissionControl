import { Metadata } from 'next'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Terms of Service',
  description: 'Mission Control Terms of Service. Read our terms governing your use of the Mission Control platform, website, and related services.',
  canonical: '/terms',
})

export default function TermsPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Terms of Service' }]} />

      <section className="section">
        <div className="container-wide max-w-4xl">
          <h1 className="text-3xl font-bold mb-2">Terms of Service</h1>
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-10">
            Effective Date: July 1, 2026 | Last Updated: July 1, 2026
          </p>

          <div className="prose prose-lg dark:prose-invert max-w-none space-y-8">
            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">1. Agreement to Terms</h2>
              <p className="text-surface-600 dark:text-surface-300">
                By accessing or using the Mission Control platform, website, and related services (collectively, the &quot;Service&quot;), you agree to be bound by these Terms of Service (&quot;Terms&quot;). If you are using the Service on behalf of an organization, you represent that you have authority to bind that organization to these Terms. If you do not agree, do not use the Service.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">2. Description of Service</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Mission Control is an enterprise IT operations platform that provides unified monitoring, infrastructure management, automation, AI-assisted operations, remote administration, and a plugin ecosystem. The Service includes the web-based dashboard, agent software, REST API, and all associated documentation and support services.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">3. Account Registration</h2>
              <p className="text-surface-600 dark:text-surface-300">
                To use certain features of the Service, you must create an account. You agree to provide accurate, current, and complete information during registration and to keep your account information up to date. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You must notify us immediately of any unauthorized use of your account.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">4. Subscription Plans and Payment</h2>
              <p className="text-surface-600 dark:text-surface-300">
                The Service is offered under various subscription plans as described on our pricing page. By selecting a paid plan, you authorize us to charge the applicable fees to your payment method. All fees are quoted in United States Dollars and are exclusive of taxes unless otherwise stated. Fees are billed in advance on a monthly or annual basis depending on your billing cycle. We reserve the right to change our pricing with 30 days&apos; notice.
              </p>
              <p className="text-surface-600 dark:text-surface-300 mt-3">
                Free trial periods are available for certain plans. At the end of a trial period, your account will be converted to a paid subscription unless you cancel before the trial expires. We do not offer refunds for partial billing periods.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">5. Acceptable Use Policy</h2>
              <p className="text-surface-600 dark:text-surface-300">
                You agree not to use the Service to: violate any applicable law or regulation; infringe on the rights of others; transmit malware, viruses, or other harmful code; attempt to gain unauthorized access to the Service or related systems; interfere with or disrupt the Service or servers; use the Service to send unsolicited communications; or use the Service for any purpose that is unlawful or prohibited by these Terms. We reserve the right to suspend or terminate accounts that violate this policy.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">6. Intellectual Property</h2>
              <p className="text-surface-600 dark:text-surface-300">
                The Service and all associated content, features, functionality, and underlying technology are owned by Mission Control and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws. These Terms do not grant you any right, title, or interest in the Service, trademarks, or other brand features. You may not copy, modify, distribute, sell, or lease any part of the Service without our express written consent.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">7. Data Ownership and Processing</h2>
              <p className="text-surface-600 dark:text-surface-300">
                You retain all rights to the data you collect through the Mission Control platform (&quot;Customer Data&quot;). We process Customer Data solely to provide the Service as described in these Terms and our Privacy Policy. You grant us a limited license to host, store, and process Customer Data as necessary to provide the Service. Upon termination, we will make your Customer Data available for export for 30 days, after which it will be deleted in accordance with our data retention policies.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">8. Service Level and Availability</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We are committed to maintaining high availability of the Service. For Professional and Enterprise plans, we offer a Service Level Agreement (SLA) guaranteeing 99.9% uptime measured monthly. If we fail to meet the SLA, eligible customers will receive service credits as described in the SLA. Exclusions include scheduled maintenance, force majeure events, and issues caused by customer configuration or third-party services.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">9. Limitation of Liability</h2>
              <p className="text-surface-600 dark:text-surface-300">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, MISSION CONTROL SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES. IN NO EVENT SHALL OUR AGGREGATE LIABILITY EXCEED THE GREATER OF (A) THE AMOUNTS PAID BY YOU TO US IN THE 12 MONTHS PRIOR TO THE EVENT GIVING RISE TO LIABILITY, OR (B) ONE HUNDRED DOLLARS ($100).
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">10. Indemnification</h2>
              <p className="text-surface-600 dark:text-surface-300">
                You agree to indemnify and hold harmless Mission Control and its officers, directors, employees, and agents from any claims, losses, damages, liabilities, costs, and expenses (including reasonable attorneys&apos; fees) arising out of or relating to your use of the Service, your violation of these Terms, or your violation of any rights of a third party.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">11. Termination</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Either party may terminate this agreement at any time. You may terminate your account at any time through the platform settings or by contacting support. We may suspend or terminate your access to the Service immediately if you breach these Terms. Upon termination, your right to use the Service ceases immediately. We will make your Customer Data available for export for 30 days following termination.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">12. Dispute Resolution</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Any disputes arising from these Terms shall be resolved through binding arbitration administered in accordance with applicable arbitration rules. The arbitration shall be conducted in English. Either party may seek injunctive relief in a court of competent jurisdiction to prevent irreparable harm pending arbitration.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">13. General Provisions</h2>
              <p className="text-surface-600 dark:text-surface-300">
                These Terms are governed by the laws of the applicable jurisdiction without regard to conflict of law principles. If any provision is found to be unenforceable, the remaining provisions remain in full force and effect. These Terms constitute the entire agreement between you and Mission Control regarding the Service and supersede all prior agreements.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">14. Contact</h2>
              <p className="text-surface-600 dark:text-surface-300">
                If you have questions about these Terms, contact us at legal@missioncontrol.io.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
