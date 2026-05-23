import clsx from 'clsx'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  sub?: string
  icon: LucideIcon
  color?: 'indigo' | 'amber' | 'green' | 'blue'
}

const colors = {
  indigo: { bg: 'bg-indigo-50', icon: 'text-indigo-600', ring: 'ring-indigo-100' },
  amber:  { bg: 'bg-amber-50',  icon: 'text-amber-600',  ring: 'ring-amber-100' },
  green:  { bg: 'bg-green-50',  icon: 'text-green-600',  ring: 'ring-green-100' },
  blue:   { bg: 'bg-blue-50',   icon: 'text-blue-600',   ring: 'ring-blue-100' },
}

export default function StatCard({ title, value, sub, icon: Icon, color = 'indigo' }: StatCardProps) {
  const c = colors[color]
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-gray-400">{sub}</p>}
        </div>
        <div className={clsx('rounded-lg p-2.5 ring-1', c.bg, c.ring)}>
          <Icon className={clsx('h-5 w-5', c.icon)} />
        </div>
      </div>
    </div>
  )
}
