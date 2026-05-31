/**
 * Sector-content voor de landingspagina's /voor/[sector].
 * Importeerbaar vanuit server- én client-componenten (geen dependencies).
 * Slugs zijn tegelijk de URL-segmenten en moeten uniek/kleinletters zijn.
 */

export interface Sector {
  slug: string
  label: string          // meervoud, zoals in de "Voor wie"-sectie
  emoji: string
  /** Eén concrete zin: het typische WhatsApp-bericht dat binnenkomt. */
  voorbeeldBericht: string
  /** Korte intro-paragraaf bovenaan de sectorpagina. */
  intro: string
  /** 3 concrete situaties waarin Repto helpt voor deze sector. */
  situaties: string[]
}

export const SECTORS: Sector[] = [
  {
    slug: 'loodgieters',
    label: 'Loodgieters',
    emoji: '🔧',
    voorbeeldBericht: 'Goedenavond, ik heb een lek in mijn badkamer. Kunnen jullie morgen langskomen?',
    intro: 'Een lek wacht niet tot kantooruren. Repto beantwoordt WhatsApp-berichten van klanten automatisch, vraagt naam, adres en de aard van het probleem, en zet de lead klaar — terwijl jij op de werf staat of slaapt.',
    situaties: [
      'Een avondoproep over een lek wordt meteen beantwoord en gekwalificeerd.',
      'Adres en type werk worden automatisch verzameld voor je dagplanning.',
      'Spoedgevallen worden herkend en met voorrang gemarkeerd in je CRM.',
    ],
  },
  {
    slug: 'elektriciens',
    label: 'Elektriciens',
    emoji: '⚡',
    voorbeeldBericht: 'Hallo, ik heb een elektrische keuring nodig voor de verkoop van mijn woning.',
    intro: 'Keuringen, storingen en offertes komen vaak buiten de uren binnen. Repto vangt elke WhatsApp-aanvraag op, verzamelt de details en stuurt een gekwalificeerde lead naar je CRM.',
    situaties: [
      'Aanvragen voor een elektrische keuring worden volledig uitgevraagd.',
      'De AI onderscheidt een storing (spoed) van een offerte-aanvraag.',
      'Je belt terug met alle info al op zak: naam, adres, type werk.',
    ],
  },
  {
    slug: 'hvac',
    label: 'HVAC',
    emoji: '🌡️',
    voorbeeldBericht: 'Mijn verwarmingsketel doet raar en het wordt koud. Kan er iemand langskomen?',
    intro: 'Verwarming en koeling kennen pieken: zodra het weer omslaat, loopt je WhatsApp vol. Repto beantwoordt elke aanvraag, plant onderhoud of herstellingen en kwalificeert spoedgevallen.',
    situaties: [
      'Onderhoudscontracten en herstellingen worden uit elkaar gehouden.',
      'Bij uitval zonder verwarming wordt de urgentie automatisch hoog gezet.',
      'Afspraken voor een werfbezoek worden meteen voorgesteld en genoteerd.',
    ],
  },
  {
    slug: 'dakwerkers',
    label: 'Dakwerkers',
    emoji: '🏠',
    voorbeeldBericht: 'Na de storm heb ik losse dakpannen. Kunnen jullie een offerte maken?',
    intro: 'Na slecht weer piekt de vraag. Repto beantwoordt offerte-aanvragen direct, verzamelt adres en omschrijving en zorgt dat geen enkele aanvraag verloren gaat in een volle inbox.',
    situaties: [
      'Storm­schade-aanvragen worden meteen opgevolgd, ook \'s avonds.',
      'De AI vraagt naar adres en een korte omschrijving voor je offerte.',
      'Leads landen gestructureerd in je CRM in plaats van losse berichten.',
    ],
  },
  {
    slug: 'garages',
    label: 'Garages',
    emoji: '🚗',
    voorbeeldBericht: 'Kan ik volgende week langskomen voor een onderhoudsbeurt en banden?',
    intro: 'Onderhoud, herstellingen en afspraken: je klanten appen liever dan ze bellen. Repto neemt de eerste reactie over, kwalificeert de vraag en plant afspraken in.',
    situaties: [
      'Afspraken voor onderhoud worden voorgesteld op basis van beschikbaarheid.',
      'De AI verzamelt merk, model en de gevraagde interventie.',
      'Je werkplaats­planning vult zich met gekwalificeerde aanvragen.',
    ],
  },
  {
    slug: 'makelaars',
    label: 'Makelaars',
    emoji: '🏡',
    voorbeeldBericht: 'Is het appartement in de Kerkstraat nog beschikbaar voor een bezichtiging?',
    intro: 'Als makelaar ontvang je tientallen WhatsApp-vragen per dag. Repto filtert de serieuze kandidaten, verzamelt hun gegevens en stuurt ze meteen naar je CRM — zodat je agenda zich met bezichtigingen vult.',
    situaties: [
      'Geïnteresseerden worden gekwalificeerd vóór ze je tijd kosten.',
      'Bezichtigingsaanvragen worden verzameld met naam en contactgegevens.',
      'Je reageert binnen seconden, ook buiten de kantooruren.',
    ],
  },
  {
    slug: 'renovatie',
    label: 'Renovatie',
    emoji: '🔨',
    voorbeeldBericht: 'We willen onze keuken laten renoveren. Kunnen jullie een prijsindicatie geven?',
    intro: 'Renovatieprojecten beginnen met een vraag via WhatsApp. Repto vangt die op, stelt de juiste vervolgvragen en levert je een gekwalificeerde lead met alle context.',
    situaties: [
      'De AI vraagt naar het type project, de scope en het adres.',
      'Grote en kleine projecten worden van elkaar onderscheiden.',
      'Je belt terug met een duidelijk beeld van de aanvraag.',
    ],
  },
  {
    slug: 'kinesisten',
    label: 'Kinesisten',
    emoji: '💆',
    voorbeeldBericht: 'Goedemiddag, ik zou graag een afspraak maken voor rugklachten.',
    intro: 'Patiënten boeken het liefst snel en buiten de uren. Repto beantwoordt afspraakvragen automatisch, verzamelt de nodige info en houdt je agenda gevuld zonder telefoongerinkel.',
    situaties: [
      'Afspraakvragen worden 24/7 beantwoord en ingepland.',
      'De AI verzamelt de reden van de afspraak en contactgegevens.',
      'Minder no-shows door duidelijke bevestiging via WhatsApp.',
    ],
  },
]

export function getSector(slug: string): Sector | undefined {
  return SECTORS.find((s) => s.slug === slug)
}
