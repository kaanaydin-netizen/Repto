import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { api } from '@/lib/api'
import BewerkClient from './BewerkClient'

export const dynamic = 'force-dynamic'

export default async function BewerkPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const org = await api.organizations.get(id).catch(() => null)
  if (!org) notFound()

  return (
    <div className="p-8 max-w-2xl">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <Link
          href={`/klanten/${org.id}`}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-900">{org.name} bewerken</h1>
          <p className="text-xs text-gray-500">Wijzigingen worden meteen actief voor de AI.</p>
        </div>
      </div>

      <BewerkClient org={org} />
    </div>
  )
}
