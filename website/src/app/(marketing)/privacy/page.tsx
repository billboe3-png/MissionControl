import { Metadata } from 'next'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'

export const metadata: Metadata = generateMetadata({
  title: 'Privacy Policy',
  description: 'Mission Control Privacy Policy. Learn how we collect, use, protect, and share your personal information and platform data.',
  canonical: '/privacy',
})

export default function PrivacyPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Privacy Policy' }]} />

      <section className="section">
        <div className="container-wide max-w-4xl">
          <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
          <p className="text-sm text-surface-500 dark:text-surface-400 mb-10">
            Effective Date: July 1, 2026 | Last Updated: July 1, 2026
          </p>

          <div className="prose prose-lg dark:prose-invert max-w-none space-y-8">
            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">1. Introduction</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Mission Control (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website at missioncontrol.io and use the Mission Control platform (collectively, the &quot;Service&quot;). By accessing or using the Service, you agree to the terms of this Privacy Policy. If you do not agree, please do not use the Service.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">2. Information We Collect</h2>
              <h3 className="text-lg font-medium mt-4 mb-2">2.1 Personal Information</h3>
              <p className="text-surface-600 dark:text-surface-300">
                We may collect personally identifiable information that you voluntarily provide to us, including but not limited to: your name, email address, company name, job title, phone number, billing address, and payment information. This information is collected when you register for an account, subscribe to a plan, contact our support team, or subscribe to our newsletter.
              </p>
              <h3 className="text-lg font-medium mt-4 mb-2">2.2 Platform Data</h3>
              <p className="text-surface-600 dark:text-surface-300">
                When you use the Mission Control platform, we collect operational data necessary to provide the Service. This includes infrastructure metrics, alert data, configuration data, agent telemetry, and log data from the servers and devices you connect to the platform. This data is processed on your behalf and is considered your data under applicable data protection laws.
              </p>
              <h3 className="text-lg font-medium mt-4 mb-2">2.3 Usage and Analytics Data</h3>
              <p className="text-surface-600 dark:text-surface-300">
                We automatically collect certain information when you visit our website or use the platform, including your IP address, browser type, operating system, referring URLs, pages visited, time spent on pages, and clickstream data. We use cookies and similar tracking technologies to collect this information.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">3. How We Use Your Information</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We use the information we collect for the following purposes: to provide, maintain, and improve the Service; to process transactions and send related information; to send administrative information such as product updates and security alerts; to respond to your inquiries and provide customer support; to monitor and analyze usage patterns and trends; to detect, prevent, and address technical issues and security threats; to comply with legal obligations; and to protect our rights and interests.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">4. Data Sharing and Disclosure</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We do not sell your personal information. We may share your information in the following circumstances: with service providers who perform services on our behalf (such as cloud infrastructure providers, payment processors, and analytics services); when required by law or to respond to legal process; to protect our rights, privacy, safety, or property; in connection with a merger, acquisition, or sale of assets; and with your explicit consent.
              </p>
              <p className="text-surface-600 dark:text-surface-300 mt-3">
                Platform data (the data you collect through the Mission Control platform from your infrastructure) is treated as confidential. We do not access, use, or share your platform data except as necessary to provide the Service or as required by law.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">5. Data Security</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We implement comprehensive technical and organizational measures to protect your information. These include TLS 1.3 encryption for all data in transit, AES-256 encryption for data at rest, regular security audits and penetration testing, access controls and authentication requirements, and continuous monitoring for unauthorized access. While we strive to protect your information, no method of transmission over the Internet is 100% secure, and we cannot guarantee absolute security.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">6. Data Retention</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We retain your personal information for as long as your account is active or as needed to provide the Service. We retain platform data in accordance with your account settings and applicable data retention policies. When you delete your account, we will delete or anonymize your personal information within 30 days, except where we are required to retain certain information for legal or legitimate business purposes.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">7. Your Rights</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Depending on your jurisdiction, you may have the following rights: access and receive a copy of your personal data, correct inaccurate or incomplete data, delete your personal data, restrict or object to the processing of your data, data portability, and withdraw consent at any time. To exercise any of these rights, please contact us at privacy@missioncontrol.io. We will respond to your request within 30 days.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">8. International Data Transfers</h2>
              <p className="text-surface-600 dark:text-surface-300">
                Your information may be transferred to and processed in countries other than your country of residence. We ensure that such transfers comply with applicable data protection laws and that appropriate safeguards are in place, including Standard Contractual Clauses (SCCs) approved by the European Commission where required.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">9. Cookies and Tracking Technologies</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We use essential cookies to operate the Service, analytics cookies to understand how the Service is used, and preference cookies to remember your settings. You can control cookie preferences through your browser settings. The Service does not respond to &quot;Do Not Track&quot; signals at this time.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">10. Children&apos;s Privacy</h2>
              <p className="text-surface-600 dark:text-surface-300">
                The Service is not intended for use by children under the age of 16. We do not knowingly collect personal information from children under 16. If you become aware that a child has provided us with personal information, please contact us so that we can take steps to delete such information.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">11. Changes to This Policy</h2>
              <p className="text-surface-600 dark:text-surface-300">
                We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on this page and updating the &quot;Last Updated&quot; date. We encourage you to review this policy periodically. Your continued use of the Service after any changes constitutes your acceptance of the new policy.
              </p>
            </div>

            <div>
              <h2 className="text-xl font-semibold mt-8 mb-3">12. Contact Us</h2>
              <p className="text-surface-600 dark:text-surface-300">
                If you have any questions about this Privacy Policy, please contact us at privacy@missioncontrol.io or write to: Mission Control, Data Protection Officer, [Address to be provided].
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
