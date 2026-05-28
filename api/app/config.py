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

    # WhatsApp — Meta Cloud API (https://developers.facebook.com/docs/whatsapp/cloud-api)
    whatsapp_access_token: str                       # System-user token (agency-WABA, stuurt namens alle nummers)
    whatsapp_phone_number_id: str                    # Default afzender; per-org override via Organization.whatsapp_phone_number_id
    whatsapp_api_version: str = "v22.0"              # Graph API versie
    whatsapp_app_secret: Optional[str] = None        # Optioneel: voor X-Hub-Signature-256 webhook-verificatie

    # Webhook verificatie token (zelf kiezen, zelfde in .env + Meta App-dashboard)
    whatsapp_verify_token: str = "repto_webhook_2026"

    # Naam van de goedgekeurde Meta message-template voor afspraakherinneringen
    whatsapp_reminder_template: str = "appointment_reminder"
    whatsapp_reminder_template_lang: str = "nl"

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
        extra = "ignore"  # onbekende/oude env-vars (bv. legacy TWILIO_*) negeren


@lru_cache()
def get_settings() -> Settings:
    return Settings()
