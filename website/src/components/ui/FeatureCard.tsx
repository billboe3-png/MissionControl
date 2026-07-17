import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  icon: LucideIcon
  title: string
  description: string
  href: string
}

export function FeatureCard({ icon: Icon, title, description, href }: FeatureCardProps) {
  return (
    <Link
      href={href}
      className="group block p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover"
    >
      <div className="w-12 h-12 rounded-lg bg-mc-50 dark:bg-mc-500/10 flex items-center justify-center mb-4 group-hover:bg-mc-100 dark:group-hover:bg-mc-500/20 transition-colors">
        <Icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
      </div>
      <h3 className="text-lg font-semibold mb-2 group-hover:text-mc-600 dark:group-hover:text-mc-400 transition-colors">
        {title}
      </h3>
      <p className="text-sm text-surface-500 dark:text-surface-400 leading-relaxed mb-4">
        {description}
      </p>
      <span className="inline-flex items-center gap-1 text-sm font-medium text-mc-600 dark:text-mc-400 group-hover:gap-2 transition-all">
        Learn more <ChevronRight className="w-4 h-4" />
      </span>
    </Link>
  )
}
