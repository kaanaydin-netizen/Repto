import { clerkClient } from '@clerk/nextjs/server'
import { NextRequest, NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'
import type Stripe from 'stripe'

// Next.js mag de body NIET parsen — Stripe heeft de raw bytes nodig
export const config = { api: { bodyParser: false } }

export async function POST(request: NextRequest) {
  const sig = request.headers.get('stripe-signature')
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET

  if (!sig || !webhookSecret) {
    return NextResponse.json({ error: 'Webhook geweigerd' }, { status: 400 })
  }

  const rawBody = await request.text()

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig, webhookSecret)
  } catch (err) {
    console.error('Stripe webhook verificatie mislukt:', err)
    return NextResponse.json({ error: 'Ongeldige handtekening' }, { status: 400 })
  }

  const clerk = await clerkClient()

  try {
    switch (event.type) {
      // Betaling succesvol — sla plan op in Clerk metadata
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        const clerkUserId = session.metadata?.clerk_user_id
        const plan = session.metadata?.plan
        const customerId = session.customer as string

        if (clerkUserId && plan) {
          const user = await clerk.users.getUser(clerkUserId)
          await clerk.users.updateUserMetadata(clerkUserId, {
            privateMetadata: {
              ...(user.privateMetadata as object),
              stripeCustomerId: customerId,
              stripePlan: plan,
              stripeSubscriptionId: session.subscription as string,
              stripeStatus: 'active',
            },
          })
        }
        break
      }

      // Abonnement bijgewerkt (upgrade/downgrade)
      case 'customer.subscription.updated': {
        const sub = event.data.object as Stripe.Subscription
        const clerkUserId = sub.metadata?.clerk_user_id
        const plan = sub.metadata?.plan

        if (clerkUserId) {
          const user = await clerk.users.getUser(clerkUserId)
          await clerk.users.updateUserMetadata(clerkUserId, {
            privateMetadata: {
              ...(user.privateMetadata as object),
              stripePlan: plan ?? (user.privateMetadata as Record<string, unknown>).stripePlan,
              stripeStatus: sub.status,
            },
          })
        }
        break
      }

      // Abonnement geannuleerd
      case 'customer.subscription.deleted': {
        const sub = event.data.object as Stripe.Subscription
        const clerkUserId = sub.metadata?.clerk_user_id

        if (clerkUserId) {
          const user = await clerk.users.getUser(clerkUserId)
          await clerk.users.updateUserMetadata(clerkUserId, {
            privateMetadata: {
              ...(user.privateMetadata as object),
              stripePlan: null,
              stripeStatus: 'cancelled',
              stripeSubscriptionId: null,
            },
          })
        }
        break
      }

      // Betaling mislukt
      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        const customerId = invoice.customer as string
        // Zoek de klant op en update status
        const customers = await stripe.customers.list({
          email: undefined,
          limit: 1,
        })
        // Gebruik customer metadata om Clerk user te vinden
        const customer = await stripe.customers.retrieve(customerId) as Stripe.Customer
        const clerkUserId = customer.metadata?.clerk_user_id
        if (clerkUserId) {
          const user = await clerk.users.getUser(clerkUserId)
          await clerk.users.updateUserMetadata(clerkUserId, {
            privateMetadata: {
              ...(user.privateMetadata as object),
              stripeStatus: 'past_due',
            },
          })
        }
        break
      }

      default:
        // Andere events negeren
        break
    }
  } catch (err) {
    console.error(`Fout bij verwerken van ${event.type}:`, err)
    return NextResponse.json({ error: 'Webhook verwerking mislukt' }, { status: 500 })
  }

  return NextResponse.json({ received: true })
}
