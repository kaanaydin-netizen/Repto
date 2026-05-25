'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import {
  LayoutDashboard,
  MessageSquare,
  Calendar,
  Settings,
  Zap,
  Building2,
} from 'lucide-react'

const nav = [
  { href: '/dashboard',    label: 'Dashboard',    icon: LayoutDashboard },
  { href: '/gesprekken',   label: 'Gesprekken',   icon: MessageSquare },
  { href: '/afspraken',    label: 'Afspraken',    icon: Calendar },
  { href: '/klanten',      label: 'Klanten',      icon: Building2 },
  { href: '/instellingen', label: 'Instellingen', icon: Settings },
]

export default function Sidebar() {
  const path = usePathname()

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2.5 border-b border-gray-200 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <span className="text-lg font-bold text-gray-900">Repto</span>
        <span className="ml-auto rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-600">
          Beta
        </span>
      </div>

      {/* Navigatie */}
      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = path.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                active
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
              )}
            >
              <Icon className={clsx('h-4 w-4', active ? 'text-indigo-600' : 'text-gray-400')} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
            K
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-gray-900">Mijn bedrijf</p>
            <p className="truncate text-[10px] text-gray-500">Starter plan</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
