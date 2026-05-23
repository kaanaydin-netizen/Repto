import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { nl } from 'date-fns/locale'
import { User, CheckCircle2 } from 'lucide-react'
import StatusBadge from './StatusBadge'
import type { Conversation } from '@/lib/types'

export default function ConversationCard({ conv }: { conv: Conversation }) {
  return (
    <Link
      href={`/gesprekken/${conv.id}`}
      className="flex items-start gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md"
    >
      {/* Avatar */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700">
        <User className="h-5 w-5" />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate font-semibold text-gray-900">
            {conv.wa_contact_name ?? conv.wa_contact_phone}
          </p>
          <span className="shrink-0 text-xs text-gray-400">
            {formatDistanceToNow(new Date(conv.updated_at), { addSuffix: true, locale: nl })}
          </span>
        </div>
        <p className="mt-0.5 truncate text-sm text-gray-500">{conv.last_message ?? '—'}</p>
        <div className="mt-2 flex items-center gap-2">
          <StatusBadge status={conv.status} />
          {conv.crm_synced_at && (
            <span className="flex items-center gap-1 text-[10px] text-green-600">
              <CheckCircle2 className="h-3 w-3" /> Synced
            </span>
          )}
          <span className="ml-auto text-[10px] text-gray-400">{conv.wa_contact_phone}</span>
        </div>
      </div>
    </Link>
  )
}
