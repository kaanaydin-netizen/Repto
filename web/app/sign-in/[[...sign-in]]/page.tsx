import { SignIn } from '@clerk/nextjs'
import { Zap } from 'lucide-react'

export default function SignInPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <span className="text-2xl font-bold text-gray-900">Repto</span>
      </div>

      <SignIn
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
    </div>
  )
}
