'use client'

import { useEffect, useRef, useState } from 'react'
import { Bot, MessageCircle, Send, User, X, Loader2 } from 'lucide-react'
import clsx from 'clsx'

const SESSION_KEY = 'repto_chat_session'
const GREETING = 'Hallo! Ik ben de AI-receptionist van Repto. Waarmee kan ik je helpen? Stel gerust je vraag of vertel wat je zoekt.'

type ChatMessage = { role: 'user' | 'assistant'; text: string }

/**
 * Zwevende web-chat (increment 2, slice 2c): demonstreert het product live op de site.
 * Conversationeel — dezelfde AI-lus als WhatsApp, maar synchroon over een sessie-id dat
 * het gesprek + geheugen aan backend-zijde vasthoudt. Praat via /api/chat (server-side
 * proxy die org_id injecteert), nooit rechtstreeks met de backend.
 *
 * Verbergt zichzelf wanneer de intake niet geconfigureerd is (proxy geeft 503).
 */
export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'assistant', text: GREETING }])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [closed, setClosed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hidden, setHidden] = useState(false)

  const sessionId = useRef<string>('')
  const scrollRef = useRef<HTMLDivElement>(null)

  // Sessie-id eenmalig vastleggen (overleeft herladen binnen hetzelfde tabblad).
  useEffect(() => {
    let id = sessionStorage.getItem(SESSION_KEY)
    if (!id) {
      id = crypto.randomUUID()
      sessionStorage.setItem(SESSION_KEY, id)
    }
    sessionId.current = id
  }, [])

  // Altijd naar het laatste bericht scrollen.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  if (hidden) return null

  async function send() {
    const text = input.trim()
    if (!text || sending || closed) return

    setInput('')
    setError(null)
    setMessages((m) => [...m, { role: 'user', text }])
    setSending(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId: sessionId.current, message: text }),
      })

      if (res.status === 503) {
        // Niet geconfigureerd op deze omgeving → widget volledig verbergen.
        setHidden(true)
        return
      }
      if (!res.ok) {
        setError('De assistent is even niet bereikbaar. Probeer het zo nog eens.')
        return
      }

      const data = (await res.json()) as { reply?: string; closed?: boolean }
      if (data.reply) {
        setMessages((m) => [...m, { role: 'assistant', text: data.reply as string }])
      }
      if (data.closed) setClosed(true)
    } catch {
      setError('Er ging iets mis met de verbinding. Probeer het zo nog eens.')
    } finally {
      setSending(false)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send()
    }
  }

  return (
    <>
      {/* Launcher */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open de chat met de AI-receptionist"
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 transition-transform hover:scale-110"
        >
          <MessageCircle className="h-7 w-7" />
        </button>
      )}

      {/* Chat-paneel */}
      {open && (
        <div
          role="dialog"
          aria-label="Chat met de AI-receptionist"
          className="fixed bottom-6 right-6 z-50 flex h-[min(34rem,calc(100vh-3rem))] w-[min(24rem,calc(100vw-3rem))] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-3 bg-indigo-600 px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
                <Bot className="h-5 w-5" />
              </div>
              <div className="leading-tight">
                <p className="text-sm font-semibold">Repto-assistent</p>
                <p className="text-xs text-indigo-100">Meestal binnen enkele seconden</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Sluit de chat"
              className="rounded-full p-1 text-indigo-100 transition-colors hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Berichten */}
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-gray-50 px-4 py-4">
            {messages.map((m, i) => (
              <div key={i} className={clsx('flex gap-2.5', m.role === 'user' ? 'flex-row-reverse' : 'flex-row')}>
                <div className={clsx(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                  m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600',
                )}>
                  {m.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div className={clsx(
                  'max-w-[75%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                  m.role === 'user'
                    ? 'rounded-tr-sm bg-indigo-600 text-white'
                    : 'rounded-tl-sm border border-gray-200 bg-white text-gray-900 shadow-sm',
                )}>
                  {m.text}
                </div>
              </div>
            ))}

            {sending && (
              <div className="flex gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-600">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-400 shadow-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Aan het typen…</span>
                </div>
              </div>
            )}

            {error && <p className="text-center text-xs text-red-500">{error}</p>}
            {closed && (
              <p className="text-center text-xs text-gray-400">
                Dit gesprek is afgerond. We nemen snel contact met je op.
              </p>
            )}
          </div>

          {/* Invoer */}
          <div className="border-t border-gray-100 bg-white p-3">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={sending || closed}
                rows={1}
                placeholder={closed ? 'Gesprek afgerond' : 'Typ je bericht…'}
                aria-label="Je bericht"
                className="max-h-28 flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-indigo-400 disabled:bg-gray-50"
              />
              <button
                type="button"
                onClick={() => void send()}
                disabled={sending || closed || !input.trim()}
                aria-label="Verstuur bericht"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-300"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-1.5 text-center text-[10px] text-gray-400">AI-receptionist · powered by Repto</p>
          </div>
        </div>
      )}
    </>
  )
}
