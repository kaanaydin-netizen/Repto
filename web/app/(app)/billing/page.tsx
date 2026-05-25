import { auth, clerkClient } from '@clerk/nextjs/server'
import BillingClient from './BillingClient'

export const dynamic = 'force-dynamic'

// Type voor Stripe metadata opgeslagen in Clerk
export interface StripeMetadata {
  stripeCustomerId?: string
  stripePlan?: string
  stripeSubscriptionId?: string
  stripeStatus?: string
}

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{ success?: string; cancelled?: string }>
}) {
  const { userId } = await auth()
  const params = await searchParams

  // Lees huidige subscription status uit Clerk metadata
  let meta: StripeMetadata = {}
  if (userId) {
    try {
      const clerk = await clerkClient()
      const user = await clerk.users.getUser(userId)
      meta = (user.privateMetadata as StripeMetadata) ?? {}
    } catch {
      // Geen metadata beschikbaar — verder met lege state
    }
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Abonnement</h1>
        <p className="mt-1 text-sm text-gray-500">
          Start met 7 dagen gratis · Creditcard vereist · Daarna automatisch verlengd · Opzeggen wanneer je wil.
        </p>
      </div>

      <BillingClient
        meta={meta}
        successParam={params.success === 'true'}
        cancelledParam={params.cancelled === 'true'}
      />
    </div>
  )
}
