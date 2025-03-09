from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    API_VERSION: str
    COHERE_API_KEY: str
    GCP_SERVICE_ACCOUNT: str
    OPENAI_API_KEY: str


settings = Settings()
