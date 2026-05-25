import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { nlBE } from '@clerk/localizations'
import './globals.css'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'Repto — AI-Receptionist voor KMO\'s',
    template: '%s — Repto',
  },
  description:
    'Repto beantwoordt automatisch WhatsApp-berichten van klanten, verzamelt leaddata en synchroniseert naar je CRM. Nooit een offerte-aanvraag meer missen.',
  keywords: [
    'WhatsApp AI',
    'receptionist',
    'KMO',
    'zelfstandige',
    'leads',
    'CRM',
    'automatisering',
    'Belgie',
    'Nederland',
    'Airtable',
  ],
  authors: [{ name: 'Repto' }],
  creator: 'Repto',
  metadataBase: new URL('https://repto-three.vercel.app'),
  openGraph: {
    type: 'website',
    locale: 'nl_BE',
    url: 'https://repto-three.vercel.app',
    siteName: 'Repto',
    title: 'Repto — Mis geen enkele offerte-aanvraag meer via WhatsApp',
    description:
      'AI-receptionist die automatisch WhatsApp-berichten beantwoordt, leads verzamelt en naar Airtable stuurt. 7 dagen gratis proberen.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Repto — AI-Receptionist voor KMO\'s',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Repto — AI-Receptionist voor KMO\'s',
    description: 'Mis geen enkele offerte-aanvraag meer via WhatsApp.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider localization={nlBE}>
      <html lang="nl">
        <body className={`${geist.className} bg-gray-50 antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}
