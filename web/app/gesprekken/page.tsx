'use client'
import { useState } from 'react'
import { Search } from 'lucide-react'
import ConversationCard from '@/components/ConversationCard'
import { MOCK_CONVERSATIONS } from '@/lib/api'
import type { ConversationStatus } from '@/lib/types'

const filters: { label: string; value: ConversationStatus | 'all' }[] = [
  { label: 'Alle',       value: 'all' },
  { label: 'Nieuw',      value: 'new' },
  { label: 'In gesprek', value: 'in_progress' },
  { label: 'Afspraak',   value: 'appointment_set' },
  { label: 'Gesloten',   value: 'closed' },
]

export default function GesprekkenPage() {
  const [activeFilter, setActiveFilter] = useState<ConversationStatus | 'all'>('all')
  const [search, setSearch] = useState('')

  const filtered = MOCK_CONVERSATIONS.filter(c => {
    const matchStatus = activeFilter === 'all' || c.status === activeFilter
    const q = search.toLowerCase()
    const matchSearch = !q ||
      c.wa_contact_name?.toLowerCase().includes(q) ||
      c.wa_contact_phone.includes(q) ||
      c.last_message?.toLowerCase().includes(q)
    return matchStatus && matchSearch
  })

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Gesprekken</h1>
        <p className="mt-1 text-sm text-gray-500">
          {MOCK_CONVERSATIONS.length} gesprekken totaal · {MOCK_CONVERSATIONS.filter(c => c.status === 'new').length} nieuwe leads
        </p>
      </div>

      {/* Zoekbalk + filters */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Zoek op naam, nummer of bericht…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {filters.map(f => (
            <button
              key={f.value}
              onClick={() => setActiveFilter(f.value)}
              className={`rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                activeFilter === f.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f.label}
              <span className="ml-1.5 opacity-60">
                {f.value === 'all'
                  ? MOCK_CONVERSATIONS.length
                  : MOCK_CONVERSATIONS.filter(c => c.status === f.value).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Lijst */}
      {filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map(conv => (
            <ConversationCard key={conv.id} conv={conv} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 text-center">
          <span className="text-4xl">💬</span>
          <p className="mt-3 font-medium text-gray-900">Geen gesprekken gevonden</p>
          <p className="mt-1 text-sm text-gray-500">Pas je filter of zoekopdracht aan.</p>
        </div>
      )}
    </div>
  )
}
