# Mission Control Website

Enterprise IT Operations Platform — marketing website built with Next.js, TypeScript, and Tailwind CSS.

## Tech Stack

- **Next.js** 14 (App Router)
- **TypeScript**
- **Tailwind CSS** 3
- **Framer Motion** (animations)
- **Lucide React** (icons)
- **next-sitemap** (SEO)
- **next-mdx-remote** (MDX content)

## Getting Started

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Static export (GitHub Pages, etc.)
npm run export

# Generate sitemap
npm run postbuild
```

## Project Structure

```
website/
├── public/
│   ├── robots.txt
│   ├── manifest.json
│   ├── favicon.svg
│   ├── icon.svg
│   └── apple-touch-icon.svg
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout (SEO metadata, ThemeProvider, Nav, Footer)
│   │   ├── page.tsx                # Home page
│   │   ├── not-found.tsx           # 404 page
│   │   └── (marketing)/
│   │       ├── features/           # 20+ feature pages
│   │       │   ├── (pages)/
│   │       │   │   ├── dashboard/
│   │       │   │   ├── infrastructure/
│   │       │   │   ├── monitoring/
│   │       │   │   ├── zabbix/
│   │       │   │   ├── hyper-v/
│   │       │   │   ├── proxmox/
│   │       │   │   ├── docker/
│   │       │   │   ├── active-directory/
│   │       │   │   ├── office-365/
│   │       │   │   ├── remote-operations/
│   │       │   │   ├── automation/
│   │       │   │   ├── playbooks/
│   │       │   │   ├── mc-agent/
│   │       │   │   ├── ai-operations/
│   │       │   │   ├── plugin-framework/
│   │       │   │   ├── multi-tenant/
│   │       │   │   ├── multi-site/
│   │       │   │   ├── reporting/
│   │       │   │   ├── credential-vault/
│   │       │   │   └── rest-api/
│   │       │   └── page.tsx        # Features overview
│   │       ├── solutions/          # 8 solution pages
│   │       │   ├── enterprise/
│   │       │   ├── msp/
│   │       │   ├── education/
│   │       │   ├── government/
│   │       │   ├── healthcare/
│   │       │   ├── finance/
│   │       │   ├── manufacturing/
│   │       │   ├── small-business/
│   │       │   └── page.tsx
│   │       ├── architecture/       # Architecture page
│   │       ├── documentation/      # Documentation landing
│   │       ├── downloads/          # Downloads page
│   │       ├── roadmap/            # Interactive roadmap
│   │       ├── blog/               # Blog listing + posts
│   │       ├── release-notes/      # Release notes
│   │       ├── pricing/            # Pricing plans
│   │       ├── partners/           # Partner program
│   │       ├── case-studies/       # Case studies
│   │       ├── knowledge-base/     # Knowledge base
│   │       ├── api-reference/      # API reference
│   │       ├── community/          # Community page
│   │       ├── support/            # Support page
│   │       ├── security/           # Security details
│   │       ├── trust-center/       # Trust center
│   │       ├── status/             # System status
│   │       ├── about/              # About us
│   │       ├── contact/            # Contact page
│   │       ├── privacy/            # Privacy policy
│   │       └── terms/              # Terms of service
│   ├── components/
│   │   ├── layout/                 # Navigation, Footer, ThemeProvider, Breadcrumb, ThemeToggle
│   │   ├── ui/                     # SectionHeader, FeatureCard, PricingCard, CTA, StatsSection, TechnologyGrid
│   │   ├── marketing/              # Hero
│   │   └── illustrations/         # (ready for custom illustrations)
│   ├── lib/
│   │   ├── site.ts                 # Site config
│   │   └── seo.ts                  # SEO metadata generator
│   ├── data/
│   │   ├── navigation.ts          # Navigation structure
│   │   ├── features.ts            # Feature definitions
│   │   └── content.ts             # Content data (blog, pricing, roadmap, etc.)
│   └── styles/
│       └── globals.css            # Global styles + Tailwind
└── next.config.js
└── tailwind.config.js
└── tsconfig.json
└── package.json
```

## Pages (45 total)

| Route | Description |
|-------|-------------|
| `/` | Home page with hero, features, stats, roadmap, blog, pricing |
| `/features` | All features overview |
| `/features/{name}` | 20 individual feature pages |
| `/solutions` | Solutions overview |
| `/solutions/{name}` | 8 industry/vertical solution pages |
| `/architecture` | System architecture diagram |
| `/documentation` | Documentation landing |
| `/downloads` | Download options |
| `/roadmap` | Interactive product roadmap |
| `/blog` | Blog listing |
| `/blog/{slug}` | Individual blog posts |
| `/pricing` | Pricing plans |
| `/release-notes` | Version history |
| `/partners` | Partner program |
| `/case-studies` | Customer case studies |
| `/knowledge-base` | Knowledge base |
| `/api-reference` | API documentation |
| `/community` | Community hub |
| `/support` | Support options |
| `/security` | Security posture |
| `/trust-center` | Trust and compliance |
| `/status` | System status |
| `/about` | About the company |
| `/contact` | Contact form |
| `/privacy` | Privacy policy |
| `/terms` | Terms of service |

## SEO Features

- **Meta Titles & Descriptions** — Every page via `generateMetadata()`
- **OpenGraph** — Title, description, images, type
- **Twitter Cards** — Summary large image
- **JSON-LD** — Organization/SoftwareApplication schema + BreadcrumbList
- **Canonical URLs** — All pages
- **robots.txt** — SEO-optimized
- **sitemap.xml** — Auto-generated via next-sitemap
- **Semantic HTML** — ARIA labels, landmarks, heading hierarchy
- **Breadcrumbs** — Structured navigation with schema.org markup

## Deployment

### Vercel (recommended)

```bash
npm i -g vercel
vercel
```

### Netlify

```bash
npm run export
# Deploy the `out/` directory
```

### Cloudflare Pages

```bash
npm run export
# Deploy the `out/` directory
```

### GitHub Pages

```bash
npm run export
# Deploy the `out/` directory to gh-pages branch
```

### Docker

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["npm", "start"]
```

## Lighthouse Targets

| Category | Target |
|----------|--------|
| Performance | 95+ |
| Accessibility | 100 |
| Best Practices | 100 |
| SEO | 100 |

## Dark Mode

Supports light, dark, and system-preference modes with smooth transitions.

## License

Proprietary — All rights reserved.
