from pydantic_settings import BaseSettings, SettingsConfigDict


class RecSettings(BaseSettings):
    service_name: str = "recommendation-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"

    # Downstream service URLs
    profile_service_url: str = "http://profile-service:8002"
    vacancy_service_url: str = "http://vacancy-service:8004"
    ml_service_url: str = "http://ml-service:8006"

    # Token used to call ml-service internal endpoints
    internal_token: str = "change_me_internal_token"

    # How many vacancy candidates to fetch before scoring
    vacancy_fetch_limit: int = 300
    # Store top-N recommendations per session
    top_n_store: int = 50

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = RecSettings()
