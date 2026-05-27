import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import {
  Zap,
  MessageSquare,
  Database,
  LayoutDashboard,
  Bot,
  ArrowRight,
  Check,
  Phone,
  Clock,
  Users,
  TrendingUp,
  Eye,
  Shield,
  Settings2,
} from 'lucide-react'

// ─── Redirect ingelogde gebruikers ────────────────────────────────────────────

export default async function HomePage() {
  try {
    const { userId } = await auth()
    if (userId) redirect('/dashboard')
  } catch {
    // Niet ingelogd of auth niet beschikbaar — toon landing page
  }

  return (
    <div className="min-h-screen bg-white">

      {/* ── Navigatie ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">Repto</span>
          </div>

          {/* Links */}
          <nav className="hidden items-center gap-6 text-sm font-medium text-gray-600 sm:flex">
            <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
            <a href="#voorbeeld" className="hover:text-gray-900 transition-colors">Voorbeeld</a>
            <a href="#hoe-werkt-het" className="hover:text-gray-900 transition-colors">Hoe het werkt</a>
            <a href="#prijzen" className="hover:text-gray-900 transition-colors">Prijzen</a>
            <a href="#faq" className="hover:text-gray-900 transition-colors">FAQ</a>
          </nav>

          {/* CTA */}
          <div className="flex items-center gap-3">
            <Link
              href="/sign-in"
              className="hidden text-sm font-medium text-gray-600 hover:text-gray-900 sm:block"
            >
              Aanmelden
            </Link>
            <Link
              href="/sign-up"
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
            >
              Gratis starten <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-white pt-16 pb-24">
        {/* Achtergrond gradient */}
        <div className="pointer-events-none absolute inset-0 -top-40 bg-gradient-to-br from-indigo-50 via-white to-white" />

        <div className="relative mx-auto max-w-4xl px-6 text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-500" />
            Voor loodgieters, installateurs, garages & meer
          </div>

          {/* Headline */}
          <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-6xl">
            Mis geen enkele<br />
            <span className="text-indigo-600">offerte-aanvraag meer.</span>
          </h1>

          {/* Sub */}
          <p className="mx-auto mt-6 max-w-2xl text-xl leading-relaxed text-gray-500">
            Repto beantwoordt automatisch WhatsApp-berichten van klanten, verzamelt naam,
            adres en aanvraagdetails — terwijl jij op de werf staat, onderweg bent
            of gewoon slaapt. Jij belt terug wanneer het jou uitkomt.
          </p>

          {/* CTA knoppen */}
          <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/sign-up"
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-7 py-3.5 text-base font-semibold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all hover:scale-105"
            >
              7 dagen gratis starten <ArrowRight className="h-5 w-5" />
            </Link>
            <a
              href="#voorbeeld"
              className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-7 py-3.5 text-base font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Bekijk een voorbeeld
            </a>
          </div>

          {/* Social proof strip */}
          <p className="mt-8 text-sm text-gray-400">
            ✓ 7 dagen gratis &nbsp;·&nbsp; ✓ Geen verplichtingen &nbsp;·&nbsp; ✓ Live in 10 minuten
          </p>

          {/* Stats — prominent in hero */}
          <div className="mx-auto mt-10 grid max-w-2xl grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { value: '24/7', label: 'Bereikbaar' },
              { value: '< 5s', label: 'Gem. reactietijd' },
              { value: '9+', label: 'Sectoren' },
              { value: '100%', label: 'Automatisch' },
            ].map(s => (
              <div key={s.label} className="rounded-2xl border border-indigo-100 bg-white/80 px-4 py-5 shadow-sm">
                <p className="text-2xl font-extrabold text-indigo-600">{s.value}</p>
                <p className="mt-1 text-sm text-gray-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Dashboard preview */}
        <div className="relative mx-auto mt-16 max-w-5xl px-6">
          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl shadow-gray-200">
            {/* Nep browser chrome */}
            <div className="flex items-center gap-2 border-b border-gray-100 bg-gray-50 px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-red-400" />
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              <span className="h-3 w-3 rounded-full bg-green-400" />
              <span className="ml-4 flex-1 rounded-md bg-white px-3 py-1 text-xs text-gray-400 ring-1 ring-gray-200">
                app.repto.be/dashboard
              </span>
            </div>

            {/* Dashboard screenshot mockup */}
            <div className="flex bg-white">
              {/* Sidebar */}
              <div className="hidden w-52 border-r border-gray-100 bg-white p-4 sm:block">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-7 w-7 rounded-lg bg-indigo-600 flex items-center justify-center">
                    <Zap className="h-3.5 w-3.5 text-white" />
                  </div>
                  <span className="text-sm font-bold text-gray-900">Repto</span>
                </div>
                {[
                  { icon: LayoutDashboard, label: 'Dashboard', active: true },
                  { icon: MessageSquare, label: 'Gesprekken', active: false },
                  { icon: Bot, label: 'AI-instellingen', active: false },
                  { icon: Database, label: 'CRM', active: false },
                ].map(({ icon: Icon, label, active }) => (
                  <div
                    key={label}
                    className={`mb-1 flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium ${
                      active ? 'bg-indigo-50 text-indigo-700' : 'text-gray-500'
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                  </div>
                ))}
              </div>

              {/* Main */}
              <div className="flex-1 p-6">
                <p className="mb-4 text-sm font-semibold text-gray-900">Dashboard</p>
                {/* Stat cards */}
                <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { label: 'Gesprekken', value: '48', color: 'text-indigo-700' },
                    { label: 'Nieuwe leads', value: '12', color: 'text-amber-700' },
                    { label: 'Gesloten', value: '7', color: 'text-green-700' },
                    { label: 'CRM sync', value: '35', color: 'text-blue-700' },
                  ].map(stat => (
                    <div key={stat.label} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                      <p className="text-xs text-gray-400">{stat.label}</p>
                      <p className={`mt-1 text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
                {/* Gesprekken */}
                <div className="space-y-2">
                  {[
                    { name: 'Thomas De Smedt', msg: 'Ik heb een lek in mijn badkamer...', time: '09:34', badge: 'Nieuw' },
                    { name: 'Sofie Vermeersch', msg: 'Wanneer kunnen jullie langskomen?', time: 'Gisteren', badge: 'In gesprek' },
                    { name: 'Jan Claes', msg: 'Bedankt, ik wacht jullie telefoontje af.', time: 'Ma', badge: 'Gesloten' },
                  ].map(c => (
                    <div key={c.name} className="flex items-center gap-3 rounded-xl border border-gray-100 bg-white p-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                        {c.name[0]}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-semibold text-gray-900">{c.name}</p>
                        <p className="truncate text-[10px] text-gray-400">{c.msg}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-[10px] text-gray-400">{c.time}</p>
                        <span className={`mt-0.5 inline-block rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${
                          c.badge === 'Nieuw' ? 'bg-amber-100 text-amber-700' :
                          c.badge === 'In gesprek' ? 'bg-indigo-100 text-indigo-700' :
                          'bg-gray-100 text-gray-500'
                        }`}>
                          {c.badge}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Demo video ───────────────────────────────────────────────────── */}
      <section className="bg-gray-50 py-20">
        <div className="mx-auto max-w-4xl px-6">
          <div className="mb-10 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
              ▶ Bekijk de demo
            </div>
            <h2 className="text-3xl font-extrabold text-gray-900">Van WhatsApp-bericht tot lead in 60 seconden</h2>
            <p className="mt-3 text-lg text-gray-500">
              Zie hoe Repto automatisch antwoordt, de klant kwalificeert en de lead opslaat — terwijl jij slaapt.
            </p>
          </div>

          {/* Video container — swap de src in zodra de video klaar is */}
          {/* Gebruik YouTube: src="https://www.youtube.com/embed/JOUW_VIDEO_ID?autoplay=0&rel=0" */}
          {/* Gebruik Vimeo:   src="https://player.vimeo.com/video/JOUW_VIDEO_ID" */}
          <div className="overflow-hidden rounded-2xl border border-gray-200 shadow-xl shadow-gray-200">
            {/* Placeholder — verwijder dit blok en uncomment de iframe zodra de video live is */}
            <div className="relative flex aspect-video w-full items-center justify-center bg-gradient-to-br from-indigo-900 via-indigo-800 to-violet-900">
              {/* Achtergrond ruis-patroon */}
              <div className="pointer-events-none absolute inset-0 opacity-10"
                style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '24px 24px' }} />

              {/* Play knop */}
              <div className="flex flex-col items-center gap-5">
                <div className="flex h-20 w-20 cursor-pointer items-center justify-center rounded-full bg-white/20 ring-4 ring-white/30 backdrop-blur-sm transition-transform hover:scale-110">
                  <div className="ml-1.5 h-0 w-0 border-y-[14px] border-l-[22px] border-y-transparent border-l-white" />
                </div>
                <div className="text-center">
                  <p className="text-base font-semibold text-white">Demo video — binnenkort beschikbaar</p>
                  <p className="mt-1 text-sm text-indigo-300">Wordt opgenomen · 60 seconden</p>
                </div>
              </div>

              {/* Stats overlay onderaan */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-center gap-6 bg-black/30 px-6 py-3 backdrop-blur-sm">
                {[
                  { value: '60s', label: 'Video' },
                  { value: '21:43', label: 'Avondlead' },
                  { value: '< 5s', label: 'AI-reactie' },
                  { value: '100%', label: 'Automatisch' },
                ].map(s => (
                  <div key={s.label} className="text-center">
                    <p className="text-sm font-bold text-white">{s.value}</p>
                    <p className="text-[10px] text-indigo-300">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── UNCOMMENT DIT ZODRA VIDEO KLAAR IS ──────────────────────────
            <iframe
              className="aspect-video w-full"
              src="https://www.youtube.com/embed/JOUW_VIDEO_ID?rel=0&modestbranding=1"
              title="Repto demo — van WhatsApp-bericht tot lead in 60 seconden"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
            ─────────────────────────────────────────────────────────────── */}
          </div>

          <p className="mt-4 text-center text-sm text-gray-400">
            Herkenbaar? <a href="/sign-up" className="font-medium text-indigo-600 hover:underline">Start 7 dagen gratis →</a>
          </p>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section id="features" className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Alles wat je nodig hebt</h2>
            <p className="mt-3 text-lg text-gray-500">
              Van eerste WhatsApp-bericht tot gekwalificeerde lead in je CRM — volledig automatisch.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: MessageSquare,
                color: 'bg-indigo-100 text-indigo-600',
                title: 'WhatsApp AI-receptionist',
                desc: 'Beantwoordt klanten automatisch in jouw naam, 24/7, in het Nederlands. Nooit een lead missen.',
              },
              {
                icon: Bot,
                color: 'bg-violet-100 text-violet-600',
                title: 'Sector-slimme prompts',
                desc: 'Specifieke AI-configuraties voor installateurs, makelaars, garages, kinesisten en meer. Kies zelf of de AI formeel (u) of informeel (je) communiceert met klanten.',
              },
              {
                icon: Database,
                color: 'bg-blue-100 text-blue-600',
                title: 'Automatische CRM sync',
                desc: 'Elke lead wordt automatisch doorgestuurd naar Airtable, compleet met naam, adres en type werk.',
              },
              {
                icon: Users,
                color: 'bg-amber-100 text-amber-600',
                title: 'Overzichtelijk dashboard',
                desc: 'Volg al je gesprekken, leads en afspraken in één helder overzicht. Altijd en overal bereikbaar.',
              },
              {
                icon: Clock,
                color: 'bg-green-100 text-green-600',
                title: 'Afspraken module',
                desc: 'De AI plant automatisch afspraken in en toont ze gegroepeerd in je agenda.',
              },
              {
                icon: TrendingUp,
                color: 'bg-rose-100 text-rose-600',
                title: 'Live statistieken',
                desc: 'Bekijk hoeveel gesprekken, leads en CRM-syncs er vandaag zijn — in real time.',
              },
            ].map(feature => (
              <div
                key={feature.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl ${feature.color}`}>
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 font-semibold text-gray-900">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-gray-500">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Praktijkvoorbeeld ─────────────────────────────────────────────── */}
      <section id="voorbeeld" className="bg-gray-50 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Zo werkt het in de praktijk</h2>
            <p className="mt-3 text-lg text-gray-500">
              Een loodgieter ontvangt om 21:43 een WhatsApp. Repto handelt het volledig af.
            </p>
          </div>

          <div className="mx-auto max-w-lg">
            {/* WhatsApp chat mockup */}
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
              {/* Chat header */}
              <div className="flex items-center gap-3 bg-[#075E54] px-4 py-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-green-300 text-sm font-bold text-green-900">
                  LB
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Loodgieter Baert</p>
                  <p className="text-xs text-green-200">via Repto AI · online</p>
                </div>
              </div>

              {/* Berichten */}
              <div className="space-y-3 bg-[#ECE5DD] p-4">

                {/* Tijdstip */}
                <div className="text-center">
                  <span className="rounded-full bg-white/60 px-3 py-0.5 text-[10px] text-gray-500">
                    Vandaag 21:43
                  </span>
                </div>

                {/* Klant */}
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-[#DCF8C6] px-3.5 py-2 shadow-sm">
                    <p className="text-sm text-gray-800">Goedenavond, ik heb een lek in mijn badkamer. Kunnen jullie morgen langskomen?</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:43 ✓✓</p>
                  </div>
                </div>

                {/* Repto */}
                <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-2xl rounded-tl-sm bg-white px-3.5 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold text-indigo-600 mb-1">⚡ Repto AI</p>
                    <p className="text-sm text-gray-800">Goedenavond! Dat lossen we snel op. Mag ik uw naam en adres vragen zodat we alles kunnen inplannen?</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:43</p>
                  </div>
                </div>

                {/* Klant */}
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-[#DCF8C6] px-3.5 py-2 shadow-sm">
                    <p className="text-sm text-gray-800">Thomas De Smedt, Kerkstraat 14, Gent</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:44 ✓✓</p>
                  </div>
                </div>

                {/* Repto */}
                <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-2xl rounded-tl-sm bg-white px-3.5 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold text-indigo-600 mb-1">⚡ Repto AI</p>
                    <p className="text-sm text-gray-800">Bedankt Thomas! Is er sprake van wateroverlast of is het een klein lek? En bent u morgen de hele dag beschikbaar?</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:44</p>
                  </div>
                </div>

                {/* Klant */}
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-[#DCF8C6] px-3.5 py-2 shadow-sm">
                    <p className="text-sm text-gray-800">Klein lek onder de wastafel. Ja morgen ben ik thuis.</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:45 ✓✓</p>
                  </div>
                </div>

                {/* Repto */}
                <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-2xl rounded-tl-sm bg-white px-3.5 py-2 shadow-sm">
                    <p className="text-[10px] font-semibold text-indigo-600 mb-1">⚡ Repto AI</p>
                    <p className="text-sm text-gray-800">Perfect! Ik heb alles genoteerd. We nemen morgenochtend contact op om een exact tijdstip af te spreken. Tot morgen! 👍</p>
                    <p className="mt-1 text-right text-[10px] text-gray-400">21:45</p>
                  </div>
                </div>

                {/* CRM sync notificatie */}
                <div className="flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 px-3 py-2.5">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500">
                    <Check className="h-3.5 w-3.5 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-green-800">Lead doorgestuurd naar Airtable ✓</p>
                    <p className="text-[10px] text-green-600">Thomas De Smedt · Kerkstraat 14, Gent · Lek badkamer</p>
                  </div>
                </div>

              </div>
            </div>

            <p className="mt-4 text-center text-sm text-gray-400">
              Terwijl jij sliep, heeft Repto de lead volledig verzameld en opgeslagen.
            </p>
          </div>
        </div>
      </section>

      {/* ── Jij houdt altijd controle ─────────────────────────────────────── */}
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                <Shield className="h-3.5 w-3.5" /> Jij blijft altijd de baas
              </div>
              <h2 className="text-3xl font-extrabold text-gray-900">
                Repto automatiseert.<br />
                <span className="text-indigo-600">Jij behoudt de controle.</span>
              </h2>
              <p className="mt-4 text-lg text-gray-500 leading-relaxed">
                Repto automatiseert de eerste klantreactie, maar jij beslist altijd wat er gebeurt.
                Je kunt elk gesprek volgen, overnemen en de AI bijsturen wanneer je wil.
              </p>
              <ul className="mt-8 space-y-4">
                {[
                  {
                    icon: Eye,
                    title: 'Alle gesprekken bekijken',
                    desc: 'Volg elk WhatsApp-gesprek live in je dashboard. Zie precies wat de AI heeft gezegd.',
                  },
                  {
                    icon: Phone,
                    title: 'Gesprek overnemen',
                    desc: 'Wil je zelf reageren? Neem het gesprek over met één klik. De AI pauzeert automatisch.',
                  },
                  {
                    icon: Settings2,
                    title: 'AI-instellingen aanpassen',
                    desc: 'Pas toon, instructies en sector aan. De AI leert hoe jij communiceert.',
                  },
                ].map(item => (
                  <li key={item.title} className="flex gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50">
                      <item.icon className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{item.title}</p>
                      <p className="mt-0.5 text-sm text-gray-500">{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Rechter kolom: mini chat interface mockup */}
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm font-semibold text-gray-900">Gesprek — Thomas De Smedt</p>
                <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-[10px] font-semibold text-green-700">Gesloten ✓</span>
              </div>
              <div className="space-y-3">
                {[
                  { dir: 'in',  text: 'Ik heb een lek in mijn badkamer...' },
                  { dir: 'out', text: 'Goedenavond! Dat lossen we snel op. Mag ik uw naam en adres?' },
                  { dir: 'in',  text: 'Thomas De Smedt, Kerkstraat 14, Gent' },
                  { dir: 'out', text: 'Bedankt! We nemen morgen contact op. 👍' },
                ].map((m, i) => (
                  <div key={i} className={`flex ${m.dir === 'out' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-xl px-3 py-2 text-xs ${
                      m.dir === 'out'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {m.dir === 'out' && <p className="mb-0.5 text-[9px] font-semibold text-indigo-200">⚡ Repto AI</p>}
                      {m.text}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2">
                <Phone className="h-3.5 w-3.5 text-indigo-600" />
                <p className="text-xs text-indigo-700 font-medium">Gesprek overnemen</p>
                <span className="ml-auto text-[10px] text-indigo-400">AI pauzeert automatisch</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Voor wie is Repto? ────────────────────────────────────────────── */}
      <section className="bg-gray-50 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Voor wie is Repto?</h2>
            <p className="mt-3 text-lg text-gray-500">
              Je bent zelfstandig of hebt een klein bedrijf. Je WhatsApp staat altijd vol —
              maar je kan niet altijd meteen antwoorden. Dat is precies waarvoor Repto gemaakt is.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 lg:grid-cols-8">
            {[
              { emoji: '⚡', label: 'Elektriciens' },
              { emoji: '🔧', label: 'Loodgieters' },
              { emoji: '🌡️', label: 'HVAC' },
              { emoji: '🏠', label: 'Dakwerkers' },
              { emoji: '🚗', label: 'Garages' },
              { emoji: '🏡', label: 'Makelaars' },
              { emoji: '🔨', label: 'Renovatie' },
              { emoji: '💆', label: 'Kinesisten' },
            ].map(s => (
              <div
                key={s.label}
                className="flex flex-col items-center gap-2 rounded-2xl border border-gray-200 bg-white p-4 text-center shadow-sm hover:border-indigo-200 hover:shadow-md transition-all"
              >
                <span className="text-2xl">{s.emoji}</span>
                <span className="text-xs font-medium text-gray-600">{s.label}</span>
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-sm text-gray-400">
            Ook voor <span className="font-medium text-gray-500">marketing agencies</span> die meerdere klanten beheren —
            bekijk het <a href="#prijzen" className="text-indigo-500 hover:underline">Agency-plan</a>.
          </p>
        </div>
      </section>

      {/* ── Hoe het werkt ─────────────────────────────────────────────────── */}
      <section id="hoe-werkt-het" className="py-24">
        <div className="mx-auto max-w-4xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">In 3 stappen live</h2>
            <p className="mt-3 text-lg text-gray-500">
              Geen technische kennis vereist. Van aanmelden tot eerste AI-gesprek in minder dan 10 minuten.
            </p>
          </div>

          <div className="relative">
            {/* Verbindingslijn */}
            <div className="absolute left-6 top-8 hidden h-[calc(100%-4rem)] w-px bg-indigo-100 sm:block" />

            <div className="space-y-8">
              {[
                {
                  step: '01',
                  title: 'Verbind je WhatsApp nummer',
                  desc: 'Koppel je Meta / WhatsApp Business nummer aan Repto via de onboarding wizard. Klaar in 2 minuten.',
                  badge: 'WhatsApp Business',
                },
                {
                  step: '02',
                  title: 'Configureer de AI-receptionist',
                  desc: 'Kies je sector, communicatiestijl en voeg extra bedrijfsinformatie toe. De AI past zich automatisch aan.',
                  badge: 'AI configuratie',
                },
                {
                  step: '03',
                  title: 'Ontvang leads in je CRM',
                  desc: 'Zodra een klant via WhatsApp contact opneemt, verwerkt de AI het gesprek en stuurt een gekwalificeerde lead naar Airtable.',
                  badge: 'Airtable sync',
                },
              ].map((item, i) => (
                <div key={i} className="relative flex gap-6 sm:items-start">
                  <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-4 border-white bg-indigo-600 text-sm font-bold text-white shadow-md">
                    {item.step}
                  </div>
                  <div className="flex-1 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-1 flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{item.title}</h3>
                      <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-semibold text-indigo-600">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed text-gray-500">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Prijzen ───────────────────────────────────────────────────────── */}
      <section id="prijzen" className="bg-gray-50 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Eenvoudige prijzen</h2>
            <p className="mt-3 text-lg text-gray-500">
              Geen vaste contracten. Geen verborgen kosten. Opzeggen wanneer je wil.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                name: 'Starter',
                price: 49,
                desc: 'Voor zelfstandigen die hun eigen WhatsApp willen automatiseren.',
                features: ['Jouw bedrijf (1 WhatsApp-nummer)', '200 gesprekken/maand', 'Airtable CRM', 'E-mail support'],
                popular: false,
              },
              {
                name: 'Groei',
                price: 99,
                desc: 'Voor bedrijven met meerdere medewerkers of hogere leadvolumes.',
                features: ['Tot 5 WhatsApp-nummers', '500 gesprekken/maand', 'Airtable CRM', 'Afspraken module', 'Prioriteit support'],
                popular: true,
              },
              {
                name: 'Agency',
                price: 199,
                desc: 'Voor agencies of partners die meerdere klanten beheren.',
                features: ['Onbeperkt klanten', 'Onbeperkt gesprekken', 'Airtable + HubSpot', 'Dedicated support', 'White-label'],
                popular: false,
              },
            ].map(plan => (
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
                  <span className="text-4xl font-extrabold text-gray-900">€{plan.price}</span>
                  <span className="text-sm text-gray-400">/maand excl. btw</span>
                </div>
                <ul className="my-6 flex-1 space-y-2.5">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
                      {f}
                    </li>
                  ))}
                </ul>
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
                <p className="mt-2 text-center text-[11px] text-gray-400">
                  Betaalmethode vereist · na 7 dagen €{plan.price}/maand excl. btw
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Integraties strip ────────────────────────────────────────────── */}
      <section className="border-y border-gray-100 bg-white py-10">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-6 text-center text-sm font-semibold uppercase tracking-widest text-gray-400">
            Werkt naadloos samen met:
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6">
            {[
              { color: 'bg-green-500',  label: 'WhatsApp Business' },
              { color: 'bg-yellow-400', label: 'Airtable' },
              { color: 'bg-red-500',    label: 'Twilio' },
              { color: 'bg-purple-600', label: 'Claude AI' },
              { color: 'bg-blue-500',   label: 'Stripe' },
            ].map(({ color, label }) => (
              <div
                key={label}
                className="flex items-center gap-2.5 rounded-full border border-gray-100 bg-gray-50 px-5 py-2.5 shadow-sm"
              >
                <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
                <span className="text-sm font-semibold text-gray-700">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ─────────────────────────────────────────────────── */}
      <section className="bg-gray-50 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
              ✨ Early access gebruikers
            </div>
            <h2 className="text-3xl font-extrabold text-gray-900">Wat onze pilotgebruikers zeggen</h2>
            <p className="mt-3 text-lg text-gray-500">
              KMO&apos;s die als eerste toegang kregen tot Repto.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                quote: 'Vroeger miste ik bijna elke avondoproep. Nu beantwoordt Repto automatisch en heb ik de volgende ochtend een volledig ingevuld leadformulier. Ik heb al 3 extra jobs per week dankzij Repto.',
                initials: 'E',
                role: 'Elektricien',
                location: 'Gent',
              },
              {
                quote: 'Als makelaar ontvang ik tientallen WhatsApp-vragen per dag. Repto filtert de serieuze kandidaten eruit en stuurt ze meteen naar mijn Airtable. Mijn agenda is 30% voller geworden.',
                initials: 'M',
                role: 'Makelaar',
                location: 'Antwerpen',
              },
              {
                quote: 'Ik stond sceptisch tegenover AI, maar Repto communiceert precies zoals ik dat zou doen. Klanten merken het verschil niet en ik mis geen enkele offerte-aanvraag meer.',
                initials: 'D',
                role: 'Dakwerker',
                location: 'Brussel',
              },
            ].map(t => (
              <div
                key={t.role}
                className="flex flex-col rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                {/* Sterren */}
                <div className="mb-4 flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span key={i} className="text-amber-400">★</span>
                  ))}
                </div>
                <p className="flex-1 text-sm leading-relaxed text-gray-600">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-5 flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{t.role}</p>
                    <p className="text-xs text-gray-400">{t.location} · early access</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────────── */}
      <section id="faq" className="bg-white py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Veelgestelde vragen</h2>
            <p className="mt-3 text-lg text-gray-500">
              Alles wat je wil weten voor je start.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            {[
              {
                q: 'Wat als de AI een fout antwoord geeft?',
                a: 'Repto is getraind op jouw sector en instructies. Je kunt elk gesprek live volgen en op elk moment overnemen. De AI laat duidelijk weten dat een medewerker zal terugbellen voor complexe vragen.',
              },
              {
                q: 'Werkt dit met mijn bestaande WhatsApp-nummer?',
                a: 'Repto werkt via WhatsApp Business. Je koppelt je bestaand zakelijk nummer in de onboarding wizard. Heb je nog geen WhatsApp Business? We begeleiden je stap voor stap bij de aanvraag.',
              },
              {
                q: 'Kan ik het gesprek overnemen?',
                a: 'Ja, met één klik in je dashboard kun je elk gesprek overnemen. De AI pauzeert automatisch zodra jij reageert.',
              },
              {
                q: 'Kan ik de AI eerst testen voor klanten ermee in contact komen?',
                a: 'Ja. Tijdens de gratis trial heb je toegang tot een testnummer waarmee je zelf gesprekken kunt simuleren. Zo stel je alles in op jouw manier voor je live gaat.',
              },
              {
                q: 'Welke CRM-systemen worden ondersteund?',
                a: 'Momenteel Airtable (volledig). HubSpot en Pipedrive zijn in ontwikkeling en worden later dit jaar toegevoegd. Je kunt ook kiezen voor alleen e-mailnotificaties zonder CRM.',
              },
              {
                q: 'Hoe lang duurt de installatie?',
                a: 'Gemiddeld 10 minuten. Je koppelt je WhatsApp Business-nummer, configureert de AI en je bent live. Geen technische kennis vereist.',
              },
              {
                q: 'Wat als ik meer gesprekken heb dan mijn plan toelaat?',
                a: 'Je ontvangt een melding bij 80% gebruik. Overschot wordt afgerekend aan een vast tarief per gesprek, of je upgradet eenvoudig naar een hoger plan. Je wordt nooit plots afgesneden.',
              },
              {
                q: 'Wat als ik wil opzeggen?',
                a: 'Je kunt op elk moment opzeggen via je accountinstellingen, zonder opzegtermijn. Je wordt nooit langer gefactureerd dan de lopende maand.',
              },
              {
                q: 'Wat als jullie de prijzen aanpassen?',
                a: 'Bestaande abonnees worden minimaal 30 dagen op voorhand per e-mail verwittigd. Je huidige tarief blijft geldig tot het einde van je lopende facturatieperiode. Akkoord je niet met de nieuwe prijs, dan kan je gewoon opzeggen — zonder extra kosten.',
              },
            ].map(({ q, a }) => (
              <div
                key={q}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                <p className="font-semibold text-gray-900">{q}</p>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── GDPR / Data & Privacy ─────────────────────────────────────────── */}
      <section className="bg-indigo-50 py-20">
        <div className="mx-auto max-w-4xl px-6">
          <div className="flex flex-col items-center gap-8 text-center sm:flex-row sm:text-left">
            {/* Icon */}
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 shadow-md">
              <Shield className="h-8 w-8 text-white" />
            </div>

            {/* Tekst */}
            <div className="flex-1">
              <h2 className="text-2xl font-extrabold text-gray-900">
                Jouw data blijft van jou — en blijft in Europa.
              </h2>
              <p className="mt-3 text-base leading-relaxed text-gray-600">
                Alle gesprekken en klantgegevens worden opgeslagen op <strong>Europese servers</strong> (EU-regio).
                Repto verwerkt gegevens conform de <strong>AVG / GDPR</strong>-wetgeving.
                Conversaties worden <strong>versleuteld</strong> bewaard en <strong>nooit gedeeld</strong> met derden.
                Jij bent en blijft de eigenaar van alle data — je kunt alles op elk moment exporteren of verwijderen.
              </p>
            </div>

            {/* Chips */}
            <div className="flex shrink-0 flex-col gap-2 sm:items-end">
              {[
                '🇪🇺 EU-servers',
                '🔒 Versleuteld',
                '✅ AVG-conform',
                '🗑️ Recht op verwijdering',
              ].map(label => (
                <span
                  key={label}
                  className="inline-flex items-center rounded-full border border-indigo-200 bg-white px-3 py-1 text-xs font-semibold text-indigo-700 shadow-sm"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────────── */}
      <section className="bg-indigo-600 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-extrabold text-white">
            Stop met leads missen via WhatsApp.
          </h2>
          <p className="mt-4 text-lg text-indigo-200">
            Start vandaag met 7 dagen gratis — verbind je WhatsApp-nummer in minder dan 10 minuten.
          </p>
          <Link
            href="/sign-up"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-semibold text-indigo-600 shadow-lg hover:bg-indigo-50 transition-colors"
          >
            7 dagen gratis starten <ArrowRight className="h-5 w-5" />
          </Link>
          <p className="mt-4 text-sm text-indigo-300">
            ✓ 7 dagen gratis &nbsp;·&nbsp; ✓ Geen verplichtingen &nbsp;·&nbsp; ✓ Opzeggen wanneer je wil
          </p>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 bg-white py-10">
        <div className="mx-auto max-w-5xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600">
                <Zap className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="font-bold text-gray-900">Repto</span>
              <span className="text-sm text-gray-400">— AI-receptionist voor KMO's</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
              <Link href="/sign-in" className="hover:text-gray-700">Aanmelden</Link>
              <a href="#prijzen" className="hover:text-gray-700">Prijzen</a>
              <a href="#faq" className="hover:text-gray-700">FAQ</a>
              <Link href="/privacy" className="hover:text-gray-700">Privacybeleid</Link>
              <Link href="/voorwaarden" className="hover:text-gray-700">Algemene voorwaarden</Link>
              <span>© 2026 Repto</span>
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}
