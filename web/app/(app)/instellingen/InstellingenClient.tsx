'use client'
import { useState } from 'react'
import { Check, Save, Copy, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import type { Organization } from '@/lib/types'

// ─── Constanten ───────────────────────────────────────────────────────────────

const SECTORS = [
  { value: 'algemeen',     label: 'Algemeen' },
  { value: 'installateur', label: 'Installateur' },
  { value: 'makelaar',     label: 'Makelaar / Vastgoed' },
  { value: 'bouwbedrijf',  label: 'Bouwbedrijf' },
  { value: 'garage',       label: 'Garage / Auto' },
  { value: 'boekhouder',   label: 'Boekhouder' },
  { value: 'freelancer',   label: 'Freelancer' },
]

// ─── Gedeelde UI ──────────────────────────────────────────────────────────────

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

function SelectField(
  props: React.SelectHTMLAttributes<HTMLSelectElement> & { children: React.ReactNode }
) {
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

interface SectionProps {
  title: string
  description?: string
  children: React.ReactNode
  onSave: () => void
  saving: boolean
  saved: boolean
  error: string
}

function Section({ title, description, children, onSave, saving, saved, error }: SectionProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-5 border-b border-gray-100 pb-4">
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
        {description && <p className="mt-0.5 text-xs text-gray-500">{description}</p>}
      </div>

      <div className="space-y-5">{children}</div>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button
          onClick={onSave}
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
            <><Save className="h-4 w-4" /> Opslaan</>
          )}
        </button>
      </div>
    </div>
  )
}

// ─── Hoofd component ──────────────────────────────────────────────────────────

export default function InstellingenClient({ org }: { org: Organization }) {
  // Bedrijfsprofiel
  const [name, setName]     = useState(org.name)
  const [sector, setSector] = useState(org.sector ?? 'algemeen')
  const [pSaving, setPSaving] = useState(false)
  const [pSaved,  setPSaved]  = useState(false)
  const [pError,  setPError]  = useState('')

  // AI-assistent
  const [aiTone,   setAiTone]   = useState(org.ai_tone ?? 'formeel')
  const [aiPrompt, setAiPrompt] = useState(org.ai_system_prompt ?? '')
  const [aiSaving, setAiSaving] = useState(false)
  const [aiSaved,  setAiSaved]  = useState(false)
  const [aiError,  setAiError]  = useState('')

  // WhatsApp
  const [waNumber,  setWaNumber]  = useState(org.whatsapp_number ?? '')
  const [waPhoneId, setWaPhoneId] = useState(org.whatsapp_phone_number_id ?? '')
  const [waSaving, setWaSaving]   = useState(false)
  const [waSaved,  setWaSaved]    = useState(false)
  const [waError,  setWaError]    = useState('')
  const [copied,   setCopied]     = useState(false)

  // CRM
  const [crmType,  setCrmType]  = useState(org.crm_type ?? 'none')
  const [atApiKey, setAtApiKey] = useState('')
  const [atBaseId, setAtBaseId] = useState('')
  const [atTable,  setAtTable]  = useState('Leads')
  const [crmSaving, setCrmSaving] = useState(false)
  const [crmSaved,  setCrmSaved]  = useState(false)
  const [crmError,  setCrmError]  = useState('')

  const webhookUrl = `${process.env.NEXT_PUBLIC_API_URL ?? 'https://repto-production.up.railway.app'}/webhooks/whatsapp`

  // ─── Save handlers ──────────────────────────────────────────────────────────

  async function saveProfile() {
    if (!name.trim()) { setPError('Bedrijfsnaam is verplicht.'); return }
    setPSaving(true); setPError('')
    try {
      await api.organizations.update(org.id, { name: name.trim(), sector })
      setPSaved(true); setTimeout(() => setPSaved(false), 3000)
    } catch { setPError('Opslaan mislukt. Probeer opnieuw.') }
    finally  { setPSaving(false) }
  }

  async function saveAi() {
    setAiSaving(true); setAiError('')
    try {
      await api.organizations.update(org.id, {
        ai_tone: aiTone,
        ai_system_prompt: aiPrompt.trim() || undefined,
      })
      setAiSaved(true); setTimeout(() => setAiSaved(false), 3000)
    } catch { setAiError('Opslaan mislukt. Probeer opnieuw.') }
    finally  { setAiSaving(false) }
  }

  async function saveWhatsApp() {
    setWaSaving(true); setWaError('')
    try {
      await api.organizations.update(org.id, {
        whatsapp_number: waNumber.trim() || undefined,
        whatsapp_phone_number_id: waPhoneId.trim() || undefined,
      })
      setWaSaved(true); setTimeout(() => setWaSaved(false), 3000)
    } catch { setWaError('Opslaan mislukt. Probeer opnieuw.') }
    finally  { setWaSaving(false) }
  }

  async function saveCrm() {
    setCrmSaving(true); setCrmError('')
    const payload: Record<string, unknown> = { crm_type: crmType }
    if (crmType === 'airtable' && atApiKey.trim()) {
      payload.airtable = {
        api_key:    atApiKey.trim(),
        base_id:    atBaseId.trim(),
        table_name: atTable.trim() || 'Leads',
      }
    }
    try {
      await api.organizations.update(org.id, payload)
      setCrmSaved(true); setTimeout(() => setCrmSaved(false), 3000)
    } catch { setCrmError('Opslaan mislukt. Probeer opnieuw.') }
    finally  { setCrmSaving(false) }
  }

  function copyWebhook() {
    navigator.clipboard.writeText(webhookUrl).catch(() => {})
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">

      {/* ── Bedrijfsprofiel ──────────────────────────────────────────────── */}
      <Section
        title="Bedrijfsprofiel"
        description="Naam en sector van je organisatie."
        onSave={saveProfile}
        saving={pSaving}
        saved={pSaved}
        error={pError}
      >
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
          <SelectField value={sector} onChange={e => setSector(e.target.value)}>
            {SECTORS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </SelectField>
        </div>
      </Section>

      {/* ── AI-assistent ─────────────────────────────────────────────────── */}
      <Section
        title="AI-assistent"
        description="Hoe communiceert de AI-receptionist met jouw klanten?"
        onSave={saveAi}
        saving={aiSaving}
        saved={aiSaved}
        error={aiError}
      >
        <div>
          <Label>Communicatiestijl</Label>
          <SelectField value={aiTone} onChange={e => setAiTone(e.target.value)}>
            <option value="formeel">Formeel (vousvoyeren — u)</option>
            <option value="informeel">Informeel (tutoyeren — je/jij)</option>
          </SelectField>
        </div>
        <div>
          <Label optional>Aangepaste instructies</Label>
          <textarea
            rows={6}
            value={aiPrompt}
            onChange={e => setAiPrompt(e.target.value)}
            placeholder={
              'bv.\nWij zijn actief in Gent en omgeving.\nOpeningsuren: ma–vr 8u–17u.\nSpoedlijn: 09 123 45 67.'
            }
            className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-1 text-xs text-gray-400">
            De AI voegt dit als context toe aan elk gesprek.
          </p>
        </div>
      </Section>

      {/* ── WhatsApp koppeling ───────────────────────────────────────────── */}
      <Section
        title="WhatsApp koppeling"
        description="Koppel je Meta / WhatsApp Business nummer aan de AI-receptionist."
        onSave={saveWhatsApp}
        saving={waSaving}
        saved={waSaved}
        error={waError}
      >
        {/* Webhook URL */}
        <div>
          <Label>Webhook URL</Label>
          <div className="mt-1 flex items-center gap-2">
            <code className="min-w-0 flex-1 truncate rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs text-gray-600">
              {webhookUrl}
            </code>
            <button
              type="button"
              onClick={copyWebhook}
              className="flex shrink-0 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-600 transition-colors hover:bg-gray-50"
            >
              {copied
                ? <><Check className="h-4 w-4 text-green-600" /> Gekopieerd</>
                : <><Copy className="h-4 w-4" /> Kopiëren</>
              }
            </button>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            Plak dit in{' '}
            <a
              href="https://business.facebook.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-0.5 text-indigo-600 hover:underline"
            >
              Meta Business <ExternalLink className="h-3 w-3" />
            </a>
            {' '}→ WhatsApp → Configuratie → Webhook
          </p>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <div>
            <Label optional>WhatsApp-nummer</Label>
            <Input
              value={waNumber}
              onChange={e => setWaNumber(e.target.value)}
              placeholder="+32468123456"
            />
          </div>
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

        {/* Status */}
        {(org.whatsapp_number || org.whatsapp_phone_number_id) ? (
          <div className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2.5 text-sm text-green-700 ring-1 ring-green-200">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            WhatsApp is gekoppeld
            {org.whatsapp_number && (
              <span className="ml-auto font-mono text-xs text-green-600">{org.whatsapp_number}</span>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-2.5 text-sm text-amber-700 ring-1 ring-amber-200">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            WhatsApp nog niet gekoppeld
          </div>
        )}
      </Section>

      {/* ── CRM koppeling ────────────────────────────────────────────────── */}
      <Section
        title="CRM koppeling"
        description="Kies waar nieuwe leads automatisch naartoe gestuurd worden."
        onSave={saveCrm}
        saving={crmSaving}
        saved={crmSaved}
        error={crmError}
      >
        {/* Huidig CRM status */}
        {org.crm_type !== 'none' && (
          <div className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2.5 text-sm text-green-700 ring-1 ring-green-200">
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
            {org.crm_type === 'airtable' ? 'Airtable actief' : org.crm_type}
          </div>
        )}

        <div>
          <Label>CRM type</Label>
          <SelectField value={crmType} onChange={e => setCrmType(e.target.value)}>
            <option value="none">Geen CRM</option>
            <option value="airtable">Airtable</option>
            <option value="hubspot" disabled>HubSpot (binnenkort)</option>
            <option value="pipedrive" disabled>Pipedrive (binnenkort)</option>
          </SelectField>
        </div>

        {crmType === 'airtable' && (
          <div className="space-y-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-xs font-medium text-indigo-700">
              {org.crm_type === 'airtable'
                ? '✅ Airtable is actief. Vul nieuwe credentials in om te updaten — leeg laten = huidige behouden.'
                : 'Vul je Airtable credentials in om de koppeling te activeren.'}
            </p>
            <div>
              <Label optional={org.crm_type === 'airtable'}>Personal Access Token</Label>
              <Input
                type="password"
                value={atApiKey}
                onChange={e => setAtApiKey(e.target.value)}
                placeholder={
                  org.crm_type === 'airtable'
                    ? '••••••••••• (leeg = niet wijzigen)'
                    : 'pat7hqea…'
                }
              />
              <p className="mt-1 text-xs text-gray-400">
                Maak aan via{' '}
                <a
                  href="https://airtable.com/create/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-indigo-600 hover:underline"
                >
                  airtable.com/create/tokens <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            </div>
            <div>
              <Label optional={org.crm_type === 'airtable'}>Base ID</Label>
              <Input
                value={atBaseId}
                onChange={e => setAtBaseId(e.target.value)}
                placeholder="appXXXXXXXXXXXXXX"
              />
              <p className="mt-1 text-xs text-gray-400">
                Te vinden in de URL van je Airtable base
              </p>
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

    </div>
  )
}
