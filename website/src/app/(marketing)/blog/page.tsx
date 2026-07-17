import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { blogPosts } from '@/data/content'
import { Calendar, User, Tag, ArrowRight } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Blog',
  description: 'Insights, tutorials, and updates from the Mission Control team. Learn about IT operations best practices, product releases, and industry trends.',
  canonical: '/blog',
})

export default function BlogPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Blog' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Blog</span>
            </h1>
            <p className="section-subtitle">
              Technical deep-dives, product updates, and best practices from the Mission Control engineering team.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {blogPosts.map((post, index) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className={`glass rounded-xl overflow-hidden card-hover group ${
                  index === 0 ? 'md:col-span-2' : ''
                }`}
              >
                {index === 0 && (
                  <div className="aspect-[21/9] bg-gradient-to-br from-mc-500 to-mc-700 relative">
                    <div className="absolute inset-0 flex items-center justify-center text-white/20 text-8xl font-bold">
                      MC
                    </div>
                  </div>
                )}
                <div className="p-6">
                  <div className="flex flex-wrap gap-2 mb-3">
                    {post.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2.5 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 text-xs font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <h2 className={`font-semibold mb-2 group-hover:text-mc-600 dark:group-hover:text-mc-400 transition-colors ${
                    index === 0 ? 'text-2xl' : 'text-lg'
                  }`}>
                    {post.title}
                  </h2>
                  <p className="text-surface-500 dark:text-surface-400 text-sm mb-4 line-clamp-2">
                    {post.excerpt}
                  </p>
                  <div className="flex items-center justify-between text-xs text-surface-400">
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5" />
                        {post.author}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {new Date(post.date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
