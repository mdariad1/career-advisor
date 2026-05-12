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
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    classifier_path: str = "models/svm_classifier.joblib"


settings = Settings()
