/**
 * POST /api/user/primary-org
 * Sla de primaire org ID op in Clerk privateMetadata + zet een cookie.
 *
 * GET /api/user/primary-org
 * Lees de primaire org ID uit Clerk metadata (of env var als fallback).
 */
import { auth, clerkClient } from '@clerk/nextjs/server'
import { NextRequest, NextResponse } from 'next/server'
import { ORG_COOKIE } from '@/lib/org'

export async function POST(request: NextRequest) {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Niet ingelogd' }, { status: 401 })

  const { orgId } = await request.json() as { orgId: string }
  if (!orgId) return NextResponse.json({ error: 'orgId ontbreekt' }, { status: 400 })

  // Sla op in Clerk metadata
  const clerk = await clerkClient()
  const user = await clerk.users.getUser(userId)
  const meta = user.privateMetadata as Record<string, unknown>
  const orgIds: string[] = Array.isArray(meta.orgIds) ? meta.orgIds as string[] : []
  if (!orgIds.includes(orgId)) orgIds.push(orgId)

  await clerk.users.updateUserMetadata(userId, {
    privateMetadata: { ...meta, primaryOrgId: orgId, orgIds },
  })

  // Zet cookie (1 jaar)
  const response = NextResponse.json({ ok: true, orgId })
  response.cookies.set(ORG_COOKIE, orgId, {
    path: '/',
    httpOnly: false,        // client-side leesbaar voor reload
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 24 * 365,
  })
  return response
}

export async function GET() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Niet ingelogd' }, { status: 401 })

  const clerk = await clerkClient()
  const user = await clerk.users.getUser(userId)
  const meta = user.privateMetadata as Record<string, unknown>

  const orgId = (meta.primaryOrgId as string | undefined)
    ?? process.env.NEXT_PUBLIC_ORG_ID
    ?? null

  return NextResponse.json({ orgId })
}
