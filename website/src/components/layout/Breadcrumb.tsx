import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  href?: string
}

export function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav aria-label="Breadcrumb" className="container-wide pt-24 pb-4">
      <ol className="flex items-center gap-1.5 text-sm text-surface-500 dark:text-surface-400">
        <li>
          <Link href="/" className="hover:text-surface-700 dark:hover:text-surface-200 transition-colors">
            <Home className="w-4 h-4" />
          </Link>
        </li>
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-1.5">
            <ChevronRight className="w-3.5 h-3.5" />
            {item.href ? (
              <Link
                href={item.href}
                className="hover:text-surface-700 dark:hover:text-surface-200 transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-surface-900 dark:text-surface-100 font-medium" aria-current="page">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
