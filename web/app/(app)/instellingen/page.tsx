import { api, ORG_ID } from '@/lib/api'
import InstellingenClient from './InstellingenClient'

export const dynamic = 'force-dynamic'

export default async function InstellingenPage() {
  // Geen ORG_ID ingesteld
  if (!ORG_ID) {
    return (
      <div className="p-8 max-w-2xl">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <p className="font-semibold text-amber-900">ORG_ID niet ingesteld</p>
          <p className="mt-1 text-sm text-amber-700">
            Stel{' '}
            <code className="rounded bg-amber-100 px-1 font-mono text-xs">
              NEXT_PUBLIC_ORG_ID
            </code>{' '}
            in als omgevingsvariabele.
          </p>
        </div>
      </div>
    )
  }

  // Organisatie ophalen
  const org = await api.organizations.get(ORG_ID).catch(() => null)

  if (!org) {
    return (
      <div className="p-8 max-w-2xl">
        <div className="rounded-xl border border-red-200 bg-red-50 p-5">
          <p className="font-semibold text-red-900">Organisatie niet gevonden</p>
          <p className="mt-1 text-sm text-red-700">
            Controleer of <code className="rounded bg-red-100 px-1 font-mono text-xs">NEXT_PUBLIC_ORG_ID</code> correct is ingesteld.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Instellingen</h1>
        <p className="mt-1 text-sm text-gray-500">
          Configureer je AI-receptionist, WhatsApp koppeling en CRM.
        </p>
      </div>

      <InstellingenClient org={org} />
    </div>
  )
}
