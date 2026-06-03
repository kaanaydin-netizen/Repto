# REPTO Upgrade — Increment 1: Lead-scoring + kanaal-overschrijdende identiteit

## Context

Het `REPTO_UPGRADE_DOSSIER.md` beschrijft de evolutie van Repto van een WhatsApp-bot
naar een multi-channel lead engine. Het dossier is geschreven als **visiedocument tegen
een standaard n8n-template** (het verwijst naar "Salesforce-nodes" en "Slack-notificatie"
als de bestaande LeadBot — dat is *niet* de echte Repto-app, die op Airtable + Resend +
Meta WhatsApp draait). De `repto-core-lead-engine-vastgoed.json` is een n8n-referentie­flow
voor de vastgoedsector.

**Besliste richting (door eigenaar):**
1. **Bestaande app uitbreiden**, niet pivoteren naar n8n. De FastAPI-kern doet de "engine"
   al robuuster dan n8n zou (Postgres + Airtable-mirror, Clerk multi-tenant, Stripe billing,
   dashboard, sectorprompts, tool-use afspraken, tests). De n8n-JSON dient enkel als
   **referentie** voor de vastgoed-prompt, veldenset en dedup/notify/confirm-flow — hij wordt
   *niet* geïmporteerd.
2. **Eerste increment (dit plan):** warm/lauw/koud lead-scoring + de identiteitsruggengraat
   (één lead-per-persoon). De overige dossier-fases (e-mail/web-kanalen, website-herbouw,
   wekelijks rapport) volgen in latere increments.

**Werkmap:** alle wijzigingen gebeuren in de **`../Repto`** git-repo
(`/Users/kaanaydin/Desktop/Antigravity/Repto`), branch `main` — *niet* in de huidige
"TestprojectAI Agent"-repo. Maak een feature-branch aan voor het werk.

### Waarom deze twee zaken eerst
Het dossier (§3.3) noemt kanaal-overschrijdend geheugen de **kerndifferentiator**, en §3.4
lead-scoring als wat concurrenten missen. Vandaag *is* een lead een `conversations`-rij
gekoppeld aan `wa_contact_phone` + `org_id`; er is geen persoon-entiteit en geen
warm/lauw/koud-score (enkel `urgentie`/`intentie`). Deze increment legt die ruggengraat
zodat latere kanalen (e-mail, webform, webchat) er enkel op hoeven aan te sluiten.

---

## Huidige relevante structuur (gevonden)

- `api/app/models/conversation.py` — modellen. Lead = `Conversation` (PK, `org_id`,
  `wa_contact_phone`, `wa_contact_name`, `status`). Geen persoon/contact-entiteit.
- `api/app/services/whatsapp_service.py` — `get_or_create_conversation()` (regel 42) zoekt/
  maakt een gesprek per (`org_id`, `wa_contact_phone`, status in new/in_progress).
  `sync_to_crm()` (regel 193) triggert na ≥3 berichten.
- `api/app/services/crm_sync_service.py` — `_extract_lead_data()` (Haiku, regel 107) levert
  o.a. `email`, `intentie`, `urgentie`, `gewenste_datum`. `_sync_airtable()` (regel 199)
  upsert via `_airtable_upsert()` met **merge op `Bron ID` = `conversation.id`**.
- `api/setup_airtable.py` — Airtable Leads-tabelschema (kolommen Naam, Telefoon, E-mail,
  Status, Intentie, Urgentie, Samenvatting, …).
- `api/migrations/versions/` — Alembic, laatste revisie `002`. Format zie `002_add_clerk_user_id.py`.
- `api/tests/` — `test_crm_sync_service.py`, `test_whatsapp_service.py`, e.a. (AsyncMock-stijl).

---

## Wijzigingen

### A. Datamodel — `Contact`-entiteit (één lead per persoon)

`api/app/models/conversation.py`:
- Nieuw model **`Contact`** (`__tablename__ = "contacts"`):
  - `id` (str PK), `org_id` (FK→organizations, niet-null)
  - `name` (str, optioneel)
  - `email` (str, optioneel) — **genormaliseerd** opgeslagen (lowercase, trim)
  - `phone` (str, optioneel) — **E.164** genormaliseerd
  - `first_channel` (str) — bv. `"whatsapp"`
  - `channels_json` (Text) — JSON-lijst van kanalen waarlangs deze persoon binnenkwam
  - `score` (str, optioneel) — `"warm" | "lauw" | "koud"`
  - `score_reason` (str, optioneel)
  - `created_at`, `updated_at` (server_default `func.now()`, `onupdate`)
  - relationship `conversations`
- `Conversation` krijgt **`contact_id`** (`Mapped[Optional[str]]`, FK→contacts, nullable) +
  relationship `contact`.

Volg exact de bestaande stijl (SQLAlchemy 2.0 Mapped, géén `from __future__ import annotations`
in dit bestand — zie de waarschuwing bovenaan het model­bestand).

### B. Migratie `003_add_contacts_and_scoring.py`

Nieuwe Alembic-revisie (`revision="003"`, `down_revision="002"`), zelfde format als `002`:
- `create_table("contacts", …)` met de kolommen hierbover + index op `org_id`, `email`, `phone`.
- `add_column("conversations", contact_id)` + index + FK.
- **Backfill** in `upgrade()`: voor elke bestaande conversation één contact aanmaken
  (phone = `wa_contact_phone`, name = `wa_contact_name`, `first_channel="whatsapp"`,
  `channels_json='["whatsapp"]'`), en `conversations.contact_id` zetten. Gebruik
  `op.get_bind()` + kernige SQL/`sa` zoals gangbaar in Alembic data-migraties.
- `downgrade()`: drop kolom + tabel + indexen.

> **Belangrijk — backfill dedupliceert per persoon, niet per gesprek.**
> `get_or_create_conversation` hergebruikt enkel gesprekken met status `new`/`in_progress`
> (whatsapp_service.py:68). Een terugkerende klant op **hetzelfde nummer** krijgt na een
> afgesloten gesprek dus een *nieuwe* `Conversation`-rij — vandaag mappen meerdere
> conversaties al op één persoon. De backfill moet daarom bestaande conversaties
> **groeperen op `(org_id, genormaliseerd telefoonnummer)`**, per groep één `Contact`
> aanmaken en alle `contact_id`'s van die groep eraan koppelen. Eén contact-per-conversation
> zou de één-lead-per-persoon-invariant meteen breken.

### C. Identiteitsservice — `api/app/services/identity_service.py` (nieuw)

- `normalize_email(raw) -> str | None` — lowercase + trim; basisvalidatie (bevat `@`).
- `normalize_phone(raw) -> str | None` — naar één **canonieke sleutel**. Let op: Meta slaat
  `wa_contact_phone` op als **wa_id (internationaal, zónder `+`)**, bv. `32470123456`
  (zie `_normalize_recipient`). De normalisatie moet alle drie deze vormen naar dezelfde
  sleutel reduceren: `32470123456` (wa_id), `+32 470 12 34 56` (E.164 met `+`) en
  `0470 12 34 56` (nationaal). Aanpak: strip spaties/`-`/`()`/`+`, zet leidende `0` om naar
  landcode `32`. Als matching hierop faalt, ontstaan alsnog duplicaten — dit is het hart van
  de differentiator. **Verplichte test:** de drie vormen hierboven resolven naar hetzelfde
  `Contact`.
- `async resolve_contact(db, org_id, *, email=None, phone=None, name=None, channel) -> Contact`:
  1. Normaliseer email + phone.
  2. Zoek binnen `org_id` een bestaand `Contact` waar **email OF phone** matcht (§3.3 dossier).
  3. Match → vul ontbrekende velden aan (name/email/phone), voeg `channel` toe aan
     `channels_json` indien nieuw, return.
  4. Geen match → maak nieuw `Contact` (`first_channel=channel`, `channels_json=[channel]`).
  Hergebruik bestaande patronen (`uuid4`, `select`, `await db.commit()`).
  - **Scope-grens increment 1:** `resolve_contact` is *find-one-or-create*. Het geval waarin
    e-mail contact B matcht terwijl telefoon contact A matchte (= twee bestaande contacten
    samenvoegen: conversaties herkoppelen + `channels_json` samenvoegen) wordt **niet**
    afgehandeld; het kan pas optreden zodra er een e-mailkanaal is. Expliciet uitgesteld naar
    de multi-channel increment.

### D. Inhaken in de WhatsApp-flow

`api/app/services/whatsapp_service.py`, in `get_or_create_conversation()`:
- Na het bepalen van `org` en `conversation`: roep `resolve_contact(db, org.id,
  phone=contact_phone, name=contact_name, channel="whatsapp")` aan en zet
  `conversation.contact_id`. Commit zoals nu.
- (E-mail van de persoon wordt later, tijdens extractie in de sync, op het contact verrijkt —
  zie E.)

### E. Lead-scoring (warm/lauw/koud)

Nieuw, **deterministisch en transparant** (dossier §3.4 vraagt expliciet transparant +
configureerbaar, dus geen extra LLM-call):
- Helper `compute_lead_score(lead: dict) -> tuple[str, str]` (in `identity_service.py` of een
  klein `scoring.py`). Input = de reeds geëxtraheerde velden (`intentie`, `urgentie`,
  `gewenste_datum`, `email`, `naam`). Baseline-regels:
  - **warm**: `intentie ∈ {Offerte, Afspraak}` **én** (`urgentie ∈ {Hoog, Spoed}` **of**
    `gewenste_datum` aanwezig) **én** contact compleet (phone aanwezig — bij WhatsApp altijd).
  - **koud**: vage `intentie ∈ {Info, Anders}` **en** weinig gegevens (geen datum, lage urgentie).
  - **lauw**: al de rest.
  - `score_reason`: één zin die de doorslaggevende factoren benoemt.
  - Sector-overrides later mogelijk via `org` config — nu defaults; laat het uitbreidbaar.
- **CRM-onafhankelijk** (bewuste keuze): scoring en e-mail-verrijking mogen *niet* in
  `_sync_airtable()` hangen, want `sync_to_crm` keert vroeg terug bij `crm_type=="none"`
  (whatsapp_service.py:207) — anders blijft de identiteitsruggengraat inert voor orgs zonder
  Airtable. Daarom: lift `_extract_lead_data` → `compute_lead_score` → contact-verrijking naar
  een stap die in de berichtverwerking draait **vóór/los van** de `crm_type`-branch (bv. een
  `enrich_contact_from_conversation()` in `whatsapp_service` of een kleine
  `lead_enrichment_service`, na ≥3 berichten net als de sync-drempel). Concreet:
  1. Extraheer leaddata (hergebruik `_extract_lead_data`; verplaats het desnoods naar een
     module die beide paden delen).
  2. Verrijk het gekoppelde `Contact` met de geëxtraheerde `email` (genormaliseerd) — zodat
     e-mail-matching klaar is voor toekomstige kanalen.
  3. Bereken `score, reason = compute_lead_score(lead)` en sla op het `Contact` op.
- `_sync_airtable()` **leest** vervolgens enkel het reeds bepaalde resultaat van het `Contact`
  en voegt toe aan `lead_fields`: `"Score": contact.score`, `"Score Reden": contact.score_reason`.

### F. Airtable-schema + merge-key (conflict expliciet gemaakt)

- `api/setup_airtable.py`: voeg in de Leads-tabel twee velden toe: **`Score`** (single select:
  Warm/Lauw/Koud) en **`Score Reden`** (long text). `typecast=True` in de upsert maakt
  ontbrekende select-opties automatisch aan, dus bestaande bases breken niet.
- **Merge-key blijft deze increment `Bron ID` = `conversation.id`.** Reden: elk gesprek werd
  al een eigen Airtable-record met die sleutel; ongewijzigd laten betekent géén regressie en
  de live-records blijven intact. (De nieuwe `contacts`-tabel dedupliceert wél per persoon —
  zie B.) Het omzetten van de Airtable-Lead-sleutel naar
  `contact.id` (met eenmalige backfill om duplicaten te vermijden) is **bewust uitgesteld**
  naar de multi-channel increment, wanneer één persoon via meerdere kanalen/gesprekken
  binnenkomt. Dit staat zo in het Beslissingenlog van het dossier genoteerd.

### G. Notificatie verrijken (de payoff van scoring)

Het dossier wil de score in de klantnotificatie "zodat die weet wie eerst te bellen". Voeg
`score` + `score_reason` toe aan de bestaande agency-notificatie die bij gesprek-afronding
vertrekt (`api/app/services/email_service.py`, getriggerd vanuit `webhooks.py` bij
`[GESPREK_AFGEROND]`). Klein, hoge waarde, sluit de increment af als verticale slice.

---

## Bestanden (overzicht)

| Bestand | Wijziging |
|---|---|
| `api/app/models/conversation.py` | `Contact`-model + `Conversation.contact_id` |
| `api/migrations/versions/003_add_contacts_and_scoring.py` | nieuw — tabel + kolom + backfill |
| `api/app/services/identity_service.py` | nieuw — normalisatie + `resolve_contact` + scoring |
| `api/app/services/whatsapp_service.py` | contact resolven in `get_or_create_conversation` |
| `api/app/services/crm_sync_service.py` | contact-verrijking + score berekenen + Airtable-velden |
| `api/setup_airtable.py` | Leads-velden `Score` + `Score Reden` |
| `api/app/services/email_service.py` | score in agency-notificatie |
| `api/tests/test_identity_service.py` | nieuw — normalisatie + resolve (match e-mail/phone/none) |
| `api/tests/test_crm_sync_service.py` | assert `Score`/`Score Reden` in lead_fields |

---

## Verificatie (Definition of Done — dossier Fase 1)

1. **Migratie draait schoon**: `cd api && alembic upgrade head` op een dev-DB; controleer dat
   `contacts` bestaat, `conversations.contact_id` gevuld is voor bestaande rijen (backfill),
   en `alembic downgrade -1` weer netjes terugdraait.
2. **Unit-tests groen**: `cd api && pytest` — nieuwe `test_identity_service.py`
   (e-mail-match, phone-match, géén-match→create, normalisatie-edgecases) en de uitgebreide
   `test_crm_sync_service.py` slagen. **Verplichte canonicalisatie-test:** `32470123456`
   (wa_id), `+32 470 12 34 56` en `0470 12 34 56` resolven naar hetzelfde `Contact`.
3. **Identiteit end-to-end**: simuleer twee gesprekken van hetzelfde nummer (bv. één
   afgesloten + één nieuw) → **één** `Contact`, beide `Conversation`s gekoppeld via
   `contact_id`. Een ander nummer maar later hetzelfde e-mailadres (gezet via extractie)
   matcht op e-mail i.p.v. een duplicaat te maken.
4. **Scoring is CRM-onafhankelijk**: bevestig dat `Contact.score ∈ {warm,lauw,koud}` +
   `score_reason` gezet wordt óók voor een org met `crm_type="none"` (niet enkel de
   Airtable-seed-org). Voor een Airtable-org: bevestig dat de upsert `Score`/`Score Reden`
   meestuurt (via gemockte httpx zoals in de bestaande sync-tests).
5. **Geen hardcoded secrets** (dossier-regel): alle sleutels blijven uit
   `crm_credentials_encrypted` / env komen; niets nieuws hardgecodeerd.
6. **Stop voor sign-off**: na deze increment pauzeren zodat de DoD afgetekend kan worden vóór
   de volgende fase (e-mail/web-kanalen), conform de werkwijze van het dossier.
