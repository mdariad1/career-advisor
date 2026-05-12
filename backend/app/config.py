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
    jwt_secret: str = "dev-secret"
    jwt_refresh_secret: str = "dev-refresh-secret"
    nlp_service_url: str = "http://nlp_service:8001"
    jobdatapool_api_key: str = ""
    sync_interval_hours: int = 6
    target_country_code: str = "GB"

    # JWT config
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


settings = Settings()
