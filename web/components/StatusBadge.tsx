import clsx from 'clsx'
import type { ConversationStatus } from '@/lib/types'

const config: Record<ConversationStatus, { label: string; classes: string }> = {
  new:             { label: 'Nieuw',      classes: 'bg-amber-100 text-amber-800 ring-amber-200' },
  in_progress:     { label: 'In gesprek', classes: 'bg-blue-100 text-blue-800 ring-blue-200' },
  appointment_set: { label: 'Afspraak',   classes: 'bg-green-100 text-green-800 ring-green-200' },
  closed:          { label: 'Gesloten',   classes: 'bg-gray-100 text-gray-600 ring-gray-200' },
}

export default function StatusBadge({ status }: { status: ConversationStatus }) {
  const { label, classes } = config[status]
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset', classes)}>
      {label}
    </span>
  )
}
