import { clerkMiddleware } from '@clerk/nextjs/server'

// Minimale middleware — alleen Clerk auth-context koppelen aan requests.
// Route-bescherming gebeurt in app/(app)/layout.tsx (Node.js runtime).
export default clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
