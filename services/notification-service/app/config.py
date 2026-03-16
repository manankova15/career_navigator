from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    service_name: str = "notification-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"

    # Token accepted from internal services (assessment, recommendation, etc.)
    internal_token: str = "change_me_internal_token"

    # ── SMTP (email channel) ──────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Career Navigator"
    smtp_from_address: str = "no-reply@career-navigator.local"
    smtp_use_tls: bool = True

    # ── Telegram (telegram channel) ───────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_api_base: str = "https://api.telegram.org"

    # Maximum delivery attempts before marking notification as failed
    max_delivery_attempts: int = 3

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = NotificationSettings()
