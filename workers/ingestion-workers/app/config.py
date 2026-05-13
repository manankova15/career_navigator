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
    # HH требует валидный User-Agent с реальным контактом, иначе отдаёт 403.
    hh_user_agent: str = "career-navigator-thesis/1.0 (manankova-15@mail.ru)"
    # OAuth для публичного API HH.ru. С весны 2025 анонимные запросы к /vacancies
    # отбиваются 403 {"errors":[{"type":"forbidden"}]}, поэтому шлём Bearer-token.
    # Если задан client_id/secret, при 403 воркер сам перевыпустит токен
    # (grant_type=client_credentials).
    hh_client_id: str = ""
    hh_client_secret: str = ""
    hh_auth_token: str = ""

    fetch_pages_per_run: int = 5       # max pages to fetch per source run
    dedup_similarity_threshold: float = 0.85

    # Синхронизация по запросу админа (если в теле запроса не передан max_vacancies)
    sync_default_max_vacancies: int = 200
    sync_max_vacancies_cap: int = 5000

    # Telegram (Telethon) — нужны для source_type=telegram
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    telegram_session_file: str = "/app/.tg_session"
    telegram_batch_size: int = 100
    telegram_request_delay_seconds: float = 1.5

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = WorkerSettings()
