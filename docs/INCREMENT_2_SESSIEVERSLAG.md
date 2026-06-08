# Increment 2 — Sessieverslag & deploy-status

_Bijgewerkt: 2026-06-08 · branch `feat/multichannel-intake`_

Verslag van wat in deze sessie is gebouwd, getest en op productie uitgevoerd voor
increment 2 (multi-channel intake). Zie ook `INCREMENT_2_PLAN.md` (plan) en
`INCREMENT_2_DEPLOY_RUNBOOK.md` (volledige deploy-procedure).

---

## 1. Slice 2c — web-chat (afgerond + gecommit)

Commit **`271f54a`** — `feat(intake): slice 2c web-chat`.

**Backend**
- `POST /intake/web-chat` (`api/app/routers/intake.py`): sessie-gekeyd, synchroon
  antwoordend; spiegelt de WhatsApp-lus (`process_incoming_message`): bericht opslaan →
  AI-antwoord → verrijking/score → bij `[GESPREK_AFGEROND]` afsluiten + notificatie →
  CRM-sync met de ≥3-berichten-gate.
- `lead_intake_service.get_or_create_web_chat_conversation`: deterministische
  `uuid5(org:session_id)` → vervolg-POSTs vinden hetzelfde gesprek + geheugen terug.
- `CLOSING_TAG` verhuisd naar `ai_service.py` (één bron voor WhatsApp + web-chat).
- **Bugfix** `whatsapp_service._reap_abandoned_contact`: een anoniem gestarte chat die
  later z'n e-mail noemt, herkoppelt naar het bestaande contact; het lege oude contact +
  z'n eventueel reeds gesyncte Airtable-record worden via de merge-cleanup opgeruimd
  (voorkomt verweesde contacten/duplicaten).

**Front-end**
- `web/components/ChatWidget.tsx`: zwevende chat-widget (indigo-brand), sessie-id in
  `sessionStorage`, praat via de server-side proxy `web/app/api/chat/route.ts` die
  `org_id` uit env injecteert → de browser ziet `org_id` nooit. Verbergt zich bij 503
  (niet geconfigureerd). Gemount op de landingspagina naast de WhatsApp-widget.

**Tests** — `api/tests/` groen (76 → met backfill 81 passed). Web `tsc` groen.
Web-chat-dekking: sessie-continuïteit, close+notify, open-geen-notify, ≥3-gate,
cross-channel merge mid-chat, synced-anoniem-geen-orphan-record, **afspraak boeken
end-to-end** (echte tool-use-lus, alleen de Anthropic-call gemockt), 404/422.

---

## 2. Backfill gehard + getest (afgerond + gecommit `8d0515e`)

`api/backfill_airtable_contact_key.py` — herkeyt Airtable-records van `conversation.id`
naar `contact.id` (slice C).
- Herschreven: groepeert **alle** records per `contact.id` (al-correcte + conv-gekeyde) →
  idempotent en veilig óók als het ooit ná de code-deploy draait. Throttle onder Airtable's
  rate-limit; een mislukte survivor-PATCH behoudt de duplicaten (geen dataverlies).
- `api/tests/test_backfill_airtable_contact_key.py` — 5 tests (gemockte Airtable + SQLite):
  dry-run raakt niets aan, rewrite/collapse, idempotentie, post-deploy-veiligheid,
  mislukte-PATCH.

---

## 3. Deploy-runbook (afgerond + gecommit `8d0515e`)

`docs/INCREMENT_2_DEPLOY_RUNBOOK.md` — turnkey checklist: migratie-volgorde, backfill-gate,
env-vars per kanaal (backend Railway + web Vercel), Resend key-rotatie + inbound MX,
verificatie per kanaal, rollback.

---

## 4. Productie-acties die in deze sessie zijn uitgevoerd

| Actie | Resultaat |
|---|---|
| `alembic current` (prod Supabase) | Prod stond op **`003`** — **correctie** t.o.v. notities die "002" zeiden. Migratie 003 (increment 1) was al live. |
| `alembic upgrade head` | **004 toegepast** (003 → 004: nullable phone + `channel`-kolom + backfill). Geverifieerd: `004 (head)`. |
| Backfill **dry-run** | **"Geen organisaties met crm_type='airtable'."** → geen Airtable-orgs in prod, backfill is een **no-op**. De slice-C-duplicaatzorg en de Airtable-CSV-backup zijn voor de huidige prod-staat **niet van toepassing**. |
| `git push … :main` | **Increment 2 + polish naar `main`** (`ac4b9fe..2162940`) → Railway- en Vercel-productiebuilds getriggerd. |
| Deploy-verificatie | Prod-OpenAPI bevat `/intake/web-chat`, `/intake/web-form`, `/webhooks/email` → **backend live op het 004-schema**. Web (Vercel) reageert 200. Backend = `repto-production.up.railway.app`. |

**Prod-DB nu op `004 (head)`.** Verbinding via Supabase **Session pooler**
(`aws-0-eu-west-1.pooler.supabase.com:5432`, project-ref `uszmqsfbhpienhcasjkd`); de directe
host is IPv6-only en werkt niet op IPv4-netwerken.

---

## 4b. Polish na de deploy (gecommit `2162940`)

- **Web-form → 'Op te volgen'**: een web-formulier is een eenmalige, volledige inzending. Het
  gesprek wordt nu meteen `closed` met opvolg-vlag → Airtable-status **'Op te volgen'** i.p.v.
  eeuwig 'Nieuw', en het telt niet meer als actief gesprek. `create_or_update_conversation`
  kreeg `reuse_any_status` zodat een herinzending hetzelfde gesprek hergebruikt (geen
  rij-proliferatie; WhatsApp/e-mail ongewijzigd). Nieuwe test dekt dit gedrag.
- **Launcher-overlap**: WhatsApp-knop naar `bottom-24 z-40` → botst niet met de web-chat-
  launcher (`bottom-6 z-50`) en verdwijnt achter het geopende chat-paneel.

Suite na polish: **82 passed**, web `tsc` groen.

---

## 5. Nog te doen

**Alleen nog dashboard-config (geen code meer) — maakt de kanalen actief**
- [ ] 🔐 **Database-wachtwoord roteren** — het is tijdens deze sessie in de chat geplakt.
      Supabase → Settings → Database → Reset database password.
- [ ] Web (Vercel): `REPTO_API_URL=https://repto-production.up.railway.app` +
      `REPTO_INTAKE_ORG_ID=<org id uit Supabase SQL Editor: select id,name from organizations>`,
      daarna **Redeploy**. Zonder deze twee verbergt de chat-widget zich en valt de demo-form
      terug op enkel mail.
- [ ] Backend (Railway), 2b e-mail: `RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET`,
      `EMAIL_INTAKE_DOMAIN` (+ MX naar Resend), `EMAIL_INTAKE_FROM`, `NOTIFICATION_FROM`
      + Resend-webhook → `https://repto-production.up.railway.app/webhooks/email`.

**Opvolging**
- [ ] Sign-off op fundament A-C + 2a/2b/2c (eigenaar).
- [ ] Na env-config: per kanaal testen (web-form, chat-widget op repto.be, e-mail-intake).

---

## 6. Aandachtspunt

De CRM-notities meldden een werkende Airtable-mini-CRM, maar prod heeft **geen** org met
`crm_type='airtable'`. Verifieer welke `crm_type` de prod-org(s) hebben (mogelijk `'none'`
of een testomgeving) zodat duidelijk is of CRM-sync überhaupt actief moet zijn voor deze klant.
