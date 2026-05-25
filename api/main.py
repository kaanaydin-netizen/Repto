from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import webhooks, conversations, organizations, appointments

settings = get_settings()

app = FastAPI(
    title="Repto API",
    description="AI-receptionist voor KMO's — WhatsApp automatisering",
    version="0.1.0",
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
    return {"status": "ok", "app": "Repto API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
