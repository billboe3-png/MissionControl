import { trustedTechnologies } from '@/data/content'

export function TechnologyGrid() {
  return (
    <section className="section">
      <div className="container-wide">
        <div className="text-center mb-12">
          <p className="text-sm font-semibold text-mc-600 dark:text-mc-400 uppercase tracking-wider mb-2">
            Trusted Technologies
          </p>
          <h2 className="section-title">
            Built for the <span className="gradient-text">Modern Stack</span>
          </h2>
          <p className="section-subtitle mt-4">
            Mission Control integrates seamlessly with the tools and platforms your team already uses.
          </p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {trustedTechnologies.map((tech) => (
            <div
              key={tech.name}
              className="flex flex-col items-center justify-center p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-surface-900 card-hover"
            >
              <div className="w-12 h-12 rounded-lg bg-surface-100 dark:bg-surface-800 flex items-center justify-center mb-3">
                <span className="text-xl font-bold text-surface-400 dark:text-surface-500">
                  {tech.name.charAt(0)}
                </span>
              </div>
              <span className="text-sm font-medium text-center">{tech.name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
