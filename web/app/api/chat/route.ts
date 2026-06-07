import { NextRequest, NextResponse } from 'next/server'

/**
 * Web-chat-proxy (increment 2, slice 2c). De browser praat NOOIT rechtstreeks met de
 * backend: deze route injecteert server-side het `org_id` uit een env-var (net als de
 * web-form-intake), zodat het org_id niet in de client-bundle belandt en niemand met de
 * org_id elders AI-kosten kan opdrijven. Eén beurt per POST: { sessionId, message } in,
 * { reply, closed } uit. Het sessie-id houdt het gesprek + geheugen aan backend-zijde vast.
 */
export async function POST(request: NextRequest) {
  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Ongeldige aanvraag.' }, { status: 400 })
  }

  const b = (body ?? {}) as Record<string, unknown>
  const sessionId = String(b.sessionId ?? '').trim()
  const message = String(b.message ?? '').trim()
  if (!sessionId || !message) {
    return NextResponse.json({ error: 'Sessie en bericht zijn verplicht.' }, { status: 400 })
  }

  const apiUrl = process.env.REPTO_API_URL
  const orgId = process.env.REPTO_INTAKE_ORG_ID
  if (!apiUrl || !orgId) {
    // Niet geconfigureerd → de widget verbergt zichzelf op basis van deze status.
    return NextResponse.json({ error: 'not_configured' }, { status: 503 })
  }

  try {
    const res = await fetch(`${apiUrl.replace(/\/$/, '')}/intake/web-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ org_id: orgId, session_id: sessionId, message }),
    })
    if (!res.ok) {
      return NextResponse.json({ error: 'De assistent is even niet bereikbaar.' }, { status: 502 })
    }
    const data = (await res.json()) as { reply?: string; closed?: boolean }
    return NextResponse.json({ reply: data.reply ?? '', closed: Boolean(data.closed) })
  } catch {
    return NextResponse.json({ error: 'De assistent is even niet bereikbaar.' }, { status: 502 })
  }
}
