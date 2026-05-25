from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Repto API"
    environment: str = "development"
    debug: bool = True

    # Database (Supabase PostgreSQL)
    database_url: str

    # Twilio WhatsApp
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_from: str  # bijv. "whatsapp:+14155238886"

    # Webhook verificatie token (zelf kiezen, zelfde in .env + Twilio dashboard)
    whatsapp_verify_token: str = "repto_webhook_2026"

    # AI (Anthropic)
    anthropic_api_key: str

    # Auth (Clerk) — optioneel fase 2
    clerk_secret_key: Optional[str] = None
    clerk_publishable_key: Optional[str] = None

    # Stripe — optioneel fase 2
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Email (Resend) — optioneel fase 2
    resend_api_key: Optional[str] = None
    notification_email: Optional[str] = None     # E-mailadres voor lead-notificaties
    notification_from: str = "Repto <noreply@repto.be>"  # Afzender (na domeinverificatie in Resend)

    # Google Sheets — service account (compact JSON string)
    google_sheets_credentials_b64: Optional[str] = None  # legacy
    google_sheets_credentials_json: Optional[str] = None

    # Google (Calendar OAuth) — optioneel fase 2
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Frontend URL (voor CORS)
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
