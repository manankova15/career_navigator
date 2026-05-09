from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    service_name: str = "ml-service"
    version: str = "0.2.0"

    # Content-based scoring weights, derived from the Analytic Hierarchy Process
    # (method of pairwise comparisons, Saaty 1980). Reproduction steps:
    #  1. Build 6x6 pairwise matrix A with a_ij ∈ {1,3,5,7,9, 1/3,1/5,1/7,1/9}
    #     encoding the relative importance of criterion i over criterion j.
    #  2. w_i = Σ_j (a_ij / Σ_k a_kj) / n — averaged-column-normalisation priorities.
    #  3. Consistency: λ_max ≈ 6.27, CI ≈ 0.053, CR ≈ 0.043 < 0.10 — consistent.
    # The resulting weights below sum to 1.0 (rounded to 2 decimals).
    weight_skills: float = 0.46
    weight_role: float = 0.24
    weight_seniority: float = 0.11
    weight_salary: float = 0.11
    weight_location: float = 0.05
    weight_format: float = 0.03

    max_candidates: int = 500
    top_n: int = 50
    skill_gap_top_n: int = 20

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = MLSettings()
