from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    service_name: str = "auth-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 14

    # SMTP (used for password reset emails). Aliased via env_prefix="" so values
    # come from SMTP_HOST/SMTP_PORT/SMTP_USERNAME/SMTP_PASSWORD (see .env).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Career Navigator"
    smtp_from_address: str = ""
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = AuthSettings()
