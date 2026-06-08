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

## 2. Backfill gehard + getest (afgerond, nog niet gecommit)

`api/backfill_airtable_contact_key.py` — herkeyt Airtable-records van `conversation.id`
naar `contact.id` (slice C).
- Herschreven: groepeert **alle** records per `contact.id` (al-correcte + conv-gekeyde) →
  idempotent en veilig óók als het ooit ná de code-deploy draait. Throttle onder Airtable's
  rate-limit; een mislukte survivor-PATCH behoudt de duplicaten (geen dataverlies).
- `api/tests/test_backfill_airtable_contact_key.py` — 5 tests (gemockte Airtable + SQLite):
  dry-run raakt niets aan, rewrite/collapse, idempotentie, post-deploy-veiligheid,
  mislukte-PATCH.

---

## 3. Deploy-runbook (afgerond, nog niet gecommit)

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

**Prod-DB nu op `004 (head)`.** Verbinding via Supabase **Session pooler**
(`aws-0-eu-west-1.pooler.supabase.com:5432`, project-ref `uszmqsfbhpienhcasjkd`); de directe
host is IPv6-only en werkt niet op IPv4-netwerken.

---

## 5. Nog te doen

**Direct / belangrijk**
- [ ] 🔐 **Database-wachtwoord roteren** — het is tijdens deze sessie in de chat geplakt.
      Supabase → Settings → Database → Reset database password.
- [ ] De stap-2/3-artefacten committen: geharde backfill + test + runbook + dit verslag.
- [ ] **Code live zetten** (increment-2-code naar prod): Railway (backend) + Vercel (web).
      Migraties zijn al gedaan; backfill is no-op → code mag rechtstreeks live.

**Env-vars vóór de kanalen werken**
- [ ] Web (Vercel): `REPTO_API_URL`, `REPTO_INTAKE_ORG_ID` (anders verbergt de chat-widget
      zich en valt de demo-form terug op enkel mail).
- [ ] Backend (Railway), 2b e-mail: `RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET`,
      `EMAIL_INTAKE_DOMAIN` (+ MX naar Resend), `EMAIL_INTAKE_FROM`, `NOTIFICATION_FROM`.

**Opvolging**
- [ ] Sign-off op fundament A-C + 2a/2b/2c (eigenaar).
- [ ] Bij WhatsApp-live: launcher-posities van WhatsApp- en chat-widget verzoenen (beide
      `bottom-6 right-6`).
- [ ] Niet-blokkerend (genoteerd): web-form resubmit stuurt elke keer notificatie;
      web_form/web_chat-gesprekken bereiken nooit 'closed' tenzij afgerond.

---

## 6. Aandachtspunt

De CRM-notities meldden een werkende Airtable-mini-CRM, maar prod heeft **geen** org met
`crm_type='airtable'`. Verifieer welke `crm_type` de prod-org(s) hebben (mogelijk `'none'`
of een testomgeving) zodat duidelijk is of CRM-sync überhaupt actief moet zijn voor deze klant.
