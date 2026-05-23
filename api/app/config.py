from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Repto API"
    environment: str = "development"
    debug: bool = True

    # Database (Supabase PostgreSQL)
    database_url: str

    # WhatsApp (Meta Cloud API)
    whatsapp_verify_token: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: str

    # AI (Anthropic)
    anthropic_api_key: str

    # Auth (Clerk)
    clerk_secret_key: str
    clerk_publishable_key: str

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str

    # Email (Resend)
    resend_api_key: str

    # Google (Sheets + Calendar)
    google_client_id: str
    google_client_secret: str

    # Frontend URL (voor CORS)
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
