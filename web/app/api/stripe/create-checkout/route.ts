import { auth, clerkClient } from '@clerk/nextjs/server'
import { NextRequest, NextResponse } from 'next/server'
import { getStripe, PLANS, type PlanKey } from '@/lib/stripe'

// Price ID per plan — gelezen uit env vars
const PRICE_IDS: Record<PlanKey, string | undefined> = {
  starter: process.env.STRIPE_PRICE_STARTER,
  groei:   process.env.STRIPE_PRICE_GROEI,
  agency:  process.env.STRIPE_PRICE_AGENCY,
}

export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Niet ingelogd' }, { status: 401 })
    }

    const { plan } = await request.json() as { plan: PlanKey }

    if (!PLANS[plan]) {
      return NextResponse.json({ error: 'Ongeldig plan' }, { status: 400 })
    }

    const priceId = PRICE_IDS[plan]
    if (!priceId) {
      return NextResponse.json(
        { error: `STRIPE_PRICE_${plan.toUpperCase()} is niet geconfigureerd in Vercel.` },
        { status: 400 }
      )
    }

    const stripe = getStripe()

    // Haal Clerk user op om stripeCustomerId te lezen
    const clerk = await clerkClient()
    const user = await clerk.users.getUser(userId)
    const meta = user.privateMetadata as {
      stripeCustomerId?: string
      stripePlan?: string
      stripeSubscriptionId?: string
    }

    // Haal bestaande Stripe Customer op of maak een nieuwe aan
    let customerId: string | undefined = meta.stripeCustomerId

    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.emailAddresses[0]?.emailAddress,
        name: user.fullName ?? user.firstName ?? undefined,
        metadata: { clerk_user_id: userId },
      })
      customerId = customer.id

      // Sla customer ID op in Clerk metadata
      await clerk.users.updateUserMetadata(userId, {
        privateMetadata: { ...meta, stripeCustomerId: customer.id },
      })
    }

    // Bepaal origin voor redirect URLs
    const origin = request.headers.get('origin') ?? process.env.NEXT_PUBLIC_SITE_URL ?? 'https://repto.be'

    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${origin}/billing?success=true&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/billing?cancelled=true`,
      metadata: { clerk_user_id: userId, plan },
      subscription_data: {
        metadata: { clerk_user_id: userId, plan },
        trial_period_days: 7,
      },
      payment_method_collection: 'always',   // creditcard verplicht ook bij trial
      allow_promotion_codes: true,
      locale: 'nl',
    })

    return NextResponse.json({ url: session.url })
  } catch (err) {
    console.error('create-checkout error:', err)
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'Checkout aanmaken mislukt.' },
      { status: 500 }
    )
  }
}
