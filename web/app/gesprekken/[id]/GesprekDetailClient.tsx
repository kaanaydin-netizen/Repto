'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Phone, Bot } from 'lucide-react'
import MessageBubble from '@/components/MessageBubble'
import StatusBadge from '@/components/StatusBadge'
import { api } from '@/lib/api'
import type { Conversation, Message, ConversationStatus } from '@/lib/types'

const STATUS_LABELS: Record<ConversationStatus, string> = {
  new:              'Nieuw',
  in_progress:      'In gesprek',
  appointment_set:  'Afspraak',
  closed:           'Gesloten',
}

export default function GesprekDetailClient({
  conv: initialConv,
  initialMessages,
}: {
  conv: Conversation
  initialMessages: Message[]
}) {
  const router = useRouter()
  const [conv, setConv] = useState(initialConv)
  const [saving, setSaving] = useState(false)

  async function changeStatus(status: ConversationStatus) {
    if (status === conv.status || saving) return
    setSaving(true)
    try {
      await api.conversations.updateStatus(conv.id, status)
      setConv(prev => ({ ...prev, status }))
    } catch (e) {
      console.error('Status update mislukt:', e)
    } finally {
      setSaving(false)
    }
  }

  const initials = (conv.wa_contact_name ?? conv.wa_contact_phone)[0].toUpperCase()

  return (
    <div className="flex h-screen flex-col">
      {/* Topbar */}
      <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <button
          onClick={() => router.back()}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 font-semibold text-indigo-700">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-gray-900">
            {conv.wa_contact_name ?? conv.wa_contact_phone}
          </p>
          <p className="text-xs text-gray-500">{conv.wa_contact_phone}</p>
        </div>
        <StatusBadge status={conv.status} />
        <a
          href={`tel:${conv.wa_contact_phone}`}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
        >
          <Phone className="h-4 w-4" />
        </a>
      </div>

      {/* Berichten */}
      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-4 space-y-4">
        <div className="flex justify-center">
          <span className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-600 ring-1 ring-indigo-100">
            <Bot className="h-3 w-3" />
            Repto AI beantwoordt automatisch
          </span>
        </div>

        {initialMessages.length === 0 ? (
          <p className="text-center text-sm text-gray-400 mt-8">Geen berichten gevonden.</p>
        ) : (
          initialMessages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))
        )}
      </div>

      {/* Status balk */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <p className="mb-2 text-xs font-medium text-gray-500">Status wijzigen:</p>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(STATUS_LABELS) as ConversationStatus[]).map(s => (
            <button
              key={s}
              onClick={() => changeStatus(s)}
              disabled={saving}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ring-1 ring-inset disabled:opacity-50 ${
                conv.status === s
                  ? 'bg-indigo-600 text-white ring-indigo-600'
                  : 'bg-white text-gray-600 ring-gray-200 hover:bg-gray-50'
              }`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
