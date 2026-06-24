from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongo_uri: str = (
        "mongodb://test1:mama2001@"
        "ac-tbf2wa3-shard-00-00.mqaoycq.mongodb.net:27017,"
        "ac-tbf2wa3-shard-00-01.mqaoycq.mongodb.net:27017,"
        "ac-tbf2wa3-shard-00-02.mqaoycq.mongodb.net:27017"
        "/career_db?authSource=admin&replicaSet=atlas-cel82u-shard-0&tls=true"
    )
    nlp_service_url: str = "http://nlp_service:8001"
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    sync_interval_hours: int = 6
    # Comma-separated lowercase Adzuna country codes, e.g. "gb,us,ro,de"
    # Adzuna free tier: 250 req/day. Each country × 8 careers = up to 40 req/cycle.
    target_countries: str = "gb"
    # 1 s gap between requests keeps well within the free-tier rate limit
    inter_query_delay_seconds: float = 1.0
    job_stale_days: int = 14


settings = Settings()
