from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import get_settings
from app.routers import webhooks, conversations, organizations, appointments

settings = get_settings()


# ─── APScheduler lifespan ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop APScheduler samen met de FastAPI app."""
    from app.services.reminder_service import send_appointment_reminders

    scheduler = AsyncIOScheduler(timezone="Europe/Brussels")
    # Elke 60 minuten controleren op aankomende afspraken
    scheduler.add_job(
        send_appointment_reminders,
        trigger="interval",
        minutes=60,
        id="appointment_reminders",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Repto API",
    description="AI-receptionist voor KMO's — WhatsApp automatisering",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS — laat het Next.js dashboard toe
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(webhooks.router)
app.include_router(conversations.router)
app.include_router(organizations.router)
app.include_router(appointments.router)


@app.get("/")
async def health_check():
    return {"status": "ok", "app": "Repto API", "version": "0.2.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
