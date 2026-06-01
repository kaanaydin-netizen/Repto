/**
 * lib/org.ts — server-side helper om de actieve org ID te bepalen.
 *
 * Prioriteitsvolgorde:
 * 1. Cookie 'repto_org_id' (gezet na org aanmaken / primary-org API)
 * 2. Clerk privateMetadata.primaryOrgId (multi-tenant, gezet bij claim/onboarding)
 * 3. Env var NEXT_PUBLIC_ORG_ID (legacy / admin fallback — wordt geretireerd)
 * 4. Leeg string (geen org geconfigureerd)
 */
import { cookies } from 'next/headers'
import { auth, clerkClient } from '@clerk/nextjs/server'

export const ORG_COOKIE = 'repto_org_id'

export async function getOrgId(): Promise<string> {
  try {
    const store = await cookies()
    const cookie = store.get(ORG_COOKIE)
    if (cookie?.value) return cookie.value
  } catch {
    // cookies() is niet beschikbaar buiten request context
  }

  // Clerk-metadata: primaryOrgId van de ingelogde gebruiker.
  try {
    const { userId } = await auth()
    if (userId) {
      const clerk = await clerkClient()
      const user = await clerk.users.getUser(userId)
      const primaryOrgId = (user.privateMetadata as Record<string, unknown>).primaryOrgId
      if (typeof primaryOrgId === 'string' && primaryOrgId) return primaryOrgId
    }
  } catch {
    // auth/clerk niet beschikbaar — val terug op env var
  }

  return process.env.NEXT_PUBLIC_ORG_ID ?? ''
}
