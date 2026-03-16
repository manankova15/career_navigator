from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    service_name: str = "ml-service"
    version: str = "0.1.0"

    # Phase 1 scoring weights (must sum to 1.0)
    weight_skills: float = 0.50
    weight_location: float = 0.20
    weight_salary: float = 0.15
    weight_seniority: float = 0.15

    # Recommendation limits
    max_candidates: int = 500    # max vacancies to score per request
    top_n: int = 50              # top results to return
    skill_gap_top_n: int = 20    # top missing skills to surface

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = MLSettings()
