import { Metadata } from 'next'
import Link from 'next/link'
import { Breadcrumb } from '@/components/layout/Breadcrumb'
import { generateMetadata } from '@/lib/seo'
import { MessageSquare, Github, Users, BookOpen, Lightbulb, Heart, ExternalLink } from 'lucide-react'

export const metadata: Metadata = generateMetadata({
  title: 'Community',
  description: 'Join the Mission Control community. Connect with other IT operations professionals, share knowledge, contribute plugins, and help shape the product roadmap.',
  canonical: '/community',
})

const channels = [
  {
    icon: MessageSquare,
    title: 'Community Forum',
    description: 'Ask questions, share tips, and discuss best practices with thousands of IT operations professionals.',
    link: '#',
    linkText: 'Visit Forum',
  },
  {
    icon: Github,
    title: 'GitHub',
    description: 'Browse the source code, report bugs, request features, and contribute pull requests.',
    link: 'https://github.com/missioncontrol',
    linkText: 'View Repository',
  },
  {
    icon: Users,
    title: 'Discord Server',
    description: 'Real-time chat with the Mission Control team and community members. Get quick answers and stay updated.',
    link: '#',
    linkText: 'Join Discord',
  },
]

const ways = [
  {
    icon: Lightbulb,
    title: 'Share Ideas',
    description: 'Submit feature requests and vote on community priorities. Your feedback directly influences our roadmap.',
  },
  {
    icon: BookOpen,
    title: 'Write Tutorials',
    description: 'Share your Mission Control expertise by writing guides, tutorials, and integration walkthroughs.',
  },
  {
    icon: Heart,
    title: 'Contribute Plugins',
    description: 'Build and publish community plugins that extend Mission Control with new integrations and capabilities.',
  },
]

const stats = [
  { value: '8,500+', label: 'Forum Members' },
  { value: '1,200+', label: 'GitHub Stars' },
  { value: '340+', label: 'Community Plugins' },
  { value: '24/7', label: 'Community Chat' },
]

export default function CommunityPage() {
  return (
    <>
      <Breadcrumb items={[{ label: 'Community' }]} />

      <section className="section">
        <div className="container-wide">
          <div className="text-center mb-16">
            <h1 className="section-title mb-4">
              <span className="gradient-text">Community</span>
            </h1>
            <p className="section-subtitle">
              Mission Control is built by and for the IT operations community. Join thousands of professionals who share knowledge, build integrations, and shape the future of the platform.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {stats.map((stat) => (
              <div key={stat.label} className="glass rounded-xl p-6 text-center">
                <div className="text-3xl font-bold gradient-text mb-1">{stat.value}</div>
                <div className="text-sm text-surface-500 dark:text-surface-400">{stat.label}</div>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {channels.map((channel) => (
              <div key={channel.title} className="glass rounded-xl p-8 card-hover text-center">
                <div className="w-12 h-12 rounded-lg bg-mc-100 dark:bg-mc-900/30 flex items-center justify-center mx-auto mb-4">
                  <channel.icon className="w-6 h-6 text-mc-600 dark:text-mc-400" />
                </div>
                <h3 className="text-lg font-semibold mb-3">{channel.title}</h3>
                <p className="text-surface-500 dark:text-surface-400 text-sm mb-6">
                  {channel.description}
                </p>
                <a
                  href={channel.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary inline-flex"
                >
                  {channel.linkText}
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            ))}
          </div>

          <div className="mb-16">
            <h2 className="text-2xl font-bold text-center mb-8">Ways to Contribute</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {ways.map((way) => (
                <div key={way.title} className="glass rounded-xl p-6 card-hover">
                  <way.icon className="w-8 h-8 text-mc-600 dark:text-mc-400 mb-3" />
                  <h3 className="font-semibold mb-2">{way.title}</h3>
                  <p className="text-sm text-surface-500 dark:text-surface-400">{way.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-xl p-12 text-center bg-gradient-to-br from-mc-500/10 to-mc-700/10">
            <h2 className="text-2xl font-bold mb-4">Join the Conversation</h2>
            <p className="text-surface-500 dark:text-surface-400 mb-8 max-w-xl mx-auto">
              Whether you are a seasoned operations engineer or just getting started, there is a place for you in the Mission Control community.
            </p>
            <Link href="/contact" className="btn-primary">
              Get Involved
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
