from pydantic_settings import BaseSettings, SettingsConfigDict


class ProfileSettings(BaseSettings):
    service_name: str = "profile-service"
    version: str = "0.1.0"

    database_url: str = "postgresql://career_navigator:change_me@postgres:5432/career_navigator"
    jwt_secret: str = "change_me_to_a_long_random_secret"
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = ProfileSettings()
