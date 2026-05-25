/**
 * /onboarding — welkomstpagina voor nieuwe Repto-gebruikers.
 * Toont na sign-up, vóór het dashboard.
 * Staat BUITEN de (app) groep zodat de sidebar-layout niet van toepassing is.
 */
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { Zap, MessageSquare, Database, Bot, ArrowRight, Check } from 'lucide-react'

export const metadata = { title: 'Welkom bij Repto' }
export const dynamic = 'force-dynamic'

export default async function OnboardingPage() {
  // Auth check
  let userId: string | null = null
  try {
    const r = await auth()
    userId = r.userId
  } catch {
    redirect('/sign-in')
  }
  if (!userId) redirect('/sign-in')

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">Repto</span>
        </div>
      </header>

      {/* Content */}
      <div className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">

        {/* Welkom */}
        <div className="mb-12 text-center">
          <div className="mb-4 text-5xl">🎉</div>
          <h1 className="text-3xl font-extrabold text-gray-900">
            Welkom bij Repto!
          </h1>
          <p className="mt-3 text-lg text-gray-500">
            Je account is aangemaakt. Voeg nu je eerste klant toe om van start te gaan.
          </p>
        </div>

        {/* Hoe het werkt — 3 stappen */}
        <div className="mb-10 grid gap-4 sm:grid-cols-3">
          {[
            {
              icon: MessageSquare,
              step: '1',
              title: 'Klant toevoegen',
              desc: 'Vul bedrijfsnaam, sector en WhatsApp-nummer in.',
              color: 'bg-indigo-50 text-indigo-600',
            },
            {
              icon: Bot,
              step: '2',
              title: 'AI configureren',
              desc: 'Kies toon en voeg bedrijfsinstructies toe.',
              color: 'bg-violet-50 text-violet-600',
            },
            {
              icon: Database,
              step: '3',
              title: 'CRM koppelen',
              desc: 'Verbind Airtable zodat leads automatisch binnenkomen.',
              color: 'bg-blue-50 text-blue-600',
            },
          ].map((s) => (
            <div
              key={s.step}
              className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
            >
              <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl ${s.color}`}>
                <s.icon className="h-5 w-5" />
              </div>
              <div className="mb-1 flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wide text-gray-400">
                  Stap {s.step}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900">{s.title}</h3>
              <p className="mt-1 text-sm text-gray-500">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Voordelen checklist */}
        <div className="mb-10 rounded-2xl border border-green-200 bg-green-50 p-6">
          <p className="mb-4 font-semibold text-green-900">Wat je krijgt:</p>
          <ul className="space-y-2.5">
            {[
              '24/7 automatisch antwoorden op WhatsApp-berichten',
              'Naam, adres en aanvraagdetails automatisch verzameld',
              'Leads direct in Airtable — geen handmatig werk meer',
              'Gesprekken bekijken en overnemen wanneer je wil',
            ].map(item => (
              <li key={item} className="flex items-center gap-2.5 text-sm text-green-800">
                <Check className="h-4 w-4 shrink-0 text-green-600" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link
            href="/klanten/nieuw"
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all hover:scale-105"
          >
            Eerste klant toevoegen <ArrowRight className="h-5 w-5" />
          </Link>
          <p className="mt-4 text-sm text-gray-400">
            Je kunt later altijd meer klanten toevoegen via het dashboard.
          </p>
          <Link
            href="/dashboard"
            className="mt-3 block text-xs text-gray-400 underline underline-offset-2 hover:text-gray-600"
          >
            Overslaan — later instellen
          </Link>
        </div>
      </div>
    </div>
  )
}
