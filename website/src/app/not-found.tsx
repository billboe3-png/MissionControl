import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, Home } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Page Not Found',
  description: 'The page you are looking for does not exist or has been moved.',
  robots: { index: false, follow: false },
}

export default function NotFound() {
  return (
    <section className="min-h-[80vh] flex items-center justify-center">
      <div className="text-center px-4">
        <div className="mb-8">
          <span className="text-[10rem] sm:text-[12rem] font-bold leading-none gradient-text opacity-20 select-none">
            404
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-4">Page Not Found</h1>
        <p className="text-surface-500 dark:text-surface-400 text-lg mb-8 max-w-md mx-auto">
          The page you are looking for does not exist, has been moved, or is temporarily unavailable.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link href="/" className="btn-primary">
            <Home className="w-4 h-4" />
            Go Home
          </Link>
          <Link href="/documentation" className="btn-secondary">
            <ArrowLeft className="w-4 h-4" />
            Documentation
          </Link>
        </div>
      </div>
    </section>
  )
}
