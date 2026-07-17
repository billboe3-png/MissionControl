'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X, ChevronDown } from 'lucide-react'
import { mainNavigation } from '@/data/navigation'
import { siteConfig } from '@/lib/site'
import { ThemeToggle } from './ThemeToggle'

export function Navigation() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [openDropdown, setOpenDropdown] = useState<string | null>(null)

  const primaryItems = mainNavigation.slice(0, 8)
  const secondaryItems = mainNavigation.slice(8)

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-gray-200/50 dark:border-gray-800/50">
      <nav className="container-wide">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-mc-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">MC</span>
            </div>
            <span className="font-bold text-lg hidden sm:block">{siteConfig.name}</span>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            {primaryItems.map((item) => (
              <div
                key={item.href}
                className="relative"
                onMouseEnter={() => item.children && setOpenDropdown(item.label)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                <Link
                  href={item.href}
                  className="px-3 py-2 text-sm font-medium text-surface-600 dark:text-surface-300 hover:text-surface-900 dark:hover:text-white rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors flex items-center gap-1"
                >
                  {item.label}
                  {item.children && (
                    <ChevronDown className={`w-3.5 h-3.5 transition-transform ${openDropdown === item.label ? 'rotate-180' : ''}`} />
                  )}
                </Link>
                {item.children && openDropdown === item.label && (
                  <div className="absolute top-full left-0 mt-1 w-56 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 shadow-xl shadow-black/5 py-2 z-50">
                    {item.children.map((child) => (
                      <Link
                        key={child.href}
                        href={child.href}
                        className="block px-4 py-2 text-sm text-surface-600 dark:text-surface-300 hover:text-surface-900 dark:hover:text-white hover:bg-surface-50 dark:hover:bg-surface-800"
                      >
                        {child.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Link href="/downloads" className="btn-primary text-sm py-2 px-4 hidden sm:inline-flex">
              Download
            </Link>
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </nav>

      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 max-h-[80vh] overflow-y-auto">
          <div className="container-wide py-4 space-y-1">
            {mainNavigation.map((item) => (
              <div key={item.href}>
                <Link
                  href={item.href}
                  className="block px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800"
                  onClick={() => setMobileOpen(false)}
                >
                  {item.label}
                </Link>
                {item.children && (
                  <div className="ml-4 space-y-1 pb-2">
                    {item.children.map((child) => (
                      <Link
                        key={child.href}
                        href={child.href}
                        className="block px-3 py-2 text-sm text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white rounded-lg hover:bg-surface-50 dark:hover:bg-surface-800"
                        onClick={() => setMobileOpen(false)}
                      >
                        {child.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div className="pt-4">
              <Link href="/downloads" className="btn-primary w-full text-center" onClick={() => setMobileOpen(false)}>
                Download
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
