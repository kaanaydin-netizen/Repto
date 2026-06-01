'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

const ACK_KEY = 'repto_cookie_ack'

/**
 * Eenvoudige cookie-info-banner. Repto gebruikt enkel functionele cookies
 * (Clerk-sessie + beveiliging), dus geen accept/weiger-keuze nodig — alleen
 * informeren conform de AVG. De bevestiging wordt in localStorage bewaard zodat
 * de banner daarna niet meer verschijnt.
 */
export default function CookieBanner() {
  // Start verborgen; pas na de mount bepalen we of de banner moet verschijnen,
  // zodat er geen flits is bij gebruikers die al akkoord gingen (SSR-safe).
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    try {
      if (!localStorage.getItem(ACK_KEY)) setVisible(true)
    } catch {
      // localStorage niet beschikbaar (privémodus) — toon dan toch de banner.
      setVisible(true)
    }
  }, [])

  function dismiss() {
    try {
      localStorage.setItem(ACK_KEY, '1')
    } catch {
      /* negeren */
    }
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 px-4 pb-4">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-3 rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-lg sm:flex-row">
        <p className="flex-1 text-center text-sm text-gray-600 sm:text-left">
          Repto gebruikt enkel <strong className="font-semibold text-gray-800">functionele cookies</strong>{' '}
          voor login en beveiliging — geen tracking of advertenties.{' '}
          <Link href="/privacy" className="font-medium text-indigo-600 hover:underline">
            Meer info
          </Link>
        </p>
        <button
          type="button"
          onClick={dismiss}
          className="shrink-0 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
        >
          Oké
        </button>
      </div>
    </div>
  )
}
