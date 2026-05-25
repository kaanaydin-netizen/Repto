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

  // ── Org cookie syncen met Clerk metadata ──────────────────────────────────
  try {
    const store = await cookies()
    const hasCookie = !!store.get(ORG_COOKIE)?.value
    const hasEnvOrg = !!process.env.NEXT_PUBLIC_ORG_ID

    // Als nog geen cookie én geen env var → lees Clerk metadata voor primaryOrgId
    if (!hasCookie && !hasEnvOrg) {
      const clerk = await clerkClient()
      const user = await clerk.users.getUser(userId!)
      const meta = user.privateMetadata as Record<string, unknown>
      const primaryOrgId = meta.primaryOrgId as string | undefined

      if (!primaryOrgId) {
        // Nieuwe gebruiker zonder org → naar onboarding
        redirect('/onboarding')
      }
      // Cookie wordt gezet via de /api/user/primary-org route na org-aanmaken.
      // Hier doen we geen server-side cookie set (niet mogelijk in layout zonder response object).
      // De onboarding flow zorgt ervoor dat de cookie al gezet is voor dit punt.
    }
  } catch (e: unknown) {
    // Als de fout een redirect is, gooi die door
    if (e && typeof e === 'object' && 'digest' in e) throw e
    // Anders: stil falen — env var of cookie valt terug op de normale flow
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
