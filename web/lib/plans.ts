/**
 * Repto plan configuratie — importeerbaar vanuit server én client componenten.
 * Bevat geen Stripe dependency zodat het veilig is op build time.
 */

// Jaarlijkse facturatie ≈ 2 maanden gratis. priceAnnualPerMonth = getoonde
// prijs/maand wanneer jaarlijks gefactureerd. Echte checkout vereist
// aparte jaarlijkse Stripe-prijzen (env vars STRIPE_PRICE_*_ANNUAL).
export const PLANS = {
  starter: {
    name: 'Starter',
    price: 49,
    priceAnnualPerMonth: 41,
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
    priceAnnualPerMonth: 83,
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
    priceAnnualPerMonth: 166,
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
