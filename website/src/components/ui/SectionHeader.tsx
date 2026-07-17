interface SectionHeaderProps {
  title: string
  subtitle?: string
  centered?: boolean
  className?: string
}

export function SectionHeader({
  title,
  subtitle,
  centered = true,
  className = '',
}: SectionHeaderProps) {
  return (
    <div
      className={`mb-12 sm:mb-16 ${
        centered ? 'text-center' : ''
      } ${className}`}
    >
      <h2 className="section-title gradient-text">{title}</h2>
      {subtitle && <p className="section-subtitle mt-4">{subtitle}</p>}
    </div>
  )
}
