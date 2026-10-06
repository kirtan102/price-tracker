from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./tracker.db"
    jwt_secret: str = "dev-only-change-me"
    jwt_access_minutes: int = 15
    refresh_days: int = 30
    admin_username: str = "admin"
    admin_password: str = "change-me"
    check_interval_minutes: int = 60
    max_failures: int = 5
    keepa_api_key: str | None = None
    flipkart_provider: str = "mock"
    flipkart_api_url: str | None = None
    flipkart_api_key: str | None = None
    firebase_credentials_json: str | None = None
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

settings = Settings()

