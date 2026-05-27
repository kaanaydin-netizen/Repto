import type { Metadata } from 'next'
import Link from 'next/link'
import { Zap, ArrowLeft } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Privacybeleid — Repto',
  description: 'Hoe Repto omgaat met jouw gegevens en klantdata. AVG/GDPR-conform, opgeslagen op Europese servers.',
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">Repto</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Terug naar home
          </Link>
        </div>
      </header>

      {/* ── Content ─────────────────────────────────────────────────────────── */}
      <main className="mx-auto max-w-3xl px-6 py-16">

        {/* Titel */}
        <div className="mb-12">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-indigo-600">Juridisch</p>
          <h1 className="text-4xl font-extrabold text-gray-900">Privacybeleid</h1>
          <p className="mt-3 text-gray-500">Laatste update: 27 mei 2026</p>
        </div>

        <div className="prose prose-gray max-w-none space-y-10 text-sm leading-relaxed text-gray-600">

          {/* ── 1 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">1. Wie zijn wij?</h2>
            <p>
              Repto is een dienst aangeboden door <strong>Repto BV</strong> (in oprichting), gevestigd in België.
              Voor vragen over dit privacybeleid kun je ons bereiken via{' '}
              <a href="mailto:privacy@repto.be" className="text-indigo-600 underline hover:text-indigo-800">privacy@repto.be</a>.
            </p>
            <p className="mt-3">
              Repto treedt op als <strong>verwerker</strong> van de klantgegevens die via WhatsApp worden
              ontvangen. De KMO of zelfstandige die Repto gebruikt, is de{' '}
              <strong>verwerkingsverantwoordelijke</strong> voor de gegevens van zijn eindklanten.
            </p>
          </section>

          {/* ── 2 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">2. Welke gegevens verwerken wij?</h2>
            <p>We verwerken twee categorieën van gegevens:</p>

            <div className="mt-4 rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Categorie</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Voorbeelden</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Doel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="px-4 py-3 font-medium text-gray-800">Accountgegevens</td>
                    <td className="px-4 py-3 text-gray-500">Naam, e-mailadres, bedrijfsnaam</td>
                    <td className="px-4 py-3 text-gray-500">Aanmaken en beheren van account</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-medium text-gray-800">Gespreksdata</td>
                    <td className="px-4 py-3 text-gray-500">WhatsApp-berichten, naam & telefoonnummer van eindklanten, adres, afspraken</td>
                    <td className="px-4 py-3 text-gray-500">Leveren van de AI-receptionist dienst</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-medium text-gray-800">Technische data</td>
                    <td className="px-4 py-3 text-gray-500">IP-adressen, logbestanden, gebruiksstatistieken</td>
                    <td className="px-4 py-3 text-gray-500">Veiligheid, diagnose en verbetering van de dienst</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-medium text-gray-800">Betalingsdata</td>
                    <td className="px-4 py-3 text-gray-500">Factuurgegevens (via Stripe — wij slaan geen kaartgegevens op)</td>
                    <td className="px-4 py-3 text-gray-500">Facturatie en abonnementsbeheer</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* ── 3 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">3. Rechtsgrond voor verwerking</h2>
            <ul className="ml-5 list-disc space-y-1.5">
              <li><strong>Uitvoering van een overeenkomst</strong> — de verwerking is noodzakelijk om de dienst te leveren (art. 6.1.b AVG).</li>
              <li><strong>Gerechtvaardigd belang</strong> — voor het verbeteren van de dienst en het beveiligen van onze systemen (art. 6.1.f AVG).</li>
              <li><strong>Wettelijke verplichting</strong> — voor het bijhouden van boekhoudkundige en fiscale verplichtingen (art. 6.1.c AVG).</li>
            </ul>
          </section>

          {/* ── 4 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">4. Waar worden gegevens opgeslagen?</h2>
            <p>
              Alle gegevens worden opgeslagen op servers binnen de <strong>Europese Unie</strong>.
              We maken gebruik van de volgende sub-verwerkers, elk met passende GDPR-verwerkersovereenkomsten:
            </p>
            <ul className="mt-3 ml-5 list-disc space-y-1.5">
              <li><strong>Supabase / PostgreSQL</strong> — database (EU-regio)</li>
              <li><strong>Railway</strong> — server hosting (EU-regio)</li>
              <li><strong>Vercel</strong> — frontend hosting</li>
              <li><strong>Anthropic Claude</strong> — AI-tekstgeneratie (berichten worden verwerkt maar niet opgeslagen door Anthropic voor trainingsdata)</li>
              <li><strong>Twilio</strong> — WhatsApp-berichtverwerking</li>
              <li><strong>Stripe</strong> — betalingen</li>
              <li><strong>Clerk</strong> — authenticatie</li>
            </ul>
          </section>

          {/* ── 5 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">5. Hoelang bewaren wij gegevens?</h2>
            <ul className="ml-5 list-disc space-y-1.5">
              <li><strong>Accountgegevens</strong> — zolang het account actief is, plus 30 dagen na opzegging.</li>
              <li><strong>Gespreksdata</strong> — 12 maanden na het laatste gesprek, tenzij je eerder verzoekt tot verwijdering.</li>
              <li><strong>Factuurdata</strong> — 7 jaar conform Belgische boekhoudwetgeving.</li>
              <li><strong>Logbestanden</strong> — maximaal 90 dagen.</li>
            </ul>
          </section>

          {/* ── 6 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">6. Jouw rechten als betrokkene</h2>
            <p>Onder de AVG heb je de volgende rechten:</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {[
                { right: '📋 Recht op inzage', desc: 'Je kunt opvragen welke gegevens we over je bewaren.' },
                { right: '✏️ Recht op rectificatie', desc: 'Je kunt onjuiste gegevens laten corrigeren.' },
                { right: '🗑️ Recht op verwijdering', desc: 'Je kunt vragen om al je gegevens te wissen.' },
                { right: '⏸️ Recht op beperking', desc: 'Je kunt de verwerking tijdelijk laten stilleggen.' },
                { right: '📤 Recht op overdraagbaarheid', desc: 'Je kunt je gegevens opvragen in een leesbaar formaat.' },
                { right: '🚫 Recht van bezwaar', desc: 'Je kunt bezwaar maken tegen verwerking op basis van gerechtvaardigd belang.' },
              ].map(({ right, desc }) => (
                <div key={right} className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <p className="font-semibold text-gray-800">{right}</p>
                  <p className="mt-1 text-xs text-gray-500">{desc}</p>
                </div>
              ))}
            </div>
            <p className="mt-4">
              Stuur een verzoek naar{' '}
              <a href="mailto:privacy@repto.be" className="text-indigo-600 underline hover:text-indigo-800">privacy@repto.be</a>.
              We reageren binnen 30 dagen. Je hebt ook het recht om klacht in te dienen bij de{' '}
              <a href="https://www.gegevensbeschermingsautoriteit.be" target="_blank" rel="noopener noreferrer" className="text-indigo-600 underline hover:text-indigo-800">
                Gegevensbeschermingsautoriteit (GBA)
              </a>.
            </p>
          </section>

          {/* ── 7 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">7. Cookies</h2>
            <p>
              Repto gebruikt een minimaal aantal cookies, enkel functioneel noodzakelijk voor authenticatie
              (Clerk session cookie) en beveiliging. We gebruiken geen tracking- of advertentiecookies.
            </p>
          </section>

          {/* ── 8 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">8. Beveiliging</h2>
            <p>
              We nemen passende technische en organisatorische maatregelen om je gegevens te beschermen:
              TLS-encryptie voor alle dataverkeer, encryptie van gevoelige velden in de database,
              toegangscontrole op basis van rollen, en regelmatige back-ups.
            </p>
          </section>

          {/* ── 9 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">9. Wijzigingen</h2>
            <p>
              We kunnen dit privacybeleid updaten. Bij wezenlijke wijzigingen informeren we je via e-mail
              of een melding in het dashboard. De datum bovenaan geeft de meest recente versie aan.
            </p>
          </section>

          {/* ── 10 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">10. Contact</h2>
            <p>
              Voor vragen, verzoeken of klachten m.b.t. privacy:{' '}
              <a href="mailto:privacy@repto.be" className="text-indigo-600 underline hover:text-indigo-800">privacy@repto.be</a>
            </p>
          </section>

        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 bg-white py-8">
        <div className="mx-auto max-w-4xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600">
                <Zap className="h-3 w-3 text-white" />
              </div>
              <span className="text-sm font-bold text-gray-900">Repto</span>
            </Link>
            <div className="flex items-center gap-5 text-sm text-gray-400">
              <Link href="/privacy" className="font-medium text-indigo-600">Privacybeleid</Link>
              <Link href="/voorwaarden" className="hover:text-gray-700">Algemene voorwaarden</Link>
              <span>© 2026 Repto</span>
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}
