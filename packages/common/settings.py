from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    service_name: str = "career-service"
    environment: str = "development"
    version: str = "0.1.0"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
