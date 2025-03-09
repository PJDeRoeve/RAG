from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env"
    )
    PUBSUB_SERVICE_ACC: str
    GCP_PROJECT_ID: str
    GCP_SERVICE_ACCOUNT: str

settings = Settings()  # type: ignore
