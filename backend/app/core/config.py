from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "CareerPilot AI"
    app_env: str = "development"
    debug: bool = False

    database_url: str
    redis_url: str
    frontend_url: str = "http://localhost:3000"
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    # Optional assistant only. Core intelligence has no provider dependency.
    assistant_provider: str = "none"
    assistant_api_key: SecretStr = SecretStr("")
    assistant_base_url: str = ""
    assistant_model: str = ""
    assistant_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
