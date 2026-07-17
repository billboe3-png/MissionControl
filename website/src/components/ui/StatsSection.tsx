import { stats } from '@/data/content'

export function StatsSection() {
  return (
    <section className="section bg-surface-50 dark:bg-surface-900/50">
      <div className="container-wide">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl sm:text-4xl lg:text-5xl font-bold gradient-text mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-surface-500 dark:text-surface-400 font-medium">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
