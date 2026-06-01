import { auth, clerkClient } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import Sidebar from '@/components/Sidebar'
import { ORG_COOKIE } from '@/lib/org'

export const dynamic = 'force-dynamic'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let userId: string | null = null

  try {
    const authResult = await auth()
    userId = authResult.userId
  } catch {
    redirect('/sign-in')
  }

  if (!userId) redirect('/sign-in')

  // ── Org-bepaling ───────────────────────────────────────────────────────────
  // De gebruiker heeft een org via cookie, Clerk-metadata (primaryOrgId) of env.
  // Heeft hij niets én is er geen env-fallback → nieuwe gebruiker → onboarding.
  // (De bestaande geseede org wordt eenmalig handmatig aan de eigenaar gekoppeld;
  //  nieuwe klanten krijgen hun org via de onboarding-wizard, die clerk_user_id
  //  server-side uit het token zet.)
  try {
    const store = await cookies()
    const hasCookie = !!store.get(ORG_COOKIE)?.value
    const hasEnvOrg = !!process.env.NEXT_PUBLIC_ORG_ID
    if (!hasCookie && !hasEnvOrg) {
      const clerk = await clerkClient()
      const user = await clerk.users.getUser(userId!)
      const meta = user.privateMetadata as Record<string, unknown>
      const primaryOrgId = meta.primaryOrgId as string | undefined
      if (!primaryOrgId) {
        redirect('/onboarding')
      }
    }
  } catch (e: unknown) {
    // Als de fout een redirect is, gooi die door
    if (e && typeof e === 'object' && 'digest' in e) throw e
    // Anders: stil falen — cookie/metadata/env valt terug op de normale flow
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
