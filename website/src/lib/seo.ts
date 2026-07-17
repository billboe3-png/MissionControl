import { siteConfig } from './site'

interface SEOProps {
  title?: string
  description?: string
  canonical?: string
  ogImage?: string
  ogType?: string
  twitterCard?: 'summary' | 'summary_large_image'
  noindex?: boolean
  breadcrumbs?: { name: string; item: string }[]
  publishedTime?: string
  modifiedTime?: string
  authors?: string[]
  tags?: string[]
}

export function generateMetadata({
  title,
  description,
  canonical,
  ogImage,
  ogType = 'website',
  twitterCard = 'summary_large_image',
  noindex = false,
  breadcrumbs,
  publishedTime,
  modifiedTime,
  authors,
  tags,
}: SEOProps = {}) {
  const fullTitle = title
    ? `${title} | ${siteConfig.name}`
    : `${siteConfig.name} | ${siteConfig.tagline}`

  const desc = description || siteConfig.description
  const url = canonical || siteConfig.url
  const image = ogImage || siteConfig.ogImage

  return {
    title: fullTitle,
    description: desc,
    ...(canonical && { alternates: { canonical: url } }),
    ...(!noindex && {
      robots: { index: true, follow: true },
    }),
    ...(noindex && {
      robots: { index: false, follow: false },
    }),
    openGraph: {
      title: fullTitle,
      description: desc,
      url,
      siteName: siteConfig.name,
      type: ogType,
      ...(image && {
        images: [
          {
            url: image,
            width: 1200,
            height: 630,
            alt: siteConfig.name,
          },
        ],
      }),
      ...(publishedTime && { publishedTime }),
      ...(modifiedTime && { modifiedTime }),
      ...(authors && { authors }),
      ...(tags && { tags }),
    },
    twitter: {
      card: twitterCard,
      title: fullTitle,
      description: desc,
      ...(image && { images: [image] }),
    },
    ...(breadcrumbs && {
      metadataBase: new URL(siteConfig.url),
    }),
  }
}

export function generateBreadcrumbStructuredData(
  items: { name: string; item: string }[]
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: `${siteConfig.url}${item.item}`,
    })),
  }
}

export function generateOrganizationStructuredData() {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: siteConfig.name,
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Linux, Windows, macOS',
    description: siteConfig.description,
    url: siteConfig.url,
    author: {
      '@type': 'Organization',
      name: siteConfig.author.name,
    },
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      description: 'Community Edition',
    },
  }
}
