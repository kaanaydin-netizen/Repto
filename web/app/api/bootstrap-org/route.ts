/**
 * TIJDELIJK bootstrap-endpoint — koppelt de bestaande (geseede) organisatie
 * eenmalig aan de ingelogde gebruiker. VERWIJDEREN na gebruik.
 *
 * Werkwijze (volledig server-side, token blijft in de sessie):
 *  1. Claim de org via de backend met het Clerk-token → backend zet clerk_user_id = sub.
 *  2. Zet primaryOrgId in Clerk privateMetadata + de org-cookie, zodat getOrgId()
 *     ook na het retireren van NEXT_PUBLIC_ORG_ID de juiste org vindt.
 *
 * Tegelijk is dit de verificatie van de JWT-setup: faalt de claim met 401, dan
 * klopt CLERK_JWKS_URL/ISSUER op de backend niet.
 */
import { auth, clerkClient } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { ORG_COOKIE } from '@/lib/org'

export const dynamic = 'force-dynamic'

// De bestaande geseede org ("Test Installateur BV").
const SEED_ORG_ID = 'b4c28832-a365-4f99-a4dc-b25a8ea7da3a'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://repto-production.up.railway.app'

export async function GET() {
  const { userId, getToken } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Niet ingelogd — log eerst in op repto.be' }, { status: 401 })
  }

  const token = await getToken()
  if (!token) {
    return NextResponse.json({ error: 'Geen Clerk-token beschikbaar' }, { status: 401 })
  }

  // 1) Claim de org bij de backend (eigenaar komt uit het token).
  const claimRes = await fetch(`${API_URL}/organizations/${SEED_ORG_ID}/claim`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  const claimBody = await claimRes.text()
  if (!claimRes.ok) {
    return NextResponse.json(
      { step: 'claim', status: claimRes.status, detail: claimBody, hint: 'Bij 401: controleer CLERK_JWKS_URL/ISSUER op Railway.' },
      { status: 502 },
    )
  }

  // 2) Zet primaryOrgId in Clerk-metadata + cookie (zodat getOrgId() werkt).
  const clerk = await clerkClient()
  const user = await clerk.users.getUser(userId)
  const meta = user.privateMetadata as Record<string, unknown>
  const orgIds: string[] = Array.isArray(meta.orgIds) ? (meta.orgIds as string[]) : []
  if (!orgIds.includes(SEED_ORG_ID)) orgIds.push(SEED_ORG_ID)
  await clerk.users.updateUserMetadata(userId, {
    privateMetadata: { ...meta, primaryOrgId: SEED_ORG_ID, orgIds },
  })

  const response = NextResponse.json({
    ok: true,
    message: 'Organisatie gekoppeld aan je account. Ga naar /dashboard.',
    orgId: SEED_ORG_ID,
  })
  response.cookies.set(ORG_COOKIE, SEED_ORG_ID, {
    path: '/',
    httpOnly: false,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 24 * 365,
  })
  return response
}
