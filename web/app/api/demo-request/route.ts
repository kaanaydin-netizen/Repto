import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const name = String(body.name ?? '').trim()
    const email = String(body.email ?? '').trim()
    const company = String(body.company ?? '').trim()
    const sector = String(body.sector ?? '').trim()
    const message = String(body.message ?? '').trim()

    if (!name || !email || !message) {
      return NextResponse.json({ error: 'Vul je naam, e-mail en bericht in.' }, { status: 400 })
    }

    // Elke demoaanvraag wordt een echte lead in de backend (increment 2, web-form-kanaal).
    // org_id staat in een server-env var — de browser ziet het nooit (CORS + spam-mitigatie).
    // Best-effort: een falende intake mag de marketingmail/UX niet blokkeren.
    const leadCaptured = await forwardToIntake({ name, email, company, sector, message })

    // Marketingmail blijft als extra. Zonder Resend valt alles terug op de lead-capture.
    const apiKey = process.env.RESEND_API_KEY
    if (!apiKey) {
      if (leadCaptured) return NextResponse.json({ ok: true })
      return NextResponse.json({ error: 'not_configured', fallbackEmail: 'info@repto.be' }, { status: 503 })
    }

    const from = process.env.CONTACT_FROM ?? 'Repto website <contact@repto.be>'
    const to = process.env.CONTACT_EMAIL ?? 'info@repto.be'

    const html = `
      <h2>Nieuwe demoaanvraag</h2>
      <p><strong>Naam:</strong> ${escapeHtml(name)}</p>
      <p><strong>E-mail:</strong> ${escapeHtml(email)}</p>
      <p><strong>Bedrijf:</strong> ${escapeHtml(company || '-')}</p>
      <p><strong>Sector:</strong> ${escapeHtml(sector || '-')}</p>
      <p><strong>Bericht:</strong></p>
      <p>${escapeHtml(message).replace(/\n/g, '<br>')}</p>
    `

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from, to, reply_to: email, subject: `Demoaanvraag van ${name}`, html }),
    })

    if (!res.ok) {
      // Mail mislukt: als de lead wél is vastgelegd, is de aanvraag toch geslaagd.
      if (leadCaptured) return NextResponse.json({ ok: true })
      return NextResponse.json({ error: 'Verzenden mislukt.' }, { status: 502 })
    }

    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ error: 'Ongeldige aanvraag.' }, { status: 400 })
  }
}

/**
 * Stuur de aanvraag server-side door naar het backend web-form-intake-endpoint.
 * Geeft true terug bij een 2xx. Niet geconfigureerd (ontbrekende env) of een fout →
 * false, zonder te gooien: de marketingmail blijft dan de fallback.
 */
async function forwardToIntake(input: {
  name: string
  email: string
  company: string
  sector: string
  message: string
}): Promise<boolean> {
  const apiUrl = process.env.REPTO_API_URL
  const orgId = process.env.REPTO_INTAKE_ORG_ID
  if (!apiUrl || !orgId) return false

  try {
    const res = await fetch(`${apiUrl.replace(/\/$/, '')}/intake/web-form`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        org_id: orgId,
        name: input.name,
        email: input.email,
        company: input.company || undefined,
        sector: input.sector || undefined,
        message: input.message || undefined,
      }),
    })
    return res.ok
  } catch {
    return false
  }
}

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
