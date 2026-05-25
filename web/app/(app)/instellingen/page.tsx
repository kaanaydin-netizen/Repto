import { api } from '@/lib/api'
import { getOrgId } from '@/lib/org'
import InstellingenClient from './InstellingenClient'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

export default async function InstellingenPage() {
  const ORG_ID = await getOrgId()

  if (!ORG_ID) {
    return (
      <div className="p-8 max-w-2xl">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <p className="font-semibold text-amber-900">Nog geen klant geconfigureerd</p>
          <p className="mt-1 text-sm text-amber-700">
            Voeg eerst een klant toe via de{' '}
            <Link href="/klanten/nieuw" className="font-medium underline">
              onboarding wizard
            </Link>
            .
          </p>
        </div>
      </div>
    )
  }

  const org = await api.organizations.get(ORG_ID).catch(() => null)

  if (!org) {
    return (
      <div className="p-8 max-w-2xl">
        <div className="rounded-xl border border-red-200 bg-red-50 p-5">
          <p className="font-semibold text-red-900">Organisatie niet gevonden</p>
          <p className="mt-1 text-sm text-red-700">
            Ga naar{' '}
            <Link href="/klanten" className="font-medium underline">
              Klanten
            </Link>{' '}
            om een actieve organisatie te selecteren.
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
