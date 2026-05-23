'use client'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Phone, MoreVertical, Send, Bot } from 'lucide-react'
import MessageBubble from '@/components/MessageBubble'
import StatusBadge from '@/components/StatusBadge'
import { MOCK_CONVERSATIONS, MOCK_MESSAGES } from '@/lib/api'

export default function GesprekDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const conv = MOCK_CONVERSATIONS.find(c => c.id === id) ?? MOCK_CONVERSATIONS[0]
  const messages = MOCK_MESSAGES.filter(m => m.conversation_id === id).length > 0
    ? MOCK_MESSAGES.filter(m => m.conversation_id === id)
    : MOCK_MESSAGES // toon altijd mock berichten

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
          {(conv.wa_contact_name ?? conv.wa_contact_phone)[0].toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate font-semibold text-gray-900">
            {conv.wa_contact_name ?? conv.wa_contact_phone}
          </p>
          <p className="text-xs text-gray-500">{conv.wa_contact_phone}</p>
        </div>
        <StatusBadge status={conv.status} />
        <button className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100">
          <Phone className="h-4 w-4" />
        </button>
        <button className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100">
          <MoreVertical className="h-4 w-4" />
        </button>
      </div>

      {/* Berichten */}
      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-4 space-y-4">
        {/* AI-badge */}
        <div className="flex justify-center">
          <span className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-600 ring-1 ring-indigo-100">
            <Bot className="h-3 w-3" />
            Repto AI beantwoordt automatisch
          </span>
        </div>

        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
      </div>

      {/* Status actie-balk */}
      <div className="border-t border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium text-gray-500">Status wijzigen:</span>
          {(['new', 'in_progress', 'appointment_set', 'closed'] as const).map(s => (
            <button
              key={s}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ring-1 ring-inset ${
                conv.status === s
                  ? 'bg-indigo-600 text-white ring-indigo-600'
                  : 'bg-white text-gray-600 ring-gray-200 hover:bg-gray-50'
              }`}
            >
              {s === 'new' ? 'Nieuw' : s === 'in_progress' ? 'In gesprek' : s === 'appointment_set' ? 'Afspraak' : 'Gesloten'}
            </button>
          ))}
        </div>

        {/* Handmatig antwoord (override AI) */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Stuur manueel een bericht (overschrijft AI)…"
            className="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <button className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700">
            <Send className="h-4 w-4" />
            Sturen
          </button>
        </div>
      </div>
    </div>
  )
}
