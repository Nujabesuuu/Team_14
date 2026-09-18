from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./teamate.db"
    jwt_secret: str = "dev-secret-do-not-use-in-prod"
    jwt_expires_days: int = 7
    media_dir: str = "./media"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,capacitor://localhost"
    free_daily_swipes: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
