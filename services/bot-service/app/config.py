from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    service_name: str = "bot-service"
    version: str = "0.1.0"

    # Telegram
    telegram_bot_token: str = ""
    # "webhook" or "polling" – polling is simpler for dev, webhook for prod
    bot_mode: str = "polling"
    webhook_base_url: str = ""          # e.g. https://yourdomain.com
    webhook_path: str = "/bot/webhook"  # registered in Telegram

    # Internal token for calling other services
    internal_token: str = "change_me_internal_token"

    # Downstream service URLs
    auth_service_url: str = "http://auth-service:8001"
    profile_service_url: str = "http://profile-service:8002"
    vacancy_service_url: str = "http://vacancy-service:8004"
    recommendation_service_url: str = "http://recommendation-service:8005"
    assessment_service_url: str = "http://assessment-service:8007"
    notification_service_url: str = "http://notification-service:8008"

    # Redis for FSM storage (aiogram MemoryStorage works without Redis)
    redis_url: str = ""

    # FastAPI health-check port
    port: int = 8009

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = BotSettings()
