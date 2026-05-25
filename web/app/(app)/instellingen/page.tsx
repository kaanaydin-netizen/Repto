export default function InstellingenPage() {
  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Instellingen</h1>
        <p className="mt-1 text-sm text-gray-500">Configureer je bedrijf, AI-assistent en koppelingen.</p>
      </div>

      {/* Bedrijfsprofiel */}
      <section className="mb-8">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Bedrijfsprofiel</h2>
        <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div>
            <label className="block text-sm font-medium text-gray-700">Bedrijfsnaam</label>
            <input type="text" defaultValue="Mijn bedrijf" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Sector</label>
            <select className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100">
              <option>Installateur</option>
              <option>Vastgoed</option>
              <option>Garage</option>
              <option>Boekhouder</option>
              <option>Bouwbedrijf</option>
              <option>Freelancer</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Toon van de AI</label>
            <select className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100">
              <option>Informeel (tutoyeren)</option>
              <option>Formeel (vousvoyeren)</option>
            </select>
          </div>
          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Opslaan
          </button>
        </div>
      </section>

      {/* WhatsApp koppeling */}
      <section className="mb-8">
        <h2 className="mb-4 text-base font-semibold text-gray-900">WhatsApp koppeling</h2>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <div className="flex items-start gap-3">
            <span className="text-2xl">📱</span>
            <div className="flex-1">
              <p className="font-medium text-amber-900">Nog niet gekoppeld</p>
              <p className="mt-1 text-sm text-amber-700">
                Je hebt een goedgekeurd Meta Business account nodig om WhatsApp te koppelen.
              </p>
              <div className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium text-amber-800">Phone Number ID</label>
                  <input type="text" placeholder="1234567890" className="mt-1 w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-amber-800">Access Token</label>
                  <input type="password" placeholder="EAAxxxxxxx" className="mt-1 w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" />
                </div>
                <button className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700">
                  Koppelen
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CRM koppeling */}
      <section className="mb-8">
        <h2 className="mb-4 text-base font-semibold text-gray-900">CRM koppeling</h2>
        <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">Kies waar nieuwe leads naartoe gestuurd worden.</p>
          <div className="space-y-2">
            {[
              { id: 'sheets', label: 'Google Sheets', badge: 'MVP', icon: '📊' },
              { id: 'hubspot', label: 'HubSpot', badge: 'Fase 2', icon: '🟠' },
              { id: 'pipedrive', label: 'Pipedrive', badge: 'Fase 2', icon: '🟢' },
            ].map(crm => (
              <label key={crm.id} className="flex cursor-pointer items-center gap-3 rounded-lg border border-gray-200 p-3 hover:bg-gray-50">
                <input type="radio" name="crm" value={crm.id} defaultChecked={crm.id === 'sheets'} className="accent-indigo-600" />
                <span className="text-lg">{crm.icon}</span>
                <span className="flex-1 text-sm font-medium text-gray-900">{crm.label}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${crm.badge === 'MVP' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {crm.badge}
                </span>
              </label>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Google Sheet ID</label>
            <input type="text" placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms" className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-mono focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100" />
            <p className="mt-1 text-xs text-gray-400">Vind dit in de URL van je Google Sheet</p>
          </div>
          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Opslaan
          </button>
        </div>
      </section>

      {/* AI prompt */}
      <section>
        <h2 className="mb-4 text-base font-semibold text-gray-900">AI-instructies</h2>
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-medium text-gray-700">Aangepaste instructies voor de AI</label>
          <textarea
            rows={5}
            defaultValue={"Wij zijn een loodgietersbedrijf actief in Gent en omgeving.\nOpeningsuren: ma-vr 8u-17u.\nSpoedlijn: 09 123 45 67.\nDienstencatalogus: sanitair, centrale verwarming, warmtepompen, zonneboilers."}
            className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-xs text-gray-400">De AI gebruikt dit als context bij elk gesprek.</p>
          <button className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Opslaan
          </button>
        </div>
      </section>
    </div>
  )
}
