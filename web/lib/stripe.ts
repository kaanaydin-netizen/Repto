import Stripe from 'stripe'

// Singleton Stripe client (server-side only)
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  typescript: true,
})

// Plan configuratie — price IDs worden ingesteld als Stripe env vars
export const PLANS = {
  starter: {
    name: 'Starter',
    price: 49,
    priceId: process.env.STRIPE_PRICE_STARTER ?? '',
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
    priceId: process.env.STRIPE_PRICE_GROEI ?? '',
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
    priceId: process.env.STRIPE_PRICE_AGENCY ?? '',
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
