import type { Metadata } from 'next'
import Link from 'next/link'
import { Zap, ArrowLeft } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Algemene Voorwaarden',
  description: 'Algemene voorwaarden voor het gebruik van Repto, de AI-receptionist voor KMO\'s.',
}

export default function VoorwaardenPage() {
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
          <h1 className="text-4xl font-extrabold text-gray-900">Algemene Voorwaarden</h1>
          <p className="mt-3 text-gray-500">Laatste update: 27 mei 2026</p>
        </div>

        <div className="prose prose-gray max-w-none space-y-10 text-sm leading-relaxed text-gray-600">

          {/* ── 1 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">1. Identiteit van de aanbieder</h2>
            <p>
              <strong>Repto BV</strong> (in oprichting), België.
              <br />
              E-mail: <a href="mailto:info@repto.be" className="text-indigo-600 underline hover:text-indigo-800">info@repto.be</a>
              <br />
              Website: <a href="https://repto-three.vercel.app" className="text-indigo-600 underline hover:text-indigo-800">https://repto-three.vercel.app</a>
            </p>
          </section>

          {/* ── 2 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">2. Toepassingsgebied</h2>
            <p>
              Deze algemene voorwaarden zijn van toepassing op alle overeenkomsten tussen Repto en de klant
              die gebruik maakt van het Repto-platform (hierna: "de Dienst"). Door een account aan te
              maken en de Dienst te gebruiken, aanvaardt de klant deze voorwaarden volledig.
            </p>
          </section>

          {/* ── 3 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">3. Beschrijving van de Dienst</h2>
            <p>
              Repto biedt een <strong>WhatsApp AI-receptionist</strong> aan voor KMO's en zelfstandigen.
              De Dienst omvat:
            </p>
            <ul className="mt-3 ml-5 list-disc space-y-1.5">
              <li>Automatische verwerking van inkomende WhatsApp-berichten via AI (Anthropic Claude)</li>
              <li>Opslag en beheer van klantgesprekken in een dashboard</li>
              <li>Synchronisatie van leads met externe CRM-systemen (Airtable, e.a.)</li>
              <li>Afsprakenbeheer en WhatsApp-herinneringen</li>
              <li>Configuratie van sector-specifieke AI-instructies</li>
            </ul>
            <p className="mt-3">
              Repto behoudt het recht om de Dienst te wijzigen, uit te breiden of te beperken,
              mits redelijke aankondiging aan de klant.
            </p>
          </section>

          {/* ── 4 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">4. Abonnementen en betaling</h2>

            <h3 className="mb-2 font-semibold text-gray-800">4.1 Tarieven</h3>
            <p>
              De geldende tarieven zijn beschikbaar op de{' '}
              <a href="/#prijzen" className="text-indigo-600 underline hover:text-indigo-800">prijzenpagina</a>.
              Alle prijzen zijn exclusief BTW, tenzij anders vermeld.
            </p>

            <h3 className="mb-2 mt-4 font-semibold text-gray-800">4.2 Gratis proefperiode</h3>
            <p>
              Nieuwe klanten genieten van een gratis proefperiode van 7 dagen. Na afloop wordt het
              abonnement automatisch verlengd tenzij tijdig opgezegd. Een geldige betaalmethode
              is vereist bij aanvang van de proefperiode.
            </p>

            <h3 className="mb-2 mt-4 font-semibold text-gray-800">4.3 Facturatie</h3>
            <p>
              Abonnementen worden maandelijks vooraf gefactureerd via Stripe. Bij mislukte betaling
              ontvangt de klant een melding; bij herhaalde mislukking kan de toegang worden
              opgeschort tot de betaling is geregeld.
            </p>

            <h3 className="mb-2 mt-4 font-semibold text-gray-800">4.4 Gesprekslimieten</h3>
            <p>
              Elk abonnementsplan bevat een maandelijks maximum aantal gesprekken. Bij overschrijding
              wordt de klant geïnformeerd. Overschot wordt afgerekend per gesprek aan het geldend tarief,
              of de klant kan upgraden naar een hoger plan.
            </p>
          </section>

          {/* ── 5 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">5. Opzegging</h2>
            <p>
              De klant kan het abonnement op elk moment opzeggen via de accountinstellingen
              in het dashboard. Na opzegging blijft de toegang actief tot het einde van de
              lopende betaalperiode. Er worden geen resterende abonnementsgelden terugbetaald,
              tenzij uitdrukkelijk anders overeengekomen.
            </p>
            <p className="mt-3">
              Repto behoudt het recht om een account te beëindigen bij:
            </p>
            <ul className="mt-2 ml-5 list-disc space-y-1">
              <li>Herhaaldelijke niet-betaling</li>
              <li>Misbruik van de Dienst of schending van deze voorwaarden</li>
              <li>Activiteiten die in strijd zijn met wet- of regelgeving</li>
            </ul>
          </section>

          {/* ── 6 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">6. Verplichtingen van de klant</h2>
            <p>De klant verbindt zich ertoe:</p>
            <ul className="mt-3 ml-5 list-disc space-y-1.5">
              <li>De Dienst uitsluitend te gebruiken voor wettige doeleinden.</li>
              <li>Zijn eindklanten te informeren dat hun berichten via een AI-systeem worden verwerkt, conform de AVG-transparantieverplichtingen.</li>
              <li>Geen spam, misleidende of onrechtmatige berichten te versturen via het platform.</li>
              <li>Zijn inloggegevens vertrouwelijk te houden en onmiddellijk melding te maken bij vermoeden van ongeautoriseerd gebruik.</li>
              <li>Te voldoen aan de geldende WhatsApp Business-gebruiksvoorwaarden van Meta.</li>
            </ul>
          </section>

          {/* ── 7 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">7. Beschikbaarheid en onderhoud</h2>
            <p>
              Repto streeft naar een beschikbaarheid van <strong>99,5%</strong> op maandbasis.
              Gepland onderhoud wordt vooraf aangekondigd. Repto is niet aansprakelijk voor
              onderbrekingen buiten zijn controle (overmacht, storingen bij derde partijen zoals
              Twilio of WhatsApp, enz.).
            </p>
          </section>

          {/* ── 8 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">8. Aansprakelijkheidsbeperking</h2>
            <p>
              Repto levert een <em>best-effort</em> AI-dienst. De antwoorden gegenereerd door de AI
              zijn automatisch en kunnen onjuistheden bevatten. De klant is zelf verantwoordelijk
              voor het monitoren van gesprekken en het bijsturen waar nodig.
            </p>
            <p className="mt-3">
              Repto is niet aansprakelijk voor:
            </p>
            <ul className="mt-2 ml-5 list-disc space-y-1">
              <li>Indirecte of gevolgschade (gederfde omzet, verlies van klanten, enz.)</li>
              <li>Schade veroorzaakt door onjuiste AI-antwoorden</li>
              <li>Onderbrekingen van WhatsApp of andere derde partijen</li>
            </ul>
            <p className="mt-3">
              De aansprakelijkheid van Repto is in alle gevallen beperkt tot het door de klant
              betaalde abonnementsbedrag in de drie maanden voorafgaand aan het schadegeval.
            </p>
          </section>

          {/* ── 9 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">9. Intellectueel eigendom</h2>
            <p>
              Alle rechten op het Repto-platform, de software, de interfaces en de branding berusten
              bij Repto. De klant verkrijgt een niet-exclusief gebruiksrecht voor de duur van het
              abonnement. De klant blijft eigenaar van zijn eigen bedrijfsgegevens en klantgesprekken.
            </p>
          </section>

          {/* ── 10 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">10. Privacy en gegevensverwerking</h2>
            <p>
              De verwerking van persoonsgegevens is geregeld in ons{' '}
              <Link href="/privacy" className="text-indigo-600 underline hover:text-indigo-800">
                Privacybeleid
              </Link>
              , dat integraal deel uitmaakt van deze overeenkomst. Repto sluit met iedere klant
              een verwerkersovereenkomst (DPA) die op aanvraag beschikbaar is via{' '}
              <a href="mailto:privacy@repto.be" className="text-indigo-600 underline hover:text-indigo-800">privacy@repto.be</a>.
            </p>
          </section>

          {/* ── 11 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">11. Wijzigingen aan de voorwaarden</h2>
            <p>
              Repto behoudt het recht deze voorwaarden te wijzigen. Wezenlijke wijzigingen worden
              minimaal 30 dagen op voorhand per e-mail gecommuniceerd. Voortgezet gebruik van de
              Dienst na de ingangsdatum geldt als aanvaarding van de gewijzigde voorwaarden.
            </p>
          </section>

          {/* ── 12 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">12. Toepasselijk recht en bevoegde rechtbank</h2>
            <p>
              Deze voorwaarden worden beheerst door het <strong>Belgisch recht</strong>.
              Bij geschillen zijn de rechtbanken van het gerechtelijk arrondissement van de
              maatschappelijke zetel van Repto bevoegd, tenzij dwingende wetgeving een andere
              rechtbank aanwijst.
            </p>
          </section>

          {/* ── 13 ── */}
          <section>
            <h2 className="mb-3 text-lg font-bold text-gray-900">13. Contact</h2>
            <p>
              Voor vragen over deze voorwaarden:{' '}
              <a href="mailto:info@repto.be" className="text-indigo-600 underline hover:text-indigo-800">info@repto.be</a>
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
              <Link href="/privacy" className="hover:text-gray-700">Privacybeleid</Link>
              <Link href="/voorwaarden" className="font-medium text-indigo-600">Algemene voorwaarden</Link>
              <span>© 2026 Repto</span>
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}
