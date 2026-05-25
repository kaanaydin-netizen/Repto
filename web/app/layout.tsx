import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { nlBE } from '@clerk/localizations'
import './globals.css'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Repto — AI-Receptionist',
  description: "WhatsApp automatisering voor KMO's",
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
