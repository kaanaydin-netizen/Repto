import { auth, clerkClient } from '@clerk/nextjs/server'
import { NextRequest, NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'

export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Niet ingelogd' }, { status: 401 })
    }

    const clerk = await clerkClient()
    const user = await clerk.users.getUser(userId)
    const meta = user.privateMetadata as { stripeCustomerId?: string }

    if (!meta.stripeCustomerId) {
      return NextResponse.json(
        { error: 'Geen actief abonnement gevonden' },
        { status: 400 }
      )
    }

    const origin = request.headers.get('origin') ?? 'https://repto-three.vercel.app'

    const portalSession = await stripe.billingPortal.sessions.create({
      customer: meta.stripeCustomerId,
      return_url: `${origin}/billing`,
    })

    return NextResponse.json({ url: portalSession.url })
  } catch (err) {
    console.error('portal error:', err)
    return NextResponse.json(
      { error: 'Customer portal openen mislukt.' },
      { status: 500 }
    )
  }
}
