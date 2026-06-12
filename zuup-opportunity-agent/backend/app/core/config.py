"""
Zuup Opportunity Agent — Core Configuration
Loads all settings from environment variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    app_env: str = "development"
    app_name: str = "zuup-opportunity-agent"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql://zuup_user:zuup_pass@localhost:5432/zuup_db"

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── AWS ──────────────────────────────────────────────────
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""
    s3_resume_prefix: str = "resumes/"

    # ── AI / LLM ─────────────────────────────────────────────
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # ── Auth ─────────────────────────────────────────────────
    jwt_secret_key: str = "zuup-super-secret-dev-key-change-in-production-12345"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # ── Email ────────────────────────────────────────────────
    sendgrid_api_key: str = ""
    from_email: str = "noreply@zuup.io"
    from_name: str = "Zuup"

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_authenticated: int = 100
    rate_limit_unauthenticated: int = 10
    rate_limit_window_seconds: int = 60

    # ── Matching Engine ──────────────────────────────────────
    min_match_score: int = 30
    recency_bonus_hours: int = 48
    recency_bonus_points: int = 10
    skill_match_bonus: int = 5
    skill_match_max_bonus: int = 20
    location_match_bonus: int = 5
    dedup_cosine_threshold: float = 0.92

    # ── Ingestion ────────────────────────────────────────────
    ingestion_min_description_words: int = 50
    ingestion_hackathon_interval_hours: int = 4
    ingestion_scholarship_interval_hours: int = 24
    ingestion_internship_interval_hours: int = 6
    ingestion_exchange_interval_hours: int = 168

    # ── Scraper ──────────────────────────────────────────────
    scraper_proxy_url: str = ""
    scraper_user_agent: str = "ZuupBot/1.0 (+https://zuup.io/bot)"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
