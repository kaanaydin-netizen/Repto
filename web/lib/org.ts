/**
 * lib/org.ts — server-side helper om de actieve org ID te bepalen.
 *
 * Prioriteitsvolgorde:
 * 1. Cookie 'repto_org_id' (gezet na org aanmaken / primary-org API)
 * 2. Env var NEXT_PUBLIC_ORG_ID (legacy / admin fallback)
 * 3. Leeg string (geen org geconfigureerd)
 */
import { cookies } from 'next/headers'

export const ORG_COOKIE = 'repto_org_id'

export async function getOrgId(): Promise<string> {
  try {
    const store = await cookies()
    const cookie = store.get(ORG_COOKIE)
    if (cookie?.value) return cookie.value
  } catch {
    // cookies() is niet beschikbaar buiten request context
  }
  return process.env.NEXT_PUBLIC_ORG_ID ?? ''
}
