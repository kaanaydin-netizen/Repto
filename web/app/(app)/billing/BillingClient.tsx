'use client'
import { useState } from 'react'
import { Check, Zap, ExternalLink, AlertCircle, CreditCard } from 'lucide-react'
import { PLANS, type PlanKey } from '@/lib/plans'
import type { StripeMetadata } from './page'

// ─── Hulpfuncties ─────────────────────────────────────────────────────────────

const PLAN_KEYS = Object.keys(PLANS) as PlanKey[]

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  active:    { label: 'Actief',      color: 'bg-green-50 text-green-700 ring-green-200' },
  past_due:  { label: 'Betaling open', color: 'bg-amber-50 text-amber-700 ring-amber-200' },
  cancelled: { label: 'Opgezegd',    color: 'bg-gray-100 text-gray-500 ring-gray-200' },
  trialing:  { label: 'Proefperiode', color: 'bg-indigo-50 text-indigo-700 ring-indigo-200' },
}

// ─── Hoofd component ──────────────────────────────────────────────────────────

interface Props {
  meta: StripeMetadata
  successParam: boolean
  cancelledParam: boolean
}

export default function BillingClient({ meta, successParam, cancelledParam }: Props) {
  const [loading, setLoading] = useState<PlanKey | 'portal' | null>(null)
  const [error, setError] = useState('')
  const [notification, setNotification] = useState(
    successParam
      ? '🎉 Betaling geslaagd! Welkom bij Repto. Je abonnement is actief.'
      : cancelledParam
      ? ''
      : ''
  )

  const currentPlan = meta.stripePlan as PlanKey | null | undefined
  const hasActiveSubscription = meta.stripeStatus === 'active' || meta.stripeStatus === 'trialing'

  async function handleCheckout(plan: PlanKey) {
    setLoading(plan)
    setError('')
    try {
      const res = await fetch('/api/stripe/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Onbekende fout')
      window.location.href = data.url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout aanmaken mislukt.')
      setLoading(null)
    }
  }

  async function handlePortal() {
    setLoading('portal')
    setError('')
    try {
      const res = await fetch('/api/stripe/portal', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Onbekende fout')
      window.location.href = data.url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Customer portal openen mislukt.')
      setLoading(null)
    }
  }

  return (
    <div>
      {/* Notificatie banner */}
      {notification && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          <Check className="h-5 w-5 shrink-0 text-green-600" />
          <p>{notification}</p>
          <button
            onClick={() => setNotification('')}
            className="ml-auto text-green-500 hover:text-green-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* Foutmelding */}
      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
          {error}
        </div>
      )}

      {/* Huidig plan samenvatting */}
      {hasActiveSubscription && currentPlan && PLANS[currentPlan] && (
        <div className="mb-8 flex items-center justify-between rounded-xl border border-indigo-200 bg-indigo-50 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold text-indigo-900">
                {PLANS[currentPlan].name} plan
              </p>
              <p className="text-sm text-indigo-700">
                €{PLANS[currentPlan].price}/maand · Automatisch verlengd
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {meta.stripeStatus && STATUS_LABELS[meta.stripeStatus] && (
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${STATUS_LABELS[meta.stripeStatus].color}`}>
                {STATUS_LABELS[meta.stripeStatus].label}
              </span>
            )}
            <button
              onClick={handlePortal}
              disabled={loading === 'portal'}
              className="flex items-center gap-1.5 rounded-lg border border-indigo-300 bg-white px-3 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-50 disabled:opacity-60"
            >
              {loading === 'portal' ? 'Laden…' : (
                <><ExternalLink className="h-4 w-4" /> Beheer abonnement</>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Pricing cards */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {PLAN_KEYS.map((planKey) => {
          const plan = PLANS[planKey]
          const isActive = currentPlan === planKey && hasActiveSubscription
          const isPopular = 'popular' in plan && plan.popular

          return (
            <div
              key={planKey}
              className={`relative flex flex-col rounded-2xl border-2 bg-white p-6 shadow-sm transition-shadow hover:shadow-md ${
                isActive
                  ? 'border-indigo-600 ring-4 ring-indigo-100'
                  : isPopular
                  ? 'border-indigo-300'
                  : 'border-gray-200'
              }`}
            >
              {/* Populair badge */}
              {isPopular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="flex items-center gap-1 rounded-full bg-indigo-600 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white shadow">
                    <Zap className="h-3 w-3" />
                    Meest gekozen
                  </span>
                </div>
              )}

              {/* Huidig plan badge */}
              {isActive && (
                <div className="absolute -top-3.5 right-4">
                  <span className="rounded-full bg-green-600 px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white shadow">
                    Huidig plan
                  </span>
                </div>
              )}

              {/* Plan naam & prijs */}
              <div className="mb-5">
                <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-gray-900">€{plan.price}</span>
                  <span className="text-sm text-gray-500">/maand</span>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  {plan.klanten === Infinity ? 'Onbeperkt klanten' : `${plan.klanten} klant${plan.klanten > 1 ? 'en' : ''}`}
                  {' · '}
                  {plan.gesprekken}
                </p>
              </div>

              {/* Features */}
              <ul className="mb-6 flex-1 space-y-2.5">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-gray-700">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" />
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA knop */}
              {isActive ? (
                <button
                  onClick={handlePortal}
                  disabled={loading === 'portal'}
                  className="w-full rounded-xl border-2 border-indigo-600 bg-white py-3 text-sm font-semibold text-indigo-700 transition-colors hover:bg-indigo-50 disabled:opacity-60"
                >
                  {loading === 'portal' ? 'Laden…' : 'Abonnement beheren'}
                </button>
              ) : (
                <button
                  onClick={() => handleCheckout(planKey)}
                  disabled={loading !== null}
                  className={`w-full rounded-xl py-3 text-sm font-semibold text-white transition-colors disabled:opacity-60 ${
                    isPopular
                      ? 'bg-indigo-600 hover:bg-indigo-700'
                      : 'bg-gray-800 hover:bg-gray-900'
                  }`}
                >
                  {loading === planKey
                    ? 'Laden…'
                    : hasActiveSubscription
                    ? 'Overstappen'
                    : 'Abonneren'}
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Garantie / info */}
      <div className="mt-8 rounded-xl border border-gray-200 bg-gray-50 p-5 text-center text-sm text-gray-500">
        <p>
          🔒 Veilige betaling via{' '}
          <a
            href="https://stripe.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-indigo-600 hover:underline"
          >
            Stripe
          </a>
          {' '}· 30 dagen niet-goed-geld-terug garantie · Opzeggen wanneer je wil
        </p>
      </div>
    </div>
  )
}
