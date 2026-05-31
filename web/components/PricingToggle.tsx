'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Check } from 'lucide-react'

type Interval = 'maand' | 'jaar'

interface Plan {
  name: string
  price: number            // €/maand bij maandelijkse facturatie
  priceAnnual: number      // €/maand bij jaarlijkse facturatie (≈ 2 maanden gratis)
  desc: string
  features: string[]
  popular: boolean
  whitelabel?: boolean
}

const PLANS: Plan[] = [
  {
    name: 'Starter',
    price: 49,
    priceAnnual: 41,
    desc: 'Voor zelfstandigen die hun eigen WhatsApp willen automatiseren.',
    features: ['Jouw bedrijf (1 WhatsApp-nummer)', '200 gesprekken/maand', 'Airtable CRM', 'E-mail support'],
    popular: false,
  },
  {
    name: 'Groei',
    price: 99,
    priceAnnual: 83,
    desc: 'Voor bedrijven met meerdere medewerkers of hogere leadvolumes.',
    features: ['Tot 5 WhatsApp-nummers', '500 gesprekken/maand', 'Airtable CRM', 'Afspraken module', 'Prioriteit support'],
    popular: true,
  },
  {
    name: 'Agency',
    price: 199,
    priceAnnual: 166,
    desc: 'Voor agencies of partners die meerdere klanten beheren.',
    features: ['Onbeperkt klanten', 'Onbeperkt gesprekken', 'Airtable (HubSpot komt Q3 2026)', 'Dedicated support', 'White-label'],
    popular: false,
    whitelabel: true,
  },
]

export default function PricingToggle() {
  const [interval, setInterval] = useState<Interval>('maand')
  const jaarlijks = interval === 'jaar'

  return (
    <div>
      {/* Maand / Jaar toggle */}
      <div className="mb-10 flex items-center justify-center">
        <div className="inline-flex items-center rounded-full border border-gray-200 bg-white p-1 shadow-sm">
          {(['maand', 'jaar'] as Interval[]).map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => setInterval(opt)}
              className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                interval === opt ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {opt === 'maand' ? 'Maandelijks' : 'Jaarlijks'}
              {opt === 'jaar' && (
                <span className={`ml-1.5 ${interval === 'jaar' ? 'text-indigo-100' : 'text-green-600'}`}>
                  −2 mnd
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 sm:grid-cols-3">
        {PLANS.map((plan) => {
          const shownPrice = jaarlijks ? plan.priceAnnual : plan.price
          return (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl p-6 shadow-sm ${
                plan.popular
                  ? 'border-2 border-indigo-600 bg-white ring-4 ring-indigo-50'
                  : 'border border-gray-200 bg-white'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-indigo-600 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
                    Meest gekozen
                  </span>
                </div>
              )}
              <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
              <p className="mt-1 text-sm text-gray-500 leading-snug">{plan.desc}</p>
              <div className="mt-3 inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-semibold text-green-700 ring-1 ring-green-200">
                ✨ 7 dagen gratis proberen
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-gray-900">€{shownPrice}</span>
                <span className="text-sm text-gray-400">/maand excl. btw</span>
              </div>
              <p className="mt-1 h-4 text-xs font-medium text-green-600">
                {jaarlijks ? 'Jaarlijks gefactureerd · 2 maanden gratis' : ' '}
              </p>
              <ul className="my-6 flex-1 space-y-2.5">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
                    {f}
                  </li>
                ))}
              </ul>
              {plan.whitelabel && (
                <p className="-mt-3 mb-4 text-xs leading-snug text-gray-400">
                  <span className="font-semibold text-gray-500">White-label:</span> bied Repto aan onder je
                  eigen merknaam — jouw klanten zien enkel jouw logo.
                </p>
              )}
              <Link
                href="/sign-up"
                className={`w-full rounded-xl py-3 text-center text-sm font-semibold transition-colors ${
                  plan.popular
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                7 dagen gratis starten →
              </Link>
            </div>
          )
        })}
      </div>

      {/* Eén discrete vermelding i.p.v. 3× herhaald */}
      <p className="mt-6 text-center text-xs text-gray-400">
        Betaalmethode vereist na de gratis periode · opzeggen kan op elk moment.
      </p>
    </div>
  )
}
