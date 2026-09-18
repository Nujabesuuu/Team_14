from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api — defaults resolve against the package root, not the shell's cwd,
# so `uvicorn --app-dir apps/api` from the repo root and `python -m app.seed`
# from apps/api both hit the same SQLite file and media folder.
API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration, read from environment / .env."""

    model_config = SettingsConfigDict(env_file=API_ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{API_ROOT / 'teamate.db'}"
    jwt_secret: str = "dev-secret-do-not-use-in-prod"
    jwt_expires_days: int = 7
    media_dir: str = str(API_ROOT / "media")
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,capacitor://localhost"
    free_daily_swipes: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
