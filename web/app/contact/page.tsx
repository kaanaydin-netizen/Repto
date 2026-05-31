'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Zap, Check } from 'lucide-react'

type Status = 'idle' | 'sending' | 'success' | 'error'

const DIRECT_EMAIL = 'Info@repto.be'

export default function ContactPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string>('')

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setStatus('sending')
    setError('')

    const form = e.currentTarget
    const data = {
      name: (form.elements.namedItem('name') as HTMLInputElement).value,
      email: (form.elements.namedItem('email') as HTMLInputElement).value,
      message: (form.elements.namedItem('message') as HTMLTextAreaElement).value,
      company: (form.elements.namedItem('company') as HTMLInputElement).value, // honeypot
    }

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      const body = await res.json().catch(() => ({}))

      if (res.ok) {
        setStatus('success')
        form.reset()
        return
      }

      if (body?.error === 'not_configured') {
        setError(
          `Onze online verzending is nog niet actief. Mail ons rechtstreeks op ${DIRECT_EMAIL}.`,
        )
      } else {
        setError(body?.error ?? 'Er ging iets mis. Probeer het later opnieuw.')
      }
      setStatus('error')
    } catch {
      setError('Er ging iets mis. Probeer het later opnieuw.')
      setStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">Repto</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            <span aria-hidden="true">←</span> Terug naar home
          </Link>
        </div>
      </header>

      {/* Inhoud */}
      <section className="relative overflow-hidden py-16 sm:py-24">
        <div className="pointer-events-none absolute inset-0 -top-40 bg-gradient-to-br from-indigo-50 via-white to-white" />

        <div className="relative mx-auto max-w-xl px-6">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
              Een vraag over Repto?
            </h1>
            <p className="mt-3 text-lg text-gray-500">
              Laat hieronder je gegevens achter — we antwoorden meestal binnen één werkdag.
              Of mail rechtstreeks naar{' '}
              <a href={`mailto:${DIRECT_EMAIL}`} className="font-medium text-indigo-600 hover:underline">
                {DIRECT_EMAIL}
              </a>
              .
            </p>
          </div>

          {status === 'success' ? (
            <div className="flex flex-col items-center gap-4 rounded-2xl border border-green-200 bg-green-50 px-8 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-500">
                <Check className="h-7 w-7 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Bedankt voor je bericht!</h2>
              <p className="text-gray-600">
                We hebben je vraag goed ontvangen en nemen zo snel mogelijk contact met je op.
              </p>
              <Link
                href="/"
                className="mt-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                Terug naar de website
              </Link>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8"
            >
              {/* Honeypot — verborgen voor mensen, val voor bots */}
              <input
                type="text"
                name="company"
                tabIndex={-1}
                autoComplete="off"
                className="hidden"
                aria-hidden="true"
              />

              <div className="space-y-5">
                <div>
                  <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-gray-700">
                    Naam
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    placeholder="Jouw naam"
                    className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-gray-700">
                    E-mailadres
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    placeholder="jij@bedrijf.be"
                    className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </div>

                <div>
                  <label htmlFor="message" className="mb-1.5 block text-sm font-medium text-gray-700">
                    Je vraag
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    required
                    rows={5}
                    placeholder="Waarmee kunnen we je helpen?"
                    className="w-full resize-y rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </div>

                {status === 'error' && (
                  <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    <span aria-hidden="true" className="mt-0.5 font-bold">!</span>
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={status === 'sending'}
                  className="w-full rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {status === 'sending' ? 'Versturen…' : 'Verstuur vraag'}
                </button>

                <p className="text-center text-xs text-gray-400">
                  We gebruiken je gegevens enkel om je vraag te beantwoorden.
                </p>
              </div>
            </form>
          )}
        </div>
      </section>
    </div>
  )
}
