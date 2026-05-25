import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/Sidebar'

export const dynamic = 'force-dynamic'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let userId: string | null = null

  try {
    const authResult = await auth()
    userId = authResult.userId
  } catch {
    // auth() gooit als Clerk niet correct is geconfigureerd
    redirect('/sign-in')
  }

  if (!userId) {
    redirect('/sign-in')
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
