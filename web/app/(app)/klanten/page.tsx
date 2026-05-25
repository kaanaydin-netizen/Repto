import Link from 'next/link'
import { Plus, Building2, Wifi, WifiOff } from 'lucide-react'
import { api } from '@/lib/api'
import type { Organization } from '@/lib/types'

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

const CRM_LABELS: Record<string, string> = {
  airtable:      'Airtable',
  google_sheets: 'Google Sheets',
  hubspot:       'HubSpot',
  pipedrive:     'Pipedrive',
  none:          'Geen CRM',
}

function OrgCard({ org }: { org: Organization }) {
  const initials = org.name.slice(0, 2).toUpperCase()
  const hasWhatsApp = !!org.whatsapp_phone_number_id
  const hasCrm = org.crm_type !== 'none'

  return (
    <Link
      href={`/klanten/${org.id}`}
      className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      {/* Avatar */}
      <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-sm font-bold text-indigo-700">
        {initials}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-gray-900">{org.name}</p>
        <p className="text-xs text-gray-500">{SECTOR_LABELS[org.sector ?? ''] ?? org.sector ?? '—'}</p>
      </div>

      {/* Status chips */}
      <div className="flex items-center gap-2">
        <span
          title={hasWhatsApp ? 'WhatsApp gekoppeld' : 'Geen WhatsApp'}
          className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
            hasWhatsApp
              ? 'bg-green-50 text-green-700 ring-1 ring-green-200'
              : 'bg-gray-100 text-gray-400'
          }`}
        >
          {hasWhatsApp ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
          WhatsApp
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${
            hasCrm
              ? 'bg-indigo-50 text-indigo-700 ring-indigo-200'
              : 'bg-gray-100 text-gray-400 ring-gray-200'
          }`}
        >
          {CRM_LABELS[org.crm_type] ?? org.crm_type}
        </span>
      </div>
    </Link>
  )
}

export default async function KlantenPage() {
  let orgs: Organization[] = []
  let error = false

  try {
    orgs = await api.organizations.list()
  } catch {
    error = true
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Klanten</h1>
          <p className="mt-1 text-sm text-gray-500">
            {orgs.length} {orgs.length === 1 ? 'klant' : 'klanten'} beheerd via Repto
          </p>
        </div>
        <Link
          href="/klanten/nieuw"
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nieuwe klant
        </Link>
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Kon klanten niet laden. Controleer de API-verbinding.
        </div>
      )}

      {/* List */}
      {!error && orgs.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-20 text-center">
          <Building2 className="mx-auto h-10 w-10 text-gray-300" />
          <p className="mt-4 font-medium text-gray-900">Nog geen klanten</p>
          <p className="mt-1 text-sm text-gray-500">Voeg je eerste klant toe om te starten.</p>
          <Link
            href="/klanten/nieuw"
            className="mt-6 flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Nieuwe klant
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {orgs.map(org => (
            <OrgCard key={org.id} org={org} />
          ))}
        </div>
      )}
    </div>
  )
}
