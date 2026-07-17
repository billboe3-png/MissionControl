import Link from 'next/link'
import { siteConfig } from '@/lib/site'
import { mainNavigation } from '@/data/navigation'

const footerLinks = {
  Product: [
    { label: 'Features', href: '/features' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Downloads', href: '/downloads' },
    { label: 'Roadmap', href: '/roadmap' },
    { label: 'Release Notes', href: '/release-notes' },
  ],
  Solutions: [
    { label: 'Enterprise', href: '/solutions/enterprise' },
    { label: 'MSP', href: '/solutions/msp' },
    { label: 'Education', href: '/solutions/education' },
    { label: 'Government', href: '/solutions/government' },
    { label: 'Healthcare', href: '/solutions/healthcare' },
  ],
  Resources: [
    { label: 'Documentation', href: '/documentation' },
    { label: 'Blog', href: '/blog' },
    { label: 'Case Studies', href: '/case-studies' },
    { label: 'Knowledge Base', href: '/knowledge-base' },
    { label: 'API Reference', href: '/api-reference' },
  ],
  Company: [
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
    { label: 'Partners', href: '/partners' },
    { label: 'Community', href: '/community' },
    { label: 'Support', href: '/support' },
  ],
  Legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
    { label: 'Security', href: '/security' },
    { label: 'Trust Center', href: '/trust-center' },
  ],
}

export function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-surface-50 dark:bg-surface-950">
      <div className="container-wide py-16">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
          <div className="col-span-2 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-mc-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">MC</span>
              </div>
              <span className="font-bold text-lg">{siteConfig.name}</span>
            </Link>
            <p className="text-sm text-surface-500 dark:text-surface-400 mb-4 max-w-xs">
              {siteConfig.description}
            </p>
            <div className="flex gap-3">
              <a
                href={siteConfig.links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 transition-colors"
                aria-label="GitHub"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              </a>
              <a
                href={siteConfig.links.twitter}
                target="_blank"
                rel="noopener noreferrer"
                className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 transition-colors"
                aria-label="Twitter"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              </a>
            </div>
          </div>

          {Object.entries(footerLinks).map(([group, links]) => (
            <div key={group}>
              <h3 className="font-semibold text-sm mb-3 text-surface-900 dark:text-surface-100">
                {group}
              </h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-surface-400">
            &copy; {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-sm text-surface-400">
            <Link href="/privacy" className="hover:text-surface-600 dark:hover:text-surface-300">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-surface-600 dark:hover:text-surface-300">
              Terms
            </Link>
            <Link href="/security" className="hover:text-surface-600 dark:hover:text-surface-300">
              Security
            </Link>
            <Link href="/status" className="hover:text-surface-600 dark:hover:text-surface-300">
              Status
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
