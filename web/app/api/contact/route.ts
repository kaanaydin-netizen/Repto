/**
 * POST /api/contact
 * Verwerkt het contactformulier van de publieke website.
 *
 * Verstuurt de vraag per e-mail naar Info@repto.be via de Resend REST API
 * (geen extra npm-dependency nodig — we gebruiken fetch). Werkt alleen zodra
 * RESEND_API_KEY is ingesteld én het afzenddomein in Resend geverifieerd is.
 * Zolang dat niet zo is, geeft de route een nette fout terug zodat het
 * formulier de bezoeker naar het directe e-mailadres kan verwijzen.
 */
import { NextRequest, NextResponse } from 'next/server'

const CONTACT_TO = process.env.CONTACT_EMAIL ?? 'Info@repto.be'
// Afzender moet op een in Resend geverifieerd domein staan.
const CONTACT_FROM = process.env.CONTACT_FROM ?? 'Repto website <contact@repto.be>'

interface ContactBody {
  name?: string
  email?: string
  message?: string
  // Honeypot — moet leeg blijven; bots vullen 'm vaak wel in.
  company?: string
}

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

export async function POST(request: NextRequest) {
  let body: ContactBody
  try {
    body = (await request.json()) as ContactBody
  } catch {
    return NextResponse.json({ error: 'Ongeldige aanvraag' }, { status: 400 })
  }

  const name = body.name?.trim() ?? ''
  const email = body.email?.trim() ?? ''
  const message = body.message?.trim() ?? ''

  // Honeypot: stilletjes "ok" teruggeven zodat de bot niets merkt.
  if (body.company && body.company.trim() !== '') {
    return NextResponse.json({ ok: true })
  }

  if (!name || !email || !message) {
    return NextResponse.json({ error: 'Vul je naam, e-mail en vraag in.' }, { status: 400 })
  }
  if (!isValidEmail(email)) {
    return NextResponse.json({ error: 'Vul een geldig e-mailadres in.' }, { status: 400 })
  }
  if (message.length > 5000) {
    return NextResponse.json({ error: 'Je bericht is te lang.' }, { status: 400 })
  }

  const apiKey = process.env.RESEND_API_KEY
  if (!apiKey) {
    // E-mailservice nog niet geconfigureerd — laat het formulier de bezoeker
    // naar het directe adres verwijzen i.p.v. stil te falen.
    return NextResponse.json(
      { error: 'not_configured', fallbackEmail: CONTACT_TO },
      { status: 503 },
    )
  }

  const html = `
    <h2>Nieuwe vraag via repto.be</h2>
    <p><strong>Naam:</strong> ${escapeHtml(name)}</p>
    <p><strong>E-mail:</strong> ${escapeHtml(email)}</p>
    <p><strong>Bericht:</strong></p>
    <p>${escapeHtml(message).replace(/\n/g, '<br>')}</p>
  `

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: CONTACT_FROM,
        to: [CONTACT_TO],
        reply_to: email,
        subject: `Contactvraag van ${name}`,
        html,
      }),
    })

    if (!res.ok) {
      const detail = await res.text()
      console.error('Resend-fout:', res.status, detail)
      return NextResponse.json({ error: 'Verzenden mislukt. Probeer later opnieuw.' }, { status: 502 })
    }

    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error('Contactformulier-fout:', err)
    return NextResponse.json({ error: 'Verzenden mislukt. Probeer later opnieuw.' }, { status: 502 })
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
