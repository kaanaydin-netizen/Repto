'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Menu, X, ArrowRight } from 'lucide-react'

const LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#voorbeeld', label: 'Voorbeeld' },
  { href: '#hoe-werkt-het', label: 'Hoe het werkt' },
  { href: '#prijzen', label: 'Prijzen' },
  { href: '#faq', label: 'FAQ' },
  { href: '/contact', label: 'Contact' },
]

/**
 * Mobiel hamburger-menu. Alleen zichtbaar onder de `sm`-breakpoint;
 * de desktop-nav in de header blijft ongewijzigd (`hidden sm:flex`).
 */
export default function MobileNav() {
  const [open, setOpen] = useState(false)

  // Voorkom scrollen van de achtergrond wanneer het menu open is.
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <div className="sm:hidden">
      <button
        type="button"
        aria-label={open ? 'Menu sluiten' : 'Menu openen'}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-700 hover:bg-gray-100"
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {open && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 top-16 z-40 bg-black/20"
            onClick={() => setOpen(false)}
          />
          {/* Uitklap-paneel */}
          <nav className="fixed inset-x-0 top-16 z-50 border-b border-gray-100 bg-white px-6 py-4 shadow-lg">
            <div className="flex flex-col gap-1">
              {LINKS.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-base font-medium text-gray-700 hover:bg-gray-50"
                >
                  {l.label}
                </a>
              ))}
              <div className="my-2 h-px bg-gray-100" />
              <Link
                href="/sign-in"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-base font-medium text-gray-700 hover:bg-gray-50"
              >
                Aanmelden
              </Link>
              <Link
                href="/sign-up"
                onClick={() => setOpen(false)}
                className="mt-1 flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-3 text-base font-semibold text-white shadow-sm hover:bg-indigo-700"
              >
                Gratis starten <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </nav>
        </>
      )}
    </div>
  )
}
