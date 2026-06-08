# Increment 2 — Deploy-runbook (slice C + kanaal-config)

> Doel: `feat/multichannel-intake` veilig live krijgen. Het hart is de **volgorde** rond
> slice C (Airtable-merge-sleutel `conversation.id` → `contact.id`). Verkeerde volgorde =
> duplicaat-Airtable-records. Lees dit één keer helemaal door vóór je begint.

## 0. Waarom de volgorde kritisch is

De nieuwe code keyt de Airtable-sync op **`contact.id`** (veld "Bron ID") i.p.v.
`conversation.id`. Bestaande live records staan nog op `conversation.id`. Deploy je de
code zonder eerst de bestaande records te herkeyen, dan vindt de eerste upsert geen match
en maakt hij **duplicaten**. Daarom geldt strikt:

```
migraties 003+004 (Supabase)  →  backfill dry-run + gate-review  →  backfill --apply  →  PAS DAN code live
```

De pipeline draait **bewust geen** migraties automatisch (Railway `startCommand` start enkel
uvicorn). Dat is met opzet: auto-migreren zou code + migraties samen live zetten en het
backfill-venster overslaan. Dus: handmatig, in deze volgorde.

---

## 1. Pre-flight

- [ ] Sign-off op fundament A-C + slices 2a/2b/2c (eigenaar).
- [ ] Branch `feat/multichannel-intake` is groen: `cd api && .venv/bin/python -m pytest tests/ -q` → 81 passed; `cd web && npx tsc --noEmit` → 0.
- [ ] **Supabase-backup**: maak een snapshot/PITR-punt van de prod-database (Supabase → Database → Backups). De backfill verwijdert Airtable-records, niet Supabase, maar een DB-snapshot vóór migraties is goedkope verzekering.
- [ ] **Airtable-backup**: dupliceer de Leads-tabel of exporteer naar CSV (Airtable → Leads → ⋯ → Duplicate / Download CSV). De `--apply` verwijdert records — dit is je terugvalpunt.
- [ ] Zet de prod-`DATABASE_URL` van Supabase klaar in je shell (de directe Postgres-connstring, niet de pooler-URL voor migraties):
  ```bash
  export DATABASE_URL="postgresql://postgres:<pw>@db.<ref>.supabase.co:5432/postgres"
  ```

---

## 2. Migraties 003 + 004 op Supabase

Prod staat op rev **002**. `upgrade head` brengt 'm via 003 naar **004**.

```bash
cd api
# Controle: welke revisie draait prod nu?
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic current      # verwacht: 002
# Toepassen (003 = contacts + scoring incl. backfill van contact_id; 004 = channel-kolom):
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic current      # verwacht nu: 004
```

> Migratie 003 vult `Conversation.contact_id` (genormaliseerd). De backfill in stap 3 leunt
> daarop — daarom moet 003 eerst draaien.

- [ ] `alembic current` toont `004`.

---

## 3. Airtable-backfill — dry-run + gate-review

Eerst **altijd** dry-run. Dit raakt niets aan en rapporteert het plan.

```bash
cd api
DATABASE_URL="$DATABASE_URL" .venv/bin/python backfill_airtable_contact_key.py
```

Lees de regel per org kritisch:
```
📋 <org>: <N> records | al-ok=<a> | herschrijven=<h> | contact-groepen=<g> | verwijderen=<d> | onresolvebaar=<u>
```
- **herschrijven** = records die van `conversation.id` naar `contact.id` gaan.
- **verwijderen** = overtollige records (zelfde persoon, meerdere gesprekken) die collaberen.
- **onresolvebaar** = Bron ID die op géén bekend gesprek mapt → **niet** aangeraakt. Als dit
  > 0 is: handmatig nakijken in Airtable vóór je verdergaat (kunnen handmatig toegevoegde of
  legacy-records zijn).

- [ ] Dry-run-output gereviewd en akkoord (eigenaar). `onresolvebaar` verklaard.

## 4. Backfill `--apply` (NA sign-off)

```bash
cd api
DATABASE_URL="$DATABASE_URL" .venv/bin/python backfill_airtable_contact_key.py --apply
```
Verwacht: `✅ Toegepast: <h> herschreven, <d> verwijderd.` De survivor van elke groep is nu
gekeyd op `contact.id`. Het script is idempotent en veilig om te herhalen.

- [ ] Steekproef in Airtable: enkele bestaande leads hebben nu `Bron ID = contact.id`, geen duplicaten.

---

## 5. Code live

Pas **na** stap 4. Merge `feat/multichannel-intake` → `main` (of deploy de branch), waarna
Railway (backend) en Vercel (web) bouwen.

- [ ] Backend (Railway) gedeployed en `Online` (healthcheck `/health`).
- [ ] Web (Vercel) gedeployed.
- [ ] Eerste echte WhatsApp/web-lead synct naar de **bestaande** survivor-records (geen nieuwe duplicaten).

---

## 6. Env-vars per kanaal

### Backend (Railway → service → Variables)
| Var | Voor | Waarde |
|---|---|---|
| `RESEND_API_KEY` | notificaties + 2b-opvolgmail | **nieuwe** key (zie stap 7) |
| `NOTIFICATION_FROM` | afzender notificatie | bv. `Repto <noreply@repto.be>` |
| `RESEND_WEBHOOK_SECRET` | 2b inbound-verificatie | Svix-secret `whsec_…` uit Resend-dashboard |
| `EMAIL_INTAKE_DOMAIN` | 2b plus-addressing | bv. `inbound.repto.be` |
| `EMAIL_INTAKE_FROM` | 2b opvolgmail-afzender | bv. `Repto <intake@repto.be>` |

### Web (Vercel → project `web` → Settings → Environment Variables)
| Var | Voor | Waarde |
|---|---|---|
| `REPTO_API_URL` | 2a + 2c server-side forward | de publieke backend-URL (Railway) |
| `REPTO_INTAKE_ORG_ID` | 2a + 2c org-injectie | de `Organization.id` van de demo-org |
| `RESEND_API_KEY` | demo-request marketingmail | **nieuwe** key |
| `CONTACT_FROM` / `CONTACT_EMAIL` | demo-request | afzender / ontvanger |

> Zonder `REPTO_API_URL` + `REPTO_INTAKE_ORG_ID` verbergt de **chat-widget** zich (proxy
> geeft 503) en valt de **demo-request** terug op enkel de marketingmail. Bewust gedrag.

- [ ] Backend-vars gezet + redeploy.
- [ ] Web-vars gezet (alle environments) + redeploy.

## 7. Resend: key-rotatie + inbound (2b)

- [ ] **Roteer de Resend API-key**: er stond ooit een echte key in `api/.env.example`
  (nooit gecommit, maar bekend). Maak in Resend een nieuwe key, zet die in Railway + Vercel
  (stap 6), en **revoke** de oude.
- [ ] **Inbound webhook**: Resend → Webhooks → endpoint `https://<backend>/webhooks/email`,
  kopieer het Svix-signing-secret naar `RESEND_WEBHOOK_SECRET`.
- [ ] **MX-record**: wijs `EMAIL_INTAKE_DOMAIN` (bv. `inbound.repto.be`) met MX naar Resend
  Inbound, conform Resend-docs. Verifieer in het dashboard.

---

## 8. Post-deploy-verificatie (per kanaal)

- [ ] **WhatsApp** (regressie): stuur een testbericht → lead synct naar de bestaande record (geen duplicaat).
- [ ] **Web-form (2a)**: dien een demo-aanvraag in op de site → lead verschijnt, score gezet.
- [ ] **E-mail (2b)**: mail naar `intake+<org_id>@<EMAIL_INTAKE_DOMAIN>` → lead in hetzelfde profiel; max één opvolgmail.
- [ ] **Web-chat (2c)**: open de widget op de landingspagina → AI antwoordt; voer een afspraak-flow → `Appointment` aangemaakt.

---

## Rollback

- **Migraties**: `alembic downgrade 002` (alleen als nodig; let op dataverlies van nieuwe kolommen).
- **Code**: Railway/Vercel → vorige deployment promoten.
- **Airtable**: herstel uit de CSV/duplicaat-tabel van stap 1. De backfill is idempotent, dus
  een herhaalde run na herstel is veilig.
- **Resend-key**: de oude key pas revoken nádat de nieuwe in beide deploys bevestigd werkt.
