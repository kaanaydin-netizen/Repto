/**
 * Stripe singleton — SERVER-SIDE ONLY.
 * Gebruik getStripe() in API routes, nooit in client components.
 * Lazy initialisatie zodat build niet crasht zonder STRIPE_SECRET_KEY.
 */
import Stripe from 'stripe'

export function getStripe(): Stripe {
  const key = process.env.STRIPE_SECRET_KEY
  if (!key) {
    throw new Error(
      'STRIPE_SECRET_KEY is niet geconfigureerd. ' +
      'Voeg de env var toe in Vercel (Settings → Environment Variables).'
    )
  }
  return new Stripe(key, { typescript: true })
}

// Re-exporteer plans en types zodat API routes alles uit één bestand halen
export { PLANS, type PlanKey } from './plans'
