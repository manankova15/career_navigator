from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    service_name: str = "admin-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"
    internal_token: str = "change_me_internal_token"

    # Downstream service URLs
    auth_service_url: str = "http://auth-service:8001"
    profile_service_url: str = "http://profile-service:8002"
    source_service_url: str = "http://source-service:8003"
    vacancy_service_url: str = "http://vacancy-service:8004"
    assessment_service_url: str = "http://assessment-service:8007"
    notification_service_url: str = "http://notification-service:8008"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = AdminSettings()
