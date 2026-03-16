from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    redis_url: str = "redis://redis:6379/0"

    vacancy_service_url: str = "http://vacancy-service:8004"
    source_service_url: str = "http://source-service:8003"

    # Internal service JWT (admin role) for calling internal endpoints
    internal_jwt_secret: str = "change_me_to_a_long_random_secret"
    internal_jwt_algorithm: str = "HS256"

    hh_api_base: str = "https://api.hh.ru"
    hh_user_agent: str = "CareerNavigator/1.0 (career.navigator@example.com)"

    fetch_pages_per_run: int = 5       # max pages to fetch per source run
    dedup_similarity_threshold: float = 0.85

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = WorkerSettings()
