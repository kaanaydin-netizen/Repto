import { MessageSquare, UserPlus, Calendar, Clock } from 'lucide-react'
import StatCard from '@/components/StatCard'
import ConversationCard from '@/components/ConversationCard'
import { MOCK_CONVERSATIONS } from '@/lib/api'

export default function DashboardPage() {
  const nieuweLeads = MOCK_CONVERSATIONS.filter(c => c.status === 'new').length
  const afspraken   = MOCK_CONVERSATIONS.filter(c => c.status === 'appointment_set').length
  const recent      = MOCK_CONVERSATIONS.slice(0, 3)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Goedemorgen! Hier is een overzicht van vandaag.</p>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Totaal gesprekken"
          value={MOCK_CONVERSATIONS.length}
          sub="deze week"
          icon={MessageSquare}
          color="indigo"
        />
        <StatCard
          title="Nieuwe leads"
          value={nieuweLeads}
          sub="wachten op opvolging"
          icon={UserPlus}
          color="amber"
        />
        <StatCard
          title="Afspraken vandaag"
          value={afspraken}
          sub="ingepland"
          icon={Calendar}
          color="green"
        />
        <StatCard
          title="Gem. reactietijd"
          value="< 1 min"
          sub="AI antwoordt direct"
          icon={Clock}
          color="blue"
        />
      </div>

      {/* Recente gesprekken */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Recente gesprekken</h2>
          <a href="/gesprekken" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
            Alles bekijken →
          </a>
        </div>
        <div className="space-y-3">
          {recent.map(conv => (
            <ConversationCard key={conv.id} conv={conv} />
          ))}
        </div>
      </div>

      {/* Onboarding banner — toon zolang WhatsApp niet gekoppeld is */}
      <div className="mt-8 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-2xl">
            📱
          </div>
          <div>
            <p className="font-semibold text-indigo-900">WhatsApp nog niet gekoppeld</p>
            <p className="mt-0.5 text-sm text-indigo-700">
              Koppel je WhatsApp Business nummer om automatisch berichten te beantwoorden.
            </p>
            <a
              href="/instellingen"
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Instellen →
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
