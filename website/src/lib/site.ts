export const siteConfig = {
  name: 'Mission Control',
  tagline: 'Enterprise IT Operations Platform',
  description:
    'Mission Control is a unified IT operations platform that combines monitoring, infrastructure management, automation, AI-assisted operations, remote administration, and a plugin ecosystem into a single operational workspace.',
  url: 'https://missioncontrol.io',
  ogImage: '/images/og-default.jpg',
  links: {
    github: 'https://github.com/missioncontrol',
    docs: 'https://docs.missioncontrol.io',
    demo: 'https://demo.missioncontrol.io',
    download: '/downloads',
    status: '/status',
    twitter: 'https://twitter.com/missioncontrol',
  },
  author: {
    name: 'Mission Control Team',
    email: 'hello@missioncontrol.io',
    twitter: '@missioncontrol',
  },
}

export type SiteConfig = typeof siteConfig
