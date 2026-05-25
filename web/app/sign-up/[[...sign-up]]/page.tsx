import { SignUp } from '@clerk/nextjs'
import { Zap } from 'lucide-react'

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <span className="text-2xl font-bold text-gray-900">Repto</span>
      </div>

      {/* Trial badge */}
      <div className="mb-6 flex items-center gap-2 rounded-full border border-green-200 bg-green-50 px-4 py-1.5 text-sm font-medium text-green-700">
        ✨ 7 dagen gratis proberen — geen kosten tot dag 7
      </div>

      <SignUp
        appearance={{
          elements: {
            rootBox: 'w-full max-w-sm',
            card: 'shadow-sm border border-gray-200 rounded-2xl',
            headerTitle: 'text-gray-900 font-bold',
            headerSubtitle: 'text-gray-500',
            formButtonPrimary:
              'bg-indigo-600 hover:bg-indigo-700 text-sm font-semibold',
            footerActionLink: 'text-indigo-600 hover:text-indigo-700',
          },
        }}
      />

      <p className="mt-6 text-center text-xs text-gray-400">
        Al een account?{' '}
        <a href="/sign-in" className="font-medium text-indigo-600 hover:underline">
          Aanmelden
        </a>
      </p>
    </div>
  )
}
