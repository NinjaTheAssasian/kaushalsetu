from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KaushalSetu API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-pro-preview"
    secret_key: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
