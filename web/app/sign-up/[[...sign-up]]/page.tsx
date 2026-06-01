import { SignUp } from '@clerk/nextjs'
import { Zap, MessageSquare, Database, Clock, Check } from 'lucide-react'

const VOORDELEN = [
  {
    icon: MessageSquare,
    title: 'WhatsApp AI-receptionist',
    desc: 'Beantwoordt klanten automatisch in jouw naam, 24/7 — je mist nooit meer een offerte-aanvraag.',
  },
  {
    icon: Database,
    title: 'Leads automatisch in je CRM',
    desc: 'Elke aanvraag wordt gekwalificeerd en doorgestuurd naar Airtable, compleet met naam en adres.',
  },
  {
    icon: Clock,
    title: 'Live in 10 minuten',
    desc: 'Koppel je WhatsApp, kies je sector en de AI is klaar. Geen technische kennis nodig.',
  },
]

const STAPPEN = [
  'Koppel je WhatsApp Business-nummer',
  'Configureer de AI voor jouw sector',
  'Ontvang gekwalificeerde leads in je dashboard',
]

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      {/* ── Linker kolom: voordelen ──────────────────────────────────────── */}
      <div className="relative hidden flex-1 flex-col justify-center overflow-hidden bg-indigo-600 px-12 py-16 lg:flex">
        <div className="pointer-events-none absolute inset-0 opacity-10"
          style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '24px 24px' }} />

        <div className="relative mx-auto max-w-md">
          <div className="mb-8 flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/30">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">Repto</span>
          </div>

          <h1 className="text-3xl font-extrabold leading-tight text-white">
            Start vandaag — mis nooit meer een lead via WhatsApp.
          </h1>

          <ul className="mt-8 space-y-5">
            {VOORDELEN.map(v => (
              <li key={v.title} className="flex gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/20">
                  <v.icon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-white">{v.title}</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-indigo-200">{v.desc}</p>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-10 rounded-2xl bg-white/10 p-5 ring-1 ring-white/15">
            <p className="mb-3 text-sm font-semibold text-white">Zo gaat het na je registratie:</p>
            <ol className="space-y-2">
              {STAPPEN.map((s, i) => (
                <li key={s} className="flex items-center gap-3 text-sm text-indigo-100">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/20 text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>

      {/* ── Rechter kolom: Clerk sign-up ─────────────────────────────────── */}
      <div className="flex flex-1 flex-col items-center justify-center bg-gray-50 px-4 py-12">
        {/* Logo — alleen op mobiel (desktop heeft het in de linkerkolom) */}
        <div className="mb-8 flex items-center gap-2.5 lg:hidden">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Repto</span>
        </div>

        {/* Trial badge */}
        <div className="mb-6 flex items-center gap-2 rounded-full border border-green-200 bg-green-50 px-4 py-1.5 text-sm font-medium text-green-700">
          ✨ 7 dagen gratis proberen — geen kosten tot dag 7
        </div>

        <SignUp
          appearance={{
            elements: {
              rootBox: 'w-full max-w-sm',
              card: 'shadow-sm border border-gray-200 rounded-2xl',
              headerTitle: 'text-gray-900 font-bold',
              headerSubtitle: 'text-gray-500',
              formButtonPrimary:
                'bg-indigo-600 hover:bg-indigo-700 text-sm font-semibold',
              footerActionLink: 'text-indigo-600 hover:text-indigo-700',
            },
          }}
        />

        {/* Vertrouwenssignalen */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 text-xs text-gray-400">
          <span className="flex items-center gap-1"><Check className="h-3.5 w-3.5 text-green-500" /> 7 dagen gratis</span>
          <span className="flex items-center gap-1"><Check className="h-3.5 w-3.5 text-green-500" /> Geen kosten tot dag 7</span>
          <span className="flex items-center gap-1"><Check className="h-3.5 w-3.5 text-green-500" /> Opzeggen wanneer je wil</span>
        </div>

        <p className="mt-5 text-center text-xs text-gray-400">
          Al een account?{' '}
          <a href="/sign-in" className="font-medium text-indigo-600 hover:underline">
            Aanmelden
          </a>
        </p>
      </div>
    </div>
  )
}
