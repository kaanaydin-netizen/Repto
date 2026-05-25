import { Calendar, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { api, ORG_ID } from '@/lib/api'
import type { Appointment } from '@/lib/types'

export const dynamic = 'force-dynamic'

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('nl-BE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('nl-BE', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function duurMinuten(start: string, end: string) {
  return Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60000)
}

function isVandaag(dateStr: string) {
  const d = new Date(dateStr)
  const nu = new Date()
  return (
    d.getFullYear() === nu.getFullYear() &&
    d.getMonth() === nu.getMonth() &&
    d.getDate() === nu.getDate()
  )
}

function isToekomst(dateStr: string) {
  return new Date(dateStr) > new Date()
}

function AfspraakCard({ appt }: { appt: Appointment }) {
  const isActief = appt.status === 'confirmed'
  const vandaag  = isVandaag(appt.start_at)
  const toekomst = isToekomst(appt.start_at)
  const duur     = duurMinuten(appt.start_at, appt.end_at)

  return (
    <div
      className={`flex items-start gap-4 rounded-xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
        vandaag && isActief
          ? 'border-indigo-300 ring-1 ring-indigo-200'
          : 'border-gray-200'
      } ${!isActief ? 'opacity-60' : ''}`}
    >
      {/* Datum blok */}
      <div
        className={`flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-xl text-sm font-bold ${
          vandaag && isActief
            ? 'bg-indigo-600 text-white'
            : 'bg-indigo-50 text-indigo-700'
        }`}
      >
        <Calendar className="h-5 w-5" />
        {vandaag && isActief && (
          <span className="mt-0.5 text-[9px] font-semibold uppercase tracking-wide opacity-80">
            Vandaag
          </span>
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="font-semibold text-gray-900 leading-tight">{appt.title}</p>
          {isActief ? (
            <span className="flex shrink-0 items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-[10px] font-semibold text-green-700 ring-1 ring-inset ring-green-200">
              <CheckCircle2 className="h-3 w-3" />
              Bevestigd
            </span>
          ) : (
            <span className="flex shrink-0 items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-[10px] font-semibold text-gray-500 ring-1 ring-inset ring-gray-200">
              <XCircle className="h-3 w-3" />
              Geannuleerd
            </span>
          )}
        </div>

        <p className="mt-1 text-sm text-gray-600">{formatDate(appt.start_at)}</p>

        <div className="mt-1.5 flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {formatTime(appt.start_at)} – {formatTime(appt.end_at)}
          </span>
          <span className="text-gray-300">·</span>
          <span>{duur} min</span>
          {!toekomst && isActief && (
            <>
              <span className="text-gray-300">·</span>
              <span className="text-gray-400 italic">Voorbij</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default async function AfsprakenPage() {
  const appts = ORG_ID
    ? await api.appointments.list(ORG_ID).catch(() => [])
    : []

  const aankomend  = appts.filter(a => a.status === 'confirmed' && isToekomst(a.start_at))
  const vandaag    = appts.filter(a => a.status === 'confirmed' && isVandaag(a.start_at))
  const verleden   = appts.filter(a => a.status === 'confirmed' && !isToekomst(a.start_at) && !isVandaag(a.start_at))
  const geannuleerd = appts.filter(a => a.status === 'cancelled')

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Afspraken</h1>
          <p className="mt-1 text-sm text-gray-500">
            Ingeplande afspraken via de AI-receptionist.
          </p>
        </div>
        {appts.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700 ring-1 ring-indigo-200">
              {aankomend.length + vandaag.length} aankomend
            </span>
          </div>
        )}
      </div>

      {appts.length === 0 ? (
        /* ── Empty state ───────────────────────────────────────────────── */
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-20 text-center">
          <span className="text-5xl">📅</span>
          <p className="mt-4 font-medium text-gray-900">Geen afspraken gepland</p>
          <p className="mt-1 text-sm text-gray-500 max-w-xs">
            Zodra de AI een afspraak inplant via WhatsApp, verschijnt die hier.
          </p>
        </div>
      ) : (
        <div className="space-y-8">

          {/* Vandaag */}
          {vandaag.length > 0 && (
            <section>
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-indigo-700">
                <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-500" />
                Vandaag
              </h2>
              <div className="space-y-3">
                {vandaag.map(a => <AfspraakCard key={a.id} appt={a} />)}
              </div>
            </section>
          )}

          {/* Aankomend */}
          {aankomend.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-gray-700">Aankomend</h2>
              <div className="space-y-3">
                {aankomend.map(a => <AfspraakCard key={a.id} appt={a} />)}
              </div>
            </section>
          )}

          {/* Verleden */}
          {verleden.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-gray-500">Afgelopen</h2>
              <div className="space-y-3">
                {verleden.slice(0, 5).map(a => <AfspraakCard key={a.id} appt={a} />)}
              </div>
            </section>
          )}

          {/* Geannuleerd */}
          {geannuleerd.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-gray-400">Geannuleerd</h2>
              <div className="space-y-3">
                {geannuleerd.map(a => <AfspraakCard key={a.id} appt={a} />)}
              </div>
            </section>
          )}

        </div>
      )}
    </div>
  )
}
