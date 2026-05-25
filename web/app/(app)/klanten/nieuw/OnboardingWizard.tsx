'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Check, ChevronRight, Building2, Bot, Phone, Database, PartyPopper, Copy } from 'lucide-react'
import { api } from '@/lib/api'
import type { OrganizationCreate } from '@/lib/types'

// ─── Types ─────────────────────────────────────────────────────────────────────

interface FormData {
  // Stap 1 — Bedrijf
  name: string
  sector: string

  // Stap 2 — AI
  ai_tone: string
  ai_system_prompt: string

  // Stap 3 — WhatsApp
  whatsapp_number: string
  whatsapp_phone_number_id: string

  // Stap 4 — Airtable
  airtable_api_key: string
  airtable_base_id: string
  airtable_table_name: string
}

const INITIAL: FormData = {
  name: '',
  sector: 'algemeen',
  ai_tone: 'formeel',
  ai_system_prompt: '',
  whatsapp_number: '',
  whatsapp_phone_number_id: '',
  airtable_api_key: '',
  airtable_base_id: '',
  airtable_table_name: 'Leads',
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

// ─── Stap-definitie ────────────────────────────────────────────────────────────

const STEPS = [
  { id: 1, label: 'Bedrijf',   icon: Building2 },
  { id: 2, label: 'AI',        icon: Bot },
  { id: 3, label: 'WhatsApp',  icon: Phone },
  { id: 4, label: 'Airtable',  icon: Database },
  { id: 5, label: 'Klaar',     icon: PartyPopper },
]

// ─── Kleine hulpcomponenten ────────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-700">{children}</label>
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 disabled:bg-gray-50 disabled:text-gray-400"
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

function SkipBadge() {
  return (
    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-500">
      Optioneel
    </span>
  )
}

// ─── Hoofd-wizard ──────────────────────────────────────────────────────────────

export default function OnboardingWizard() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState<FormData>(INITIAL)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdOrg, setCreatedOrg] = useState<{ id: string; name: string } | null>(null)
  const [copied, setCopied] = useState(false)

  const set = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => setForm(prev => ({ ...prev, [field]: e.target.value }))

  // ── Navigatie ────────────────────────────────────────────────────────────────

  function canProceed() {
    if (step === 1) return form.name.trim().length >= 2
    return true
  }

  function next() {
    if (step < 4) setStep(s => s + 1)
    else handleSubmit()
  }

  function back() {
    if (step > 1) setStep(s => s - 1)
  }

  // ── Opslaan ──────────────────────────────────────────────────────────────────

  async function handleSubmit() {
    setLoading(true)
    setError('')

    // Haal Clerk user ID op voor multi-tenant koppeling
    let clerkUserId: string | undefined
    try {
      const res = await fetch('/api/user/primary-org')
      if (res.ok) {
        // Clerk user ID is beschikbaar — stuur het mee als header
        // We lezen het indirect via de primary-org response context
      }
    } catch { /* stil falen */ }

    const payload: OrganizationCreate = {
      name: form.name.trim(),
      sector: form.sector,
      ai_tone: form.ai_tone,
      ai_system_prompt: form.ai_system_prompt.trim() || undefined,
      whatsapp_number: form.whatsapp_number.trim() || undefined,
      whatsapp_phone_number_id: form.whatsapp_phone_number_id.trim() || undefined,
      crm_type: form.airtable_api_key.trim() ? 'airtable' : 'none',
    }

    if (form.airtable_api_key.trim()) {
      payload.airtable = {
        api_key: form.airtable_api_key.trim(),
        base_id: form.airtable_base_id.trim(),
        table_name: form.airtable_table_name.trim() || 'Leads',
      }
    }

    try {
      const org = await api.organizations.create(payload)

      // Sla org ID op als primaire org (Clerk metadata + cookie)
      await fetch('/api/user/primary-org', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orgId: org.id }),
      })

      setCreatedOrg({ id: org.id, name: org.name })
      setStep(5)
    } catch (e) {
      setError('Aanmaken mislukt. Controleer je invoer en probeer opnieuw.')
    } finally {
      setLoading(false)
    }
  }

  function copyOrgId() {
    if (!createdOrg) return
    navigator.clipboard.writeText(createdOrg.id)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-full flex-col items-center justify-start px-4 py-12">
      {/* Stap-indicator */}
      <div className="mb-10 flex items-center gap-0">
        {STEPS.map((s, i) => {
          const done = step > s.id
          const active = step === s.id
          const Icon = s.icon
          return (
            <div key={s.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-full border-2 transition-colors ${
                    done
                      ? 'border-indigo-600 bg-indigo-600 text-white'
                      : active
                      ? 'border-indigo-600 bg-white text-indigo-600'
                      : 'border-gray-200 bg-white text-gray-400'
                  }`}
                >
                  {done ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                </div>
                <span
                  className={`mt-1.5 text-[10px] font-medium ${
                    active ? 'text-indigo-600' : done ? 'text-gray-600' : 'text-gray-400'
                  }`}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`mb-4 h-px w-16 transition-colors ${
                    step > s.id ? 'bg-indigo-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Kaart */}
      <div className="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">

        {/* ── Stap 1: Bedrijf ─────────────────────────────────────────────── */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Bedrijfsgegevens</h2>
              <p className="mt-1 text-sm text-gray-500">Hoe heet de klant en in welke sector werken ze?</p>
            </div>
            <div>
              <Label>Bedrijfsnaam *</Label>
              <Input
                autoFocus
                placeholder="bv. Loodgieters De Smedt"
                value={form.name}
                onChange={set('name')}
              />
            </div>
            <div>
              <Label>Sector</Label>
              <Select value={form.sector} onChange={set('sector')}>
                {SECTORS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </Select>
            </div>
          </div>
        )}

        {/* ── Stap 2: AI ──────────────────────────────────────────────────── */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">AI-assistent</h2>
              <p className="mt-1 text-sm text-gray-500">Hoe communiceert de AI met klanten?</p>
            </div>
            <div>
              <Label>Communicatiestijl</Label>
              <Select value={form.ai_tone} onChange={set('ai_tone')}>
                <option value="formeel">Formeel (vousvoyeren — u)</option>
                <option value="informeel">Informeel (tutoyeren — je/jij)</option>
              </Select>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Label>Extra instructies voor de AI</Label>
                <SkipBadge />
              </div>
              <textarea
                rows={5}
                placeholder={`bv.\nWij zijn actief in Gent en omgeving.\nOpeningsuren: ma–vr 8u–17u.\nSpoedlijn: 09 123 45 67.\nDiensten: CV-ketels, warmtepompen, sanitair.`}
                value={form.ai_system_prompt}
                onChange={set('ai_system_prompt')}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
              <p className="mt-1 text-xs text-gray-400">De AI voegt dit toe aan elke gesprekssessie.</p>
            </div>
          </div>
        )}

        {/* ── Stap 3: WhatsApp ────────────────────────────────────────────── */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-gray-900">WhatsApp koppeling</h2>
                <SkipBadge />
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Heb je al een Meta Business-nummer? Vul het hier in. Je kan dit later ook instellen.
              </p>
            </div>
            <div>
              <Label>WhatsApp-nummer</Label>
              <Input
                placeholder="+32 4xx xx xx xx"
                value={form.whatsapp_number}
                onChange={set('whatsapp_number')}
              />
              <p className="mt-1 text-xs text-gray-400">Inclusief landcode, bv. +32468123456</p>
            </div>
            <div>
              <Label>Phone Number ID (Meta)</Label>
              <Input
                placeholder="123456789012345"
                value={form.whatsapp_phone_number_id}
                onChange={set('whatsapp_phone_number_id')}
              />
              <p className="mt-1 text-xs text-gray-400">
                Vind je in Meta Business → WhatsApp → Telefoonbeheer
              </p>
            </div>
            <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-700 ring-1 ring-amber-200">
              <strong>Webhook URL na aanmaken:</strong> je krijgt straks een webhook-URL om in Meta in te stellen.
            </div>
          </div>
        )}

        {/* ── Stap 4: Airtable ────────────────────────────────────────────── */}
        {step === 4 && (
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-gray-900">Airtable CRM</h2>
                <SkipBadge />
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Leads worden automatisch naar Airtable gestuurd. Je kan dit later ook instellen.
              </p>
            </div>
            <div>
              <Label>Personal Access Token</Label>
              <Input
                type="password"
                placeholder="pat7hqea…"
                value={form.airtable_api_key}
                onChange={set('airtable_api_key')}
              />
              <p className="mt-1 text-xs text-gray-400">
                Maak aan via airtable.com → Account → Developer hub → Personal access tokens
              </p>
            </div>
            <div>
              <Label>Base ID</Label>
              <Input
                placeholder="appXXXXXXXXXXXXXX"
                value={form.airtable_base_id}
                onChange={set('airtable_base_id')}
              />
              <p className="mt-1 text-xs text-gray-400">
                Staat in de URL van je Airtable: airtable.com/appXXX/...
              </p>
            </div>
            <div>
              <Label>Tabelnaam</Label>
              <Input
                placeholder="Leads"
                value={form.airtable_table_name}
                onChange={set('airtable_table_name')}
              />
            </div>
          </div>
        )}

        {/* ── Stap 5: Klaar ───────────────────────────────────────────────── */}
        {step === 5 && createdOrg && (
          <div className="space-y-6 text-center">
            <div className="flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100">
                <Check className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{createdOrg.name} is aangemaakt!</h2>
              <p className="mt-2 text-sm text-gray-500">
                De klant staat nu in Repto. Bewaar de onderstaande gegevens.
              </p>
            </div>

            {/* Org ID */}
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-left">
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">Organisatie ID</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 break-all rounded-md bg-white px-2.5 py-1.5 text-xs text-gray-800 ring-1 ring-gray-200">
                  {createdOrg.id}
                </code>
                <button
                  onClick={copyOrgId}
                  className="flex-shrink-0 rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  title="Kopieer"
                >
                  {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Webhook URL */}
            <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-left">
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-indigo-500">WhatsApp Webhook URL</p>
              <code className="block break-all text-xs text-indigo-800">
                {`${process.env.NEXT_PUBLIC_API_URL || 'https://repto-production.up.railway.app'}/webhooks/whatsapp/${createdOrg.id}`}
              </code>
              <p className="mt-2 text-xs text-indigo-600">
                Stel deze URL in bij Meta Business → WhatsApp → Webhooks
              </p>
            </div>

            <div className="flex flex-col gap-3 pt-2">
              <button
                onClick={() => router.push(`/klanten/${createdOrg.id}`)}
                className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
              >
                Klantprofiel bekijken
              </button>
              <button
                onClick={() => router.push('/klanten')}
                className="w-full rounded-lg border border-gray-200 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Terug naar overzicht
              </button>
            </div>
          </div>
        )}

        {/* ── Foutmelding ──────────────────────────────────────────────────── */}
        {error && (
          <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
            {error}
          </div>
        )}

        {/* ── Knoppen ──────────────────────────────────────────────────────── */}
        {step < 5 && (
          <div className="mt-8 flex items-center justify-between">
            <button
              onClick={back}
              disabled={step === 1}
              className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:invisible transition-colors"
            >
              Vorige
            </button>
            <button
              onClick={next}
              disabled={!canProceed() || loading}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                'Aanmaken…'
              ) : step === 4 ? (
                'Aanmaken'
              ) : (
                <>
                  Volgende
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Skip links voor optionele stappen */}
      {(step === 3 || step === 4) && (
        <button
          onClick={next}
          className="mt-4 text-xs text-gray-400 underline underline-offset-2 hover:text-gray-600"
        >
          {step === 4 ? 'Overslaan en aanmaken zonder Airtable' : 'Overslaan — later instellen'}
        </button>
      )}
    </div>
  )
}
