import { clerkMiddleware } from '@clerk/nextjs/server'

/**
 * Clerk-middleware — VERPLICHT in Clerk v7 zodat `auth()` in server components
 * de sessie kan uitlezen. Zonder dit gooit `auth()` in (app)/layout.tsx een fout,
 * wat een redirect-loop /sign-in ↔ /dashboard veroorzaakt.
 *
 * Bewust GEEN `auth.protect()` hier: de routebescherming gebeurt in
 * `app/(app)/layout.tsx`. Zo blijven de publieke homepage `/` en de publieke
 * `/api/contact`-route gewoon bereikbaar zonder login.
 *
 * De keys worden automatisch gelezen uit NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
 * en CLERK_SECRET_KEY (staan in Vercel env).
 */
export default clerkMiddleware()

export const config = {
  matcher: [
    // Alle routes behalve Next.js internals en statische bestanden
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
