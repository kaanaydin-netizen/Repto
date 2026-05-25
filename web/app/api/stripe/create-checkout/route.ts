import { auth, clerkClient } from '@clerk/nextjs/server'
import { NextRequest, NextResponse } from 'next/server'
import { stripe, PLANS, type PlanKey } from '@/lib/stripe'

export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Niet ingelogd' }, { status: 401 })
    }

    const { plan } = await request.json() as { plan: PlanKey }
    const planConfig = PLANS[plan]
    if (!planConfig || !planConfig.priceId) {
      return NextResponse.json({ error: 'Ongeldig plan of priceId niet geconfigureerd' }, { status: 400 })
    }

    // Haal Clerk user op om stripe_customer_id te lezen
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

      // Sla customer ID direct op in Clerk metadata
      await clerk.users.updateUserMetadata(userId, {
        privateMetadata: { ...meta, stripeCustomerId: customer.id },
      })
    }

    // Bepaal success / cancel URL op basis van het request origin
    const origin = request.headers.get('origin') ?? 'https://repto-three.vercel.app'

    // Maak een Checkout Session aan
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: planConfig.priceId, quantity: 1 }],
      success_url: `${origin}/billing?success=true&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/billing?cancelled=true`,
      metadata: { clerk_user_id: userId, plan },
      subscription_data: { metadata: { clerk_user_id: userId, plan } },
      allow_promotion_codes: true,
      locale: 'nl',
    })

    return NextResponse.json({ url: session.url })
  } catch (err) {
    console.error('create-checkout error:', err)
    return NextResponse.json(
      { error: 'Checkout aanmaken mislukt. Probeer opnieuw.' },
      { status: 500 }
    )
  }
}
