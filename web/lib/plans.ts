/**
 * Repto plan configuratie — importeerbaar vanuit server én client componenten.
 * Bevat geen Stripe dependency zodat het veilig is op build time.
 */

export const PLANS = {
  starter: {
    name: 'Starter',
    price: 49,
    klanten: 1,
    gesprekken: '200/maand',
    features: [
      '1 klant-organisatie',
      '200 gesprekken per maand',
      'Airtable CRM koppeling',
      'AI-receptionist via WhatsApp',
      'E-mail support',
    ],
  },
  groei: {
    name: 'Groei',
    price: 99,
    klanten: 5,
    gesprekken: '500/maand',
    popular: true,
    features: [
      '5 klant-organisaties',
      '500 gesprekken per maand',
      'Airtable CRM koppeling',
      'AI-receptionist via WhatsApp',
      'Afspraken module',
      'Prioriteit support',
    ],
  },
  agency: {
    name: 'Agency',
    price: 199,
    klanten: Infinity,
    gesprekken: 'Onbeperkt',
    features: [
      'Onbeperkt klant-organisaties',
      'Onbeperkt gesprekken',
      'Airtable + HubSpot koppeling',
      'AI-receptionist via WhatsApp',
      'Afspraken module',
      'Dedicated support',
      'White-label optie',
    ],
  },
} as const

export type PlanKey = keyof typeof PLANS
