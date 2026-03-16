from fastapi import FastAPI

from packages.common.api import build_meta_router

app = FastAPI(title="ingestion-workers", version="0.1.0")
app.include_router(build_meta_router("ingestion-workers"))


@app.get("/jobs", tags=["ingestion"])
async def jobs() -> dict[str, list[str]]:
    return {
        "pipelines": [
            "fetch_raw_payload",
            "normalize_vacancy",
            "extract_skills",
            "deduplicate",
            "archive_expired",
            "emit_catalog_updated",
        ]
    }


@app.get("/deduplication-rules", tags=["ingestion"])
async def deduplication_rules() -> dict[str, list[str]]:
    return {
        "rules": [
            "external_id_match",
            "canonical_url_match",
            "title_company_similarity",
            "fingerprint_similarity",
        ]
    }
