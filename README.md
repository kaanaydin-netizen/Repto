# 🤖 Repto — AI-Receptionist voor KMO's

> **Nooit meer een lead missen. Altijd snel antwoorden. Jij focust op het werk, wij regelen de opvolging.**

Repto is een SaaS webapp die als digitale AI-receptionist werkt voor KMO's (installateurs, vastgoed, garages, boekhouders, bouwbedrijven, freelancers). Via WhatsApp beantwoordt Repto automatisch inkomende berichten, plant afspraken in, stuurt herinneringen en synchroniseert leads met bestaande CRM's (HubSpot, Pipedrive, Google Sheets).

---

## 🏗️ Architectuur

```
repto/
├── web/          Next.js 14 (App Router) + Tailwind CSS  →  Vercel
├── api/          FastAPI (Python 3.11+)                  →  Railway
├── .env.example  Alle benodigde omgevingsvariabelen
└── docker-compose.yml  Lokale development setup
```

## 🚀 Snel starten (lokale ontwikkeling)

### Vereisten
- Node.js 20+
- Python 3.11+
- Docker (optioneel, voor de lokale database)

### 1. Omgevingsvariabelen instellen

```bash
cp .env.example .env
# Vul de waarden in .env aan (zie opmerkingen per variabele)
```

### 2. Backend starten (FastAPI)

```bash
cd api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# API draait op http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### 3. Frontend starten (Next.js)

```bash
cd web
npm install
npm run dev
# Dashboard draait op http://localhost:3000
```

### 4. Alles tegelijk via Docker

```bash
docker-compose up
```

---

## 📦 Tech Stack

| Laag | Technologie |
|------|-------------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL via Supabase (EU region) |
| Auth | Clerk |
| AI | Anthropic Claude (claude-sonnet-4-6) met prompt caching |
| WhatsApp | Meta Cloud API |
| CRM sync | Google Sheets (MVP) · HubSpot (fase 2) · Pipedrive (fase 2) |
| Betalingen | Stripe |
| E-mail | Resend |
| Hosting | Vercel (web) + Railway (api) |

---

## 🔑 Benodigde API-keys

| Dienst | Waar aanvragen |
|--------|----------------|
| Meta WhatsApp Cloud API | [developers.facebook.com](https://developers.facebook.com/docs/whatsapp/cloud-api) |
| Anthropic Claude | [console.anthropic.com](https://console.anthropic.com) |
| Supabase | [supabase.com](https://supabase.com) → EU region |
| Clerk | [dashboard.clerk.com](https://dashboard.clerk.com) |
| Stripe | [dashboard.stripe.com](https://dashboard.stripe.com) |
| Resend | [resend.com](https://resend.com) |
| Google Cloud (Sheets + Calendar) | [console.cloud.google.com](https://console.cloud.google.com) |

---

## 📋 MVP Scope (Fase 1)

- [x] Project setup
- [ ] WhatsApp webhook ontvangen
- [ ] Claude AI-antwoord genereren + versturen
- [ ] Google Sheets lead-sync
- [ ] Google Calendar afspraken inplannen
- [ ] Herinneringen (24u voor afspraak)
- [ ] Next.js dashboard (gesprekken + statussen)
- [ ] Stripe abonnementen
- [ ] Onboarding flow

---

## 📄 Product Dossier

Zie [`../TestprojectAI Agent/PRODUCT_DOSSIER.md`](../TestprojectAI%20Agent/PRODUCT_DOSSIER.md) voor het volledige product dossier (business case, architectuur, roadmap, business model).

---

*Versie 0.1.0 — In ontwikkeling*
