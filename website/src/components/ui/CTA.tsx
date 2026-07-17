import Link from 'next/link'
import { ArrowRight, Download } from 'lucide-react'
import { siteConfig } from '@/lib/site'

interface CTAProps {
  title?: string
  subtitle?: string
}

export function CTA({
  title = 'Ready to Transform Your IT Operations?',
  subtitle = 'Join thousands of organizations using Mission Control to manage their infrastructure. Start for free with the Community edition or request a personalized Enterprise demo.',
}: CTAProps) {
  return (
    <section className="section">
      <div className="container-wide">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-mc-600 via-mc-700 to-mc-800 px-8 py-16 sm:px-16 sm:py-20 text-center">
          <div className="absolute inset-0 bg-[url('/images/grid.svg')] opacity-10" />
          <div className="relative z-10">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 text-balance">
              {title}
            </h2>
            <p className="text-lg text-mc-100 max-w-2xl mx-auto mb-8">
              {subtitle}
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href={siteConfig.links.download}
                className="btn bg-white text-mc-700 hover:bg-mc-50 shadow-lg shadow-black/20 font-semibold"
              >
                <Download className="w-5 h-5" />
                Download Free
              </Link>
              <Link
                href="/contact"
                className="btn border-2 border-white/30 text-white hover:bg-white/10 font-semibold"
              >
                Request Demo
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
