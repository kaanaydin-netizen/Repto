import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Building2, Bot, Phone, Database, Pencil,
         MessageSquare, Activity, CheckCircle2, CalendarCheck } from 'lucide-react'
import { api } from '@/lib/api'

export const dynamic = 'force-dynamic'

const SECTOR_LABELS: Record<string, string> = {
  algemeen:      'Algemeen',
  installateur:  'Installateur',
  makelaar:      'Makelaar',
  bouwbedrijf:   'Bouwbedrijf',
  garage:        'Garage',
  boekhouder:    'Boekhouder',
  freelancer:    'Freelancer',
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between gap-4 border-b border-gray-100 py-3 text-sm last:border-0">
      <span className="font-medium text-gray-500">{label}</span>
      <span className="break-all text-right text-gray-900">
        {value || <span className="text-gray-300">—</span>}
      </span>
    </div>
  )
}

function Section({ icon: Icon, title, children }: {
  icon: React.ElementType
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-indigo-600" />
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
      </div>
      {children}
    </div>
  )
}

export default async function KlantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  // Laad org + stats parallel
  const [org, stats] = await Promise.all([
    api.organizations.get(id).catch(() => null),
    api.conversations.stats(id).catch(() => ({
      total_conversations: 0,
      active_conversations: 0,
      closed_conversations: 0,
      confirmed_appointments: 0,
      new_leads_today: 0,
    })),
  ])

  if (!org) notFound()

  const webhookUrl = `${process.env.NEXT_PUBLIC_API_URL || 'https://repto-production.up.railway.app'}/webhooks/whatsapp`

  return (
    <div className="p-8 max-w-2xl">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="mb-6 flex items-center gap-3">
        <Link
          href="/klanten"
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-sm font-bold text-indigo-700">
          {org.name.slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="truncate text-xl font-bold text-gray-900">{org.name}</h1>
          <p className="text-xs text-gray-500">
            {SECTOR_LABELS[org.sector ?? ''] ?? org.sector ?? 'Onbekende sector'}
          </p>
        </div>
        <Link
          href={`/klanten/${org.id}/bewerken`}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <Pencil className="h-3.5 w-3.5" />
          Bewerken
        </Link>
      </div>

      {/* ── Stats strip ───────────────────────────────────────────────── */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          {
            icon: MessageSquare,
            label: 'Gesprekken',
            value: stats.total_conversations,
            color: 'text-indigo-600',
            bg: 'bg-indigo-50',
          },
          {
            icon: Activity,
            label: 'Actief',
            value: stats.active_conversations,
            color: 'text-amber-600',
            bg: 'bg-amber-50',
          },
          {
            icon: CheckCircle2,
            label: 'Gesloten',
            value: stats.closed_conversations,
            color: 'text-green-600',
            bg: 'bg-green-50',
          },
          {
            icon: CalendarCheck,
            label: 'Afspraken',
            value: stats.confirmed_appointments,
            color: 'text-blue-600',
            bg: 'bg-blue-50',
          },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border border-gray-200 bg-white p-4 shadow-sm`}>
            <div className={`mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg ${s.bg}`}>
              <s.icon className={`h-4 w-4 ${s.color}`} />
            </div>
            <p className={`text-2xl font-extrabold ${s.color}`}>{s.value}</p>
            <p className="mt-0.5 text-[10px] font-medium text-gray-400 leading-tight">{s.label}</p>
          </div>
        ))}
      </div>

      {/* ── Detail secties ────────────────────────────────────────────── */}
      <div className="space-y-4">

        {/* Bedrijf */}
        <Section icon={Building2} title="Bedrijfsprofiel">
          <InfoRow label="Naam"   value={org.name} />
          <InfoRow label="Sector" value={SECTOR_LABELS[org.sector ?? ''] ?? org.sector} />
          <InfoRow label="Org ID" value={org.id} />
        </Section>

        {/* AI */}
        <Section icon={Bot} title="AI-assistent">
          <InfoRow
            label="Communicatiestijl"
            value={org.ai_tone === 'formeel' ? 'Formeel (u)' : 'Informeel (je/jij)'}
          />
          <InfoRow label="Extra instructies" value={org.ai_system_prompt} />
        </Section>

        {/* WhatsApp */}
        <Section icon={Phone} title="WhatsApp">
          <InfoRow label="Nummer"         value={org.whatsapp_number} />
          <InfoRow label="Phone Number ID" value={org.whatsapp_phone_number_id} />
          <div className="mt-3 rounded-lg bg-indigo-50 p-3">
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-500">
              Webhook URL
            </p>
            <code className="break-all text-xs text-indigo-800">{webhookUrl}</code>
          </div>
        </Section>

        {/* CRM */}
        <Section icon={Database} title="CRM koppeling">
          <InfoRow
            label="Type"
            value={org.crm_type === 'none' ? 'Geen CRM' : org.crm_type}
          />
          {org.crm_type === 'airtable' && (
            <div className="mt-2 flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-xs text-green-700">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500" />
              Airtable actief · credentials versleuteld opgeslagen
            </div>
          )}
        </Section>

        {/* Gesprekken link */}
        <Link
          href={`/gesprekken`}
          className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
        >
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-indigo-600" />
            <span className="text-sm font-medium text-gray-900">Alle gesprekken bekijken</span>
          </div>
          <span className="text-sm text-indigo-600">→</span>
        </Link>
      </div>
    </div>
  )
}
