import { MessageSquare, UserPlus, CheckCircle2, RefreshCw } from 'lucide-react'
import StatCard from '@/components/StatCard'
import ConversationCard from '@/components/ConversationCard'
import { api } from '@/lib/api'
import { getOrgId } from '@/lib/org'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const ORG_ID = await getOrgId()

  const [stats, conversations, org] = await Promise.all([
    api.stats(ORG_ID).catch(() => ({
      total_conversations: 0,
      new_leads: 0,
      closed_today: 0,
      crm_synced: 0,
    })),
    api.conversations.list(ORG_ID).catch(() => []),
    ORG_ID ? api.organizations.get(ORG_ID).catch(() => null) : Promise.resolve(null),
  ])

  const recent = conversations.slice(0, 5)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            {org ? (
              <>Live overzicht voor <span className="font-medium text-gray-700">{org.name}</span>.</>
            ) : (
              'Live overzicht van je gesprekken en leads.'
            )}
          </p>
        </div>
        <a
          href="/dashboard"
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4" />
          Vernieuwen
        </a>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Totaal gesprekken"
          value={stats.total_conversations}
          sub="alle tijd"
          icon={MessageSquare}
          color="indigo"
        />
        <StatCard
          title="Nieuwe leads"
          value={stats.new_leads}
          sub="wachten op opvolging"
          icon={UserPlus}
          color="amber"
        />
        <StatCard
          title="Gesloten vandaag"
          value={stats.closed_today}
          sub="gesprekken afgerond"
          icon={CheckCircle2}
          color="green"
        />
        <StatCard
          title="CRM gesynchroniseerd"
          value={stats.crm_synced}
          sub="leads in Airtable"
          icon={RefreshCw}
          color="blue"
        />
      </div>

      {/* Recente gesprekken */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            Recente gesprekken
          </h2>
          <a
            href="/gesprekken"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            Alles bekijken →
          </a>
        </div>

        {recent.length > 0 ? (
          <div className="space-y-3">
            {recent.map(conv => (
              <ConversationCard key={conv.id} conv={conv} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 text-center">
            <span className="text-4xl">💬</span>
            <p className="mt-3 font-medium text-gray-900">Nog geen gesprekken</p>
            <p className="mt-1 text-sm text-gray-500">
              Zodra klanten je WhatsApp sturen, verschijnen ze hier.
            </p>
          </div>
        )}
      </div>

      {/* Onboarding banner */}
      {!ORG_ID && (
        <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-100 text-2xl">
              ⚠️
            </div>
            <div>
              <p className="font-semibold text-amber-900">ORG_ID niet ingesteld</p>
              <p className="mt-0.5 text-sm text-amber-700">
                Stel <code className="rounded bg-amber-100 px-1 font-mono text-xs">NEXT_PUBLIC_ORG_ID</code> in
                als omgevingsvariabele om je organisatie te koppelen.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
