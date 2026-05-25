'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Phone, Bot, RefreshCw, CheckCircle2 } from 'lucide-react'
import { format, isToday, isYesterday, isSameDay } from 'date-fns'
import { nl } from 'date-fns/locale'
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

// ─── Datumscheidingslabel ─────────────────────────────────────────────────────

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr)
  if (isToday(d))     return 'Vandaag'
  if (isYesterday(d)) return 'Gisteren'
  return format(d, 'd MMMM yyyy', { locale: nl })
}

function DateSeparator({ dateStr }: { dateStr: string }) {
  return (
    <div className="flex items-center gap-3 py-1">
      <div className="h-px flex-1 bg-gray-200" />
      <span className="rounded-full bg-gray-100 px-3 py-0.5 text-[10px] font-medium text-gray-500">
        {formatDateLabel(dateStr)}
      </span>
      <div className="h-px flex-1 bg-gray-200" />
    </div>
  )
}

// ─── Hoofd component ──────────────────────────────────────────────────────────

export default function GesprekDetailClient({
  conv: initialConv,
  initialMessages,
}: {
  conv: Conversation
  initialMessages: Message[]
}) {
  const router = useRouter()
  const [conv,     setConv]     = useState(initialConv)
  const [messages, setMessages] = useState(initialMessages)
  const [saving,   setSaving]   = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const bottomRef    = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // ─── Scroll helpers ──────────────────────────────────────────────────────

  const scrollToBottom = useCallback((smooth = false) => {
    bottomRef.current?.scrollIntoView({
      behavior: smooth ? 'smooth' : 'instant',
      block: 'end',
    })
  }, [])

  function isAtBottom() {
    const el = scrollAreaRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < 120
  }

  // Eerste keer direct naar onderen
  useEffect(() => {
    scrollToBottom(false)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll mee als nieuwe berichten binnenkomen én gebruiker al onderin zat
  useEffect(() => {
    if (isAtBottom()) scrollToBottom(true)
  }, [messages.length]) // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Auto-refresh elke 10s ───────────────────────────────────────────────

  const refreshMessages = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true)
    try {
      const [freshMsgs, freshConv] = await Promise.all([
        api.conversations.messages(conv.id),
        api.conversations.get(conv.id),
      ])
      setMessages(freshMsgs)
      setConv(freshConv)
    } catch {
      // Stil falen
    } finally {
      if (showSpinner) setRefreshing(false)
    }
  }, [conv.id])

  useEffect(() => {
    const timer = setInterval(() => refreshMessages(false), 10_000)
    return () => clearInterval(timer)
  }, [refreshMessages])

  // ─── Status wijzigen ─────────────────────────────────────────────────────

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

  // ─── Berichten groeperen per dag ─────────────────────────────────────────

  const groups: { dateStr: string; msgs: Message[] }[] = []
  for (const msg of messages) {
    const last = groups[groups.length - 1]
    if (!last || !isSameDay(new Date(msg.sent_at), new Date(last.dateStr))) {
      groups.push({ dateStr: msg.sent_at, msgs: [msg] })
    } else {
      last.msgs.push(msg)
    }
  }

  const initials = (conv.wa_contact_name ?? conv.wa_contact_phone)[0].toUpperCase()
  const isClosed = conv.status === 'closed'

  // ─── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen flex-col overflow-hidden">

      {/* ── Topbar ───────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-6 py-3.5 shadow-sm">
        <button
          onClick={() => router.back()}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>

        {/* Avatar */}
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-100 font-bold text-indigo-700">
          {initials}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-gray-900">
            {conv.wa_contact_name ?? conv.wa_contact_phone}
          </p>
          <p className="text-xs text-gray-400">
            {conv.wa_contact_phone}
            {conv.crm_synced_at && (
              <span className="ml-2 text-green-500">· ✓ Airtable</span>
            )}
          </p>
        </div>

        {/* Acties */}
        <StatusBadge status={conv.status} />

        <button
          onClick={() => refreshMessages(true)}
          disabled={refreshing}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
          title="Berichten verversen"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>

        <a
          href={`tel:${conv.wa_contact_phone}`}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-green-600 transition-colors"
          title="Bellen"
        >
          <Phone className="h-4 w-4" />
        </a>
      </div>

      {/* ── Berichten ────────────────────────────────────────────────────── */}
      <div
        ref={scrollAreaRef}
        className="flex-1 overflow-y-auto bg-gray-50 px-4 py-4 sm:px-6"
      >
        {/* AI banner */}
        <div className="mb-4 flex justify-center">
          <span className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-4 py-1.5 text-xs font-medium text-indigo-600 ring-1 ring-indigo-100">
            <Bot className="h-3.5 w-3.5" />
            Repto AI beantwoordt automatisch · elke 10s bijgewerkt
          </span>
        </div>

        {messages.length === 0 ? (
          <p className="mt-8 text-center text-sm text-gray-400">
            Nog geen berichten in dit gesprek.
          </p>
        ) : (
          <div className="space-y-1">
            {groups.map((group, gi) => (
              <div key={gi}>
                {/* Datumscheiding */}
                <DateSeparator dateStr={group.dateStr} />
                <div className="space-y-3 py-2">
                  {group.msgs.map(msg => (
                    <MessageBubble key={msg.id} msg={msg} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Gesprek afgesloten banner */}
        {isClosed && (
          <div className="mt-4 flex items-center justify-center gap-2 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
            Gesprek afgerond · Lead gesynchroniseerd naar Airtable
          </div>
        )}

        {/* Scroll anker */}
        <div ref={bottomRef} className="h-4" />
      </div>

      {/* ── Status balk ──────────────────────────────────────────────────── */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <p className="mr-1 text-xs font-medium text-gray-500">Status:</p>
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
          <span className="ml-auto text-[10px] text-gray-300">
            {format(new Date(conv.updated_at), 'd MMM HH:mm', { locale: nl })}
          </span>
        </div>
      </div>
    </div>
  )
}
