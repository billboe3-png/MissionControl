import Link from 'next/link'
import { Check } from 'lucide-react'

interface PricingCardProps {
  name: string
  price: string
  period?: string
  description: string
  features: string[]
  cta: string
  href: string
  featured?: boolean
}

export function PricingCard({
  name,
  price,
  period,
  description,
  features,
  cta,
  href,
  featured = false,
}: PricingCardProps) {
  return (
    <div
      className={`relative flex flex-col p-8 rounded-2xl border ${
        featured
          ? 'border-mc-500 shadow-xl shadow-mc-500/10 scale-[1.02] bg-white dark:bg-surface-900'
          : 'border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900'
      }`}
    >
      {featured && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="bg-mc-600 text-white text-xs font-semibold px-4 py-1.5 rounded-full">
            Most Popular
          </span>
        </div>
      )}

      <div className="mb-6">
        <h3 className="text-xl font-bold mb-1">{name}</h3>
        <p className="text-sm text-surface-500 dark:text-surface-400">{description}</p>
      </div>

      <div className="mb-6">
        <span className="text-4xl font-bold">{price}</span>
        {period && (
          <span className="text-surface-500 dark:text-surface-400 text-sm ml-1">{period}</span>
        )}
      </div>

      <ul className="space-y-3 mb-8 flex-1">
        {features.map((feature) => (
          <li key={feature} className="flex items-start gap-3">
            <Check className="w-5 h-5 text-mc-500 shrink-0 mt-0.5" />
            <span className="text-sm text-surface-600 dark:text-surface-300">{feature}</span>
          </li>
        ))}
      </ul>

      <Link
        href={href}
        className={featured ? 'btn-primary w-full text-center' : 'btn-outline w-full text-center'}
      >
        {cta}
      </Link>
    </div>
  )
}
