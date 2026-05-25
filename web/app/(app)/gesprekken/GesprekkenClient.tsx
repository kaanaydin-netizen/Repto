'use client'
import { useState, useEffect, useCallback } from 'react'
import { Search, RefreshCw } from 'lucide-react'
import ConversationCard from '@/components/ConversationCard'
import { api, ORG_ID } from '@/lib/api'
import type { Conversation, ConversationStatus } from '@/lib/types'

const FILTERS: { label: string; value: ConversationStatus | 'all' }[] = [
  { label: 'Alle',       value: 'all' },
  { label: 'Nieuw',      value: 'new' },
  { label: 'In gesprek', value: 'in_progress' },
  { label: 'Afspraak',   value: 'appointment_set' },
  { label: 'Gesloten',   value: 'closed' },
]

export default function GesprekkenClient({
  initialConversations,
}: {
  initialConversations: (Conversation & { last_message?: string })[]
}) {
  const [conversations, setConversations] = useState(initialConversations)
  const [activeFilter, setActiveFilter] = useState<ConversationStatus | 'all'>('all')
  const [search, setSearch] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  // Ververs de lijst
  const refresh = useCallback(async (silent = true) => {
    if (!ORG_ID) return
    if (!silent) setRefreshing(true)
    try {
      const fresh = await api.conversations.list(ORG_ID)
      setConversations(fresh)
      setLastUpdated(new Date())
    } catch {
      // Stil falen
    } finally {
      if (!silent) setRefreshing(false)
    }
  }, [])

  // Auto-refresh elke 30 seconden
  useEffect(() => {
    const timer = setInterval(() => refresh(true), 30_000)
    return () => clearInterval(timer)
  }, [refresh])

  const filtered = conversations.filter(c => {
    const matchStatus = activeFilter === 'all' || c.status === activeFilter
    const q = search.toLowerCase()
    const matchSearch =
      !q ||
      c.wa_contact_name?.toLowerCase().includes(q) ||
      c.wa_contact_phone.includes(q) ||
      c.last_message?.toLowerCase().includes(q)
    return matchStatus && matchSearch
  })

  function count(val: ConversationStatus | 'all') {
    if (val === 'all') return conversations.length
    return conversations.filter(c => c.status === val).length
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gesprekken</h1>
          <p className="mt-1 text-sm text-gray-500">
            {conversations.length} gesprekken totaal ·{' '}
            {count('new')} nieuwe leads ·{' '}
            <span className="text-gray-400">
              bijgewerkt om {lastUpdated.toLocaleTimeString('nl-BE', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </p>
        </div>
        <button
          onClick={() => refresh(false)}
          disabled={refreshing}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Laden…' : 'Vernieuwen'}
        </button>
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
        <div className="flex flex-wrap gap-1.5">
          {FILTERS.map(f => (
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
              <span className="ml-1.5 opacity-60">{count(f.value)}</span>
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
