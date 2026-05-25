'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Check, Save, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { Organization } from '@/lib/types'

// ─── Hulpcomponenten ───────────────────────────────────────────────────────────

function Label({ children, optional }: { children: React.ReactNode; optional?: boolean }) {
  return (
    <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
      {children}
      {optional && (
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-400">
          Optioneel
        </span>
      )}
    </label>
  )
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 disabled:bg-gray-50"
    />
  )
}

function Select(props: React.SelectHTMLAttributes<HTMLSelectElement> & { children: React.ReactNode }) {
  const { children, ...rest } = props
  return (
    <select
      {...rest}
      className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
    >
      {children}
    </select>
  )
}

function Section({ title, description, children }: {
  title: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-5 border-b border-gray-100 pb-4">
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-gray-500">{description}</p>}
      </div>
      <div className="space-y-5">{children}</div>
    </div>
  )
}

// ─── Hoofd component ───────────────────────────────────────────────────────────

interface Props {
  org: Organization
}

const SECTORS = [
  { value: 'algemeen',     label: 'Algemeen' },
  { value: 'installateur', label: 'Installateur' },
  { value: 'makelaar',     label: 'Makelaar' },
  { value: 'bouwbedrijf',  label: 'Bouwbedrijf' },
  { value: 'garage',       label: 'Garage' },
  { value: 'boekhouder',   label: 'Boekhouder' },
  { value: 'freelancer',   label: 'Freelancer' },
]

export default function BewerkClient({ org }: Props) {
  const router = useRouter()

  const [name, setName] = useState(org.name)
  const [sector, setSector] = useState(org.sector ?? 'algemeen')
  const [aiTone, setAiTone] = useState(org.ai_tone ?? 'formeel')
  const [aiPrompt, setAiPrompt] = useState(org.ai_system_prompt ?? '')
  const [waNumber, setWaNumber] = useState(org.whatsapp_number ?? '')
  const [waPhoneId, setWaPhoneId] = useState(org.whatsapp_phone_number_id ?? '')
  const [crmType, setCrmType] = useState(org.crm_type ?? 'none')
  const [atApiKey, setAtApiKey] = useState('')        // nooit pre-ingevuld (versleuteld)
  const [atBaseId, setAtBaseId] = useState('')
  const [atTable, setAtTable] = useState('Leads')

  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    if (!name.trim()) { setError('Bedrijfsnaam is verplicht.'); return }
    setSaving(true)
    setError('')

    const payload: Record<string, unknown> = {
      name: name.trim(),
      sector,
      ai_tone: aiTone,
      ai_system_prompt: aiPrompt.trim() || null,
      whatsapp_number: waNumber.trim() || null,
      whatsapp_phone_number_id: waPhoneId.trim() || null,
      crm_type: crmType,
    }

    // Enkel Airtable meesturen als de gebruiker nieuwe credentials invult
    if (crmType === 'airtable' && atApiKey.trim()) {
      payload.airtable = {
        api_key: atApiKey.trim(),
        base_id: atBaseId.trim(),
        table_name: atTable.trim() || 'Leads',
      }
    }

    try {
      await api.organizations.update(org.id, payload)
      setSaved(true)
      setTimeout(() => {
        router.push(`/klanten/${org.id}`)
      }, 800)
    } catch {
      setError('Opslaan mislukt. Probeer opnieuw.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5">

      {/* ── Bedrijfsprofiel ─────────────────────────────────────────────── */}
      <Section title="Bedrijfsprofiel">
        <div>
          <Label>Bedrijfsnaam</Label>
          <Input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="bv. Loodgieters De Smedt"
          />
        </div>
        <div>
          <Label>Sector</Label>
          <Select value={sector} onChange={e => setSector(e.target.value)}>
            {SECTORS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </Select>
        </div>
      </Section>

      {/* ── AI-assistent ────────────────────────────────────────────────── */}
      <Section
        title="AI-assistent"
        description="Hoe communiceert de AI met klanten van deze organisatie?"
      >
        <div>
          <Label>Communicatiestijl</Label>
          <Select value={aiTone} onChange={e => setAiTone(e.target.value)}>
            <option value="formeel">Formeel (vousvoyeren — u)</option>
            <option value="informeel">Informeel (tutoyeren — je/jij)</option>
          </Select>
        </div>
        <div>
          <Label optional>Extra instructies</Label>
          <textarea
            rows={6}
            value={aiPrompt}
            onChange={e => setAiPrompt(e.target.value)}
            placeholder={`bv.\nWij zijn actief in Gent en omgeving.\nOpeningsuren: ma–vr 8u–17u.\nSpoedlijn: 09 123 45 67.`}
            className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-xs text-gray-400">De AI voegt dit toe aan elke gesprekssessie.</p>
        </div>
      </Section>

      {/* ── WhatsApp ────────────────────────────────────────────────────── */}
      <Section
        title="WhatsApp koppeling"
        description="Pas het gekoppelde WhatsApp-nummer aan."
      >
        <div>
          <Label optional>WhatsApp-nummer</Label>
          <Input
            value={waNumber}
            onChange={e => setWaNumber(e.target.value)}
            placeholder="+32468123456"
          />
        </div>
        <div>
          <Label optional>Phone Number ID (Meta)</Label>
          <Input
            value={waPhoneId}
            onChange={e => setWaPhoneId(e.target.value)}
            placeholder="123456789012345"
          />
          <p className="mt-1 text-xs text-gray-400">
            Te vinden in Meta Business → WhatsApp → Telefoonbeheer
          </p>
        </div>
      </Section>

      {/* ── CRM ─────────────────────────────────────────────────────────── */}
      <Section
        title="CRM koppeling"
        description="Kies waar nieuwe leads naartoe gestuurd worden."
      >
        <div>
          <Label>CRM type</Label>
          <Select value={crmType} onChange={e => setCrmType(e.target.value)}>
            <option value="none">Geen CRM</option>
            <option value="airtable">Airtable</option>
            <option value="hubspot">HubSpot (binnenkort)</option>
            <option value="pipedrive">Pipedrive (binnenkort)</option>
          </Select>
        </div>

        {crmType === 'airtable' && (
          <div className="space-y-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-xs text-indigo-600">
              Vul nieuwe credentials in om de Airtable-koppeling te updaten.
              Leeg laten = huidige credentials behouden.
            </p>
            <div>
              <Label optional>Personal Access Token</Label>
              <Input
                type="password"
                value={atApiKey}
                onChange={e => setAtApiKey(e.target.value)}
                placeholder="pat7hqea… (laat leeg om niet te wijzigen)"
              />
            </div>
            <div>
              <Label optional>Base ID</Label>
              <Input
                value={atBaseId}
                onChange={e => setAtBaseId(e.target.value)}
                placeholder="appXXXXXXXXXXXXXX"
              />
            </div>
            <div>
              <Label optional>Tabelnaam</Label>
              <Input
                value={atTable}
                onChange={e => setAtTable(e.target.value)}
                placeholder="Leads"
              />
            </div>
          </div>
        )}
      </Section>

      {/* ── Foutmelding ─────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {/* ── Acties ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={() => router.push(`/klanten/${org.id}`)}
          className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Annuleren
        </button>
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={`flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition-colors disabled:opacity-70 ${
            saved ? 'bg-green-600' : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {saved ? (
            <><Check className="h-4 w-4" /> Opgeslagen</>
          ) : saving ? (
            'Opslaan…'
          ) : (
            <><Save className="h-4 w-4" /> Wijzigingen opslaan</>
          )}
        </button>
      </div>
    </div>
  )
}
