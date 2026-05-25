import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Building2, Bot, Phone, Database, Pencil } from 'lucide-react'
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
    <div className="flex justify-between gap-4 py-3 text-sm border-b border-gray-100 last:border-0">
      <span className="font-medium text-gray-500">{label}</span>
      <span className="text-right text-gray-900 break-all">{value || <span className="text-gray-300">—</span>}</span>
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

export default async function KlantDetailPage({ params }: { params: { id: string } }) {
  const org = await api.organizations.get(params.id).catch(() => null)
  if (!org) notFound()

  const webhookUrl = `${process.env.NEXT_PUBLIC_API_URL || 'https://repto-production.up.railway.app'}/webhooks/whatsapp/${org.id}`

  return (
    <div className="p-8 max-w-2xl">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <Link
          href="/klanten"
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-sm font-bold text-indigo-700">
          {org.name.slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">{org.name}</h1>
          <p className="text-xs text-gray-500">{SECTOR_LABELS[org.sector ?? ''] ?? org.sector ?? 'Onbekende sector'}</p>
        </div>
        <Link
          href={`/klanten/${org.id}/bewerken`}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50"
        >
          <Pencil className="h-3.5 w-3.5" />
          Bewerken
        </Link>
      </div>

      <div className="space-y-4">
        {/* Bedrijf */}
        <Section icon={Building2} title="Bedrijfsprofiel">
          <InfoRow label="Naam" value={org.name} />
          <InfoRow label="Sector" value={SECTOR_LABELS[org.sector ?? ''] ?? org.sector} />
          <InfoRow label="Org ID" value={org.id} />
        </Section>

        {/* AI */}
        <Section icon={Bot} title="AI-assistent">
          <InfoRow label="Communicatiestijl" value={org.ai_tone === 'formeel' ? 'Formeel (u)' : 'Informeel (je/jij)'} />
          <InfoRow label="Extra instructies" value={org.ai_system_prompt} />
        </Section>

        {/* WhatsApp */}
        <Section icon={Phone} title="WhatsApp">
          <InfoRow label="Nummer" value={org.whatsapp_number} />
          <InfoRow label="Phone Number ID" value={org.whatsapp_phone_number_id} />
          <div className="mt-3 rounded-lg bg-indigo-50 p-3">
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-500">Webhook URL</p>
            <code className="break-all text-xs text-indigo-800">{webhookUrl}</code>
          </div>
        </Section>

        {/* CRM */}
        <Section icon={Database} title="CRM koppeling">
          <InfoRow label="Type" value={org.crm_type === 'none' ? 'Geen CRM' : org.crm_type} />
          {org.crm_type !== 'none' && (
            <p className="mt-2 text-xs text-gray-400">
              Airtable-credentials zijn versleuteld opgeslagen en worden niet getoond.
            </p>
          )}
        </Section>

        {/* Gesprekken link */}
        <Link
          href={`/gesprekken?org_id=${org.id}`}
          className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <span className="text-sm font-medium text-gray-900">Gesprekken bekijken →</span>
        </Link>
      </div>
    </div>
  )
}
