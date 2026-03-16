from pydantic_settings import BaseSettings, SettingsConfigDict


class AssessmentSettings(BaseSettings):
    service_name: str = "assessment-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"

    # Max attempts a user may have per assessment (0 = unlimited)
    max_attempts_per_assessment: int = 0

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = AssessmentSettings()
