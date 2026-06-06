# REPTO Upgrade — Increment 2: Multi-channel intake (web-form + e-mail + web-chat)

## Context

Increment 1 (`docs/INCREMENT_1_PLAN.md`, gemerged in `main` t/m `ac4b9fe`) legde de
**identiteits-/score-ruggengraat**: `Contact` (één lead per persoon), `resolve_contact`
(match op genormaliseerde e-mail OF telefoon), `compute_lead_score` (warm/lauw/koud) en de
inhaak in de WhatsApp-flow. Increment 2 = **dossier Fase 2 ("Kanalen aansluiten")**: e-mail,
website-formulier en website-chat laten *pluggen* op die ruggengraat, zodat een lead via elk
kanaal in hetzelfde klantprofiel belandt (dossier §3.2–§3.3).

**Besliste richting (door eigenaar, 2026-06-06):**
1. **Scope = alle drie de kanalen** (web-form + e-mail + web-chat) in dit increment. Om de
   tight-slice-werkwijze te bewaren is het plan opgebouwd als **één gedeeld fundament** (A–C)
   gevolgd door **drie afzonderlijke kanaal-slices** (2a/2b/2c), elk met een eigen DoD en een
   **stop voor sign-off**. Het fundament + 2a (web-form) is de eerste verticale, deploybare
   slice; 2b en 2c bouwen erop voort.
2. **Datamodel: `Conversation` generaliseren** (niet de dossier-`Interactions`-tabel). Lager
   risico, het werkende WhatsApp-pad blijft intact, elk nieuw kanaal hergebruikt de bestaande
   pipeline (verrijking → score → notificatie → CRM). De `Interactions`-refactor blijft het
   *eventuele* einddoel maar valt buiten dit increment.
3. **Bestaand Next.js demo-formulier** (`web/app/api/demo-request/route.ts`, mailt nu enkel via
   Resend) wordt **doorgestuurd naar het nieuwe web-form-kanaal**, zodat elke demoaanvraag een
   echte lead wordt. De marketingmail mag als extra blijven.

**Werkmap:** `/Users/kaanaydin/Desktop/Antigravity/Repto`. Maak een feature-branch
(`feat/multichannel-intake`). Stop na elke slice zodat de DoD afgetekend kan worden.

> **De spil van dit increment is het datamodel + de merge-logica, niet de endpoints.** De
> kanaal-endpoints zijn klein; het echte werk is dat `extract_and_enrich`, `sync_to_crm` en
> `send_lead_notification` allemaal op een `Conversation` werken terwijl `wa_contact_phone`
> NOT NULL is. Een web-/e-maillead heeft geen telefoonnummer → kan vandaag geen `Conversation`
> aanmaken → krijgt geen notify/score/CRM (exact de inertie die increment 1 voor `crm_type=none`
> oploste). Bouw het plan rond A–C.

---

## Status — fundament A–C AFGEROND (2026-06-06), wacht op sign-off

Branch `feat/multichannel-intake`. Suite groen (51 passed) op SQLite én op echte Postgres
(scratch-DB op rev 004) voor de identity-tests.

- **A — datamodel** ✅ `Conversation.wa_contact_phone` nu nullable + nieuwe `channel`-kolom
  (default `"whatsapp"`). Migratie `004` round-trip bewezen op scratch-Postgres
  (upgrade → channel NOT NULL + phone nullable; downgrade keert beide om; re-upgrade ok).
- **B — gedeelde intake + merge** ✅ Nieuw `lead_intake_service.create_or_update_conversation`
  (contact-gekeyd, kanaal-agnostisch); WhatsApp-pad loopt er nu doorheen. `resolve_contact`
  voegt het botsingsgeval (e-mail→B, telefoon→A) nu SAMEN (`_merge_contacts`: oudste wint,
  kanalen-unie, gesprekken herkoppeld, verliezer verwijderd). Tests: merge-botsing +
  regressievangnet "terugkerende WhatsApp-klant → zelfde gesprek".
- **C — Airtable per-persoon** ✅ (CODE) merge-key `conversation.id` → `contact.id`;
  Naam/Telefoon/E-mail uit het `Contact` (val terug op `conversation.wa_contact_*`).

> ⚠️ **DEPLOY-CONSTRAINT (C) — kop, geen voetnoot.** C's code mag NIET naar productie vóór
> de Airtable-backfill draait. De oude live records zijn op `conversation.id` gekeyd; de
> nieuwe upsert keyt op `contact.id` → zonder backfill ontstaan **duplicaat-records**.
> `api/backfill_airtable_contact_key.py` (dry-run default) verzorgt de gate + herkoppeling,
> maar is **PROVISIONEEL en ongetest tegen echte Airtable-data** — eerst de gate-output
> nalezen, dan pas `--apply`, en pas ná sign-off. **Deploy-volgorde:** migraties `003`+`004`
> op Supabase (prod staat op `002`) → backfill `--apply` → dan pas de nieuwe code live.

---

## Huidige relevante structuur (gevonden)

- `api/app/models/conversation.py:75` — `Conversation`; `wa_contact_phone` (regel 81) is
  **`nullable=False`**, `wa_contact_name` optioneel. Sinds increment 1: `contact_id` (FK→contacts).
- **Enige plek waar een `Conversation` wordt aangemaakt:** `whatsapp_service.py:80`
  (`get_or_create_conversation`). Alle andere kanalen moeten via een gedeelde helper.
- **Lezers van `wa_contact_phone`** (breken/aanpassen bij nullable):
  - `email_service.py:128-129` — `naam`/`telefoon` voor de agency-notificatie.
  - `crm_sync_service.py:250-252` — Airtable-payload (`Bron ID`, `Naam`, `Telefoon`); ook
    `:87` (log) en `:354`.
  - `reminder_service.py:92` — `contact_phone` voor WhatsApp-herinnering (blijft WhatsApp-specifiek).
  - `routers/conversations.py:25` — `ConversationOut.wa_contact_phone: str` (response-schema).
- `resolve_contact` (`identity_service.py:65`) — vind-één-of-maak; het **merge-geval** (e-mail
  matcht Contact B terwijl telefoon Contact A matchte) is in increment 1 **expliciet uitgesteld
  naar dit increment** (docstring regel 80-83). De huidige `or_(...).scalars().first()` (regel
  95-98) kiest bij zo'n botsing willekeurig één — onveilig zodra een tweede kanaal bestaat.
- `crm_sync_service.py` — Airtable-merge-key is increment 1 bewust nog **`Bron ID` =
  `conversation.id`** (één record per gesprek). Increment 1 stelde de omzetting naar
  `contact.id` uit naar **dit** increment (plan §F).
- `web/app/api/demo-request/route.ts` — losse Resend-mail, raakt de backend niet.
- `setup_airtable.py` — Leads-tabelschema (sinds increment 1 incl. `Score`/`Score Reden`).

---

## Fundament (gedeeld door alle kanalen)

### A. Datamodel — `Conversation` kanaal-agnostisch maken

`api/app/models/conversation.py`:
- `wa_contact_phone` → **`nullable=True`** (web-/e-maillead heeft geen nummer).
- Nieuwe kolom **`channel`** (`Mapped[str]`, default `"whatsapp"`) — `"whatsapp" | "email" |
  "web_form" | "web_chat"`. Backfill bestaande rijen op `"whatsapp"`.
- Overweeg hernoemen *vermijden*: laat `wa_contact_phone`/`wa_contact_name` staan (minder
  ruis/migratierisico); behandel ze als "het contactnummer/-naam zoals dit kanaal het kent".
  Het canonieke nummer leeft toch al op `Contact.phone` (genormaliseerd).

**Migratie `004_generalize_conversation_channel.py`** (`down_revision="003"`):
- `alter_column("conversations", "wa_contact_phone", nullable=True)`.
- `add_column("conversations", channel, server_default="whatsapp", nullable=False)` + backfill
  bestaande rijen expliciet (server_default dekt nieuwe rijen; zet bestaande ook hard op
  `"whatsapp"`). Index op `channel` optioneel.
- `downgrade`: kolom droppen + `nullable=False` terug (let op: faalt als er dan al
  null-telefoon-rijen zijn — documenteer dat downgrade enkel veilig is vóór niet-WhatsApp-leads).
- **Pre-deploy-gate (zoals Supabase bij increment 1):** `004` is additief/relaxerend
  (kolom toevoegen + NOT NULL → NULL), dus forward-safe; draai 'm op Supabase vóór de nieuwe
  code leads zonder telefoon aanmaakt.

### B. Gedeelde lead-intake helper + merge-logica

Nieuw: `api/app/services/lead_intake_service.py` (of uitbreiding van een bestaande service):
- `async create_or_update_conversation(db, org, *, channel, name, email, phone, message) ->
  Conversation` — de kanaal-agnostische tegenhanger van `whatsapp_service.get_or_create_conversation`:
  1. `resolve_contact(db, org.id, email=…, phone=…, name=…, channel=channel)`.
  2. Maak/hergebruik een `Conversation` met `channel`, koppel `contact_id`.
  3. Sla het inkomende bericht op (hergebruik `save_message`).
- **WhatsApp-pad migreren** om deze helper te gebruiken (één plek voor conversatie+contact),
  zodat alle kanalen identiek door verrijking/score/notificatie/CRM lopen.

**Contact-merge (verplicht — niet langer uitstelbaar):** breid `resolve_contact` uit zodat het
botsingsgeval (e-mail → Contact B, telefoon → Contact A, A≠B) wordt **samengevoegd** i.p.v.
willekeurig gekozen:
- Kies een "winnaar" (bv. oudste `created_at`), verplaats de `channels_json`-union en ontbrekende
  velden (email/phone/name/score) naar de winnaar, **herkoppel** alle `conversations.contact_id`
  van de verliezer naar de winnaar, verwijder de verliezer.
- **Verplichte test:** web-lead met e-mail X (maakt Contact B) → later WhatsApp met telefoon Y
  + e-mail X waar Y al Contact A was → resulteert in **één** Contact met beide kanalen en beide
  conversaties.

### C. Airtable-merge-key: `conversation.id` → `contact.id`

`crm_sync_service.py:250` — `"Bron ID"` wordt `contact.id` i.p.v. `conversation.id`, zodat één
persoon (meerdere gesprekken/kanalen) **één** Airtable-record is. `"Telefoon"`/`"Naam"` lezen
van het `Contact` (val terug op `conversation.wa_contact_*`).
- **Raakt LIVE data** (Airtable-base is geverifieerd werkend — zie [[crm-relationeel-voortgang]]).
  Pas dezelfde discipline toe als bij de Supabase-migratie: een **pre-migratie-gate** die de
  bestaande records inspecteert (welke `Bron ID`'s bestaan, mappen ze 1-op-1 op gesprekken) +
  een eenmalige backfill die bestaande records herkoppelt op `contact.id` zonder duplicaten.
- Documenteer dit als productie-aanrakende stap; draai pas na expliciete sign-off.

---

## Kanaal-slices

### 2a. Web-formulier (eerste verticale slice)

- Nieuw FastAPI-endpoint `POST /intake/web-form` (`routers/intake.py`): valideert server-side
  (naam, e-mail verplicht; sectorafhankelijke velden), bepaalt de `org` (via een client-/
  org-identifier in de payload — géén org-id raden), roept de helper (B) aan met
  `channel="web_form"`, draait verrijking + score, stuurt de agency-notificatie, en antwoordt
  met een nette bevestiging (200). Geen persoonsgegevens in URL — alles POST-body (dossier §7.4).
- **Next.js `demo-request` doorsturen:** de route postt naar dit endpoint i.p.v. (of naast) de
  Resend-mail; bij `not_configured`/fout een nette fallback.
- **email_service**: notificatie sourcet `naam`/`telefoon`/`email` van het `Contact` (val terug
  op `conversation.wa_contact_*`), en toont het `channel`-label.
- **DoD 2a:** een web-form-POST maakt/updatet één `Contact` + `Conversation(channel=web_form)`,
  zet score, stuurt notificatie; een web-lead met e-mail die later een WhatsApp-contact matcht
  wordt **één** profiel (merge-test uit B); geen hardcoded org/secrets. **Stop voor sign-off.**

### 2b. E-mail-intake

> **Open beslissing (te bevestigen bij start 2b): inbound-e-mailprovider.** Resend is enkel
> *uitgaand*. Inbound vereist óf IMAP-polling (een achtergrond-poller/cron) óf een
> inbound-parse-webhook (Postmark/SendGrid/Resend Inbound). Keuze bepaalt de infra. Aanbeveling
> in plan vastleggen vóór bouw.

- Trigger (poller of webhook) → parse afzender/onderwerp/body → `channel="email"` → helper (B).
- Bij ontbrekende verplichte velden: AI stuurt **max. één** opvolgmail met gerichte vragen vóór
  escalatie naar de eindklant (dossier §5.3). Hergebruik `email_service` (SMTP/Resend uitgaand).
- **DoD 2b:** een inkomende e-mail wordt een lead in hetzelfde profiel (match op e-mail);
  max. één opvolgmail; end-to-end getest met een realistisch bericht. **Stop voor sign-off.**

### 2c. Web-chat

- Conversationele widget met sessie-geheugen — feitelijk de WhatsApp-AI-lus op het web. Nieuw
  `POST /intake/web-chat` (sessie-id → `Conversation(channel=web_chat)`), hergebruikt de
  AI-agent + tool-use + afspraken-flow. Frontend-widget volgens de `frontend-design` skill.
- **DoD 2c:** een web-chatsessie kwalificeert conversationeel, koppelt aan het profiel, kan een
  afspraak plannen (vastgoedconfig); end-to-end getest. **Stop voor sign-off.**

---

## Bestanden (overzicht)

| Bestand | Wijziging |
|---|---|
| `api/app/models/conversation.py` | `wa_contact_phone` nullable + `channel`-kolom |
| `api/migrations/versions/004_generalize_conversation_channel.py` | nieuw — alter + add + backfill |
| `api/app/services/lead_intake_service.py` | nieuw — kanaal-agnostische conversatie+contact-helper |
| `api/app/services/identity_service.py` | `resolve_contact` + **merge-logica** (botsingsgeval) |
| `api/app/services/whatsapp_service.py` | WhatsApp-pad via de gedeelde helper |
| `api/app/services/crm_sync_service.py` | Airtable-key → `contact.id`; phone/naam van `Contact` |
| `api/app/services/email_service.py` | notificatie kanaal-agnostisch (Contact-velden + channel-label) |
| `api/app/routers/intake.py` | nieuw — `/intake/web-form`, `/intake/web-chat` |
| `api/app/routers/conversations.py` | `ConversationOut`: `wa_contact_phone` optioneel + `channel` |
| `web/app/api/demo-request/route.ts` | doorsturen naar `/intake/web-form` |
| `api/tests/test_identity_service.py` | merge-test (twee contacten samenvoegen) |
| `api/tests/test_lead_intake_service.py` | nieuw — web-form intake end-to-end (gemockt) |

---

## Verificatie (Definition of Done — dossier Fase 2)

1. **Migratie schoon**: `004` op dev-Postgres (+ scratch-DB round-trip zoals increment 1), daarna
   pre-deploy-gate + run op Supabase. Bestaande rijen krijgen `channel="whatsapp"`.
2. **Elk kanaal levert een correcte intake** aan de gedeelde helper (web-form getest in 2a,
   e-mail in 2b, web-chat in 2c).
3. **Kanaal-overschrijdend profiel**: een lead via web-form en later via WhatsApp (zelfde e-mail)
   = **één** `Contact`, beide `Conversation`s gekoppeld. Merge-botsingsgeval afgehandeld.
4. **E-mailkanaal** stuurt max. één opvolgmail bij ontbrekende velden.
5. **Airtable**: één persoon over meerdere kanalen = één record (`Bron ID = contact.id`);
   live-backfill zonder duplicaten, na pre-migratie-gate.
6. **Geen hardcoded secrets/org-ids/afzenderadressen** (dossier-regel).
7. **Stop na elke slice** (2a/2b/2c) voor sign-off vóór de volgende.

---

## Openstaande beslissing (vóór 2b)
- **Inbound-e-mailprovider:** IMAP-poller vs inbound-parse-webhook (Postmark/SendGrid/Resend
  Inbound). Aan eigenaar voor te leggen wanneer 2b start.

## Aanpalend (niet in dit increment, wel noteren)
- **Deploy-pipeline draait geen migraties** ([[increment-1-leadscoring-identity]]): `railway.toml`
  start enkel uvicorn. Aanrader: `alembic upgrade head` als release-stap inbouwen vóór 2a deployt,
  zodat `004` (en alle toekomstige) automatisch meegaan en de handmatige Supabase-stap vervalt.
