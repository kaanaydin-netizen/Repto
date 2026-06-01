/**
 * Server-side helper om het Clerk session-token op te halen voor backend-calls.
 * Gebruik in server components: `const token = await getServerToken()`.
 * Client components gebruiken in plaats hiervan `useAuth().getToken()`.
 */
import { auth } from '@clerk/nextjs/server'

export async function getServerToken(): Promise<string | null> {
  try {
    const { getToken } = await auth()
    return await getToken()
  } catch {
    return null
  }
}
