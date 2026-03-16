from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    version: str = "0.1.0"

    auth_service_url: str = "http://auth-service:8001"
    profile_service_url: str = "http://profile-service:8002"
    source_service_url: str = "http://source-service:8003"
    vacancy_service_url: str = "http://vacancy-service:8004"
    recommendation_service_url: str = "http://recommendation-service:8005"
    ml_service_url: str = "http://ml-service:8006"
    assessment_service_url: str = "http://assessment-service:8007"
    notification_service_url: str = "http://notification-service:8008"
    analytics_service_url: str = "http://analytics-service:8011"
    admin_service_url: str = "http://admin-service:8010"

    # Rate limiting: max requests per window per client key
    rate_limit_requests: int = 600
    rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = GatewaySettings()
