import { Calendar, Clock } from 'lucide-react'

const MOCK_AFSPRAKEN = [
  { id: '1', title: 'Ketelonderhoud', name: 'Thomas De Smedt', phone: '+32 496 55 66 77', start: new Date(Date.now() + 1000 * 60 * 60 * 26), duur: 60 },
  { id: '2', title: 'Warmtepomp offerte', name: 'Sofie Vermeersch', phone: '+31 6 12 34 56 78', start: new Date(Date.now() + 1000 * 60 * 60 * 50), duur: 90 },
]

export default function AfsprakenPage() {
  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Afspraken</h1>
        <p className="mt-1 text-sm text-gray-500">Ingeplande afspraken via Repto.</p>
      </div>

      {MOCK_AFSPRAKEN.length > 0 ? (
        <div className="space-y-3">
          {MOCK_AFSPRAKEN.map(a => (
            <div key={a.id} className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-indigo-50 text-indigo-700">
                <Calendar className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900">{a.title}</p>
                <p className="text-sm text-gray-500">{a.name} · {a.phone}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-medium text-gray-900">
                  {a.start.toLocaleDateString('nl-BE', { weekday: 'short', day: 'numeric', month: 'short' })}
                </p>
                <p className="flex items-center gap-1 justify-end text-xs text-gray-500">
                  <Clock className="h-3 w-3" />
                  {a.start.toLocaleTimeString('nl-BE', { hour: '2-digit', minute: '2-digit' })} · {a.duur} min
                </p>
              </div>
              <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 ring-1 ring-inset ring-green-200">
                Bevestigd
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 text-center">
          <span className="text-4xl">📅</span>
          <p className="mt-3 font-medium text-gray-900">Geen afspraken gepland</p>
          <p className="mt-1 text-sm text-gray-500">Afspraken verschijnen hier zodra klanten inplannen via WhatsApp.</p>
        </div>
      )}
    </div>
  )
}
