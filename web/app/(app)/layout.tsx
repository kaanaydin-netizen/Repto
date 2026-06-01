import { auth, clerkClient } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import Sidebar from '@/components/Sidebar'
import { ORG_COOKIE } from '@/lib/org'
import { api } from '@/lib/api'

export const dynamic = 'force-dynamic'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let userId: string | null = null
  let getToken: (() => Promise<string | null>) | null = null

  try {
    const authResult = await auth()
    userId = authResult.userId
    getToken = authResult.getToken
  } catch {
    redirect('/sign-in')
  }

  if (!userId) redirect('/sign-in')

  // ── Org koppelen aan deze gebruiker (Clerk metadata) ───────────────────────
  // Doel: de gebruiker heeft een primaryOrgId in zijn metadata. Zo niet:
  //  1. claim een nog-ongeclaimde org (eenmalig, bv. de geseede org), of
  //  2. stuur naar onboarding als er niets te claimen valt.
  try {
    const store = await cookies()
    const hasCookie = !!store.get(ORG_COOKIE)?.value
    if (!hasCookie) {
      const clerk = await clerkClient()
      const user = await clerk.users.getUser(userId!)
      const meta = user.privateMetadata as Record<string, unknown>
      let primaryOrgId = meta.primaryOrgId as string | undefined

      if (!primaryOrgId) {
        // Probeer een ongeclaimde org te claimen (org zonder clerk_user_id).
        const token = getToken ? await getToken() : null
        const orgs = await api.organizations.list(token).catch(() => [])
        const claimable = orgs.find(o => !o.clerk_user_id)
        if (claimable) {
          await api.organizations.claim(claimable.id, token).catch(() => null)
          primaryOrgId = claimable.id
          // Zet als primaire org in Clerk-metadata (cookie volgt via /api/user/primary-org).
          await clerk.users.updateUserMetadata(userId!, {
            privateMetadata: {
              ...meta,
              primaryOrgId,
              orgIds: [...(Array.isArray(meta.orgIds) ? meta.orgIds as string[] : []), claimable.id],
            },
          })
        }
      }

      if (!primaryOrgId) {
        // Niets te claimen → nieuwe gebruiker → onboarding.
        redirect('/onboarding')
      }
    }
  } catch (e: unknown) {
    // Als de fout een redirect is, gooi die door
    if (e && typeof e === 'object' && 'digest' in e) throw e
    // Anders: stil falen — cookie/metadata valt terug op de normale flow
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
