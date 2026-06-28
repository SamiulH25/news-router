from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = (_BACKEND_ROOT / "data" / "news_router.db").as_posix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{_DEFAULT_DB}"
    secret_key: str = "change-me-in-production-use-openssl-rand"
    access_token_expire_minutes: int = 60 * 24 * 7
    cookie_name: str = "news_router_token"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    feed_poll_interval_minutes: int = 45
    feed_window_hours: int = 12
    feed_poll_concurrency: int = 8

    digest_morning_hour: int = 7
    digest_morning_minute: int = 0
    digest_evening_hour: int = 19
    digest_evening_minute: int = 0

    ntfy_base_url: str = "http://127.0.0.1:2586"
    app_base_url: str = "http://localhost:5173"
    allow_registration: bool = True

    @property
    def digest_schedule(self) -> list[tuple[int, int]]:
        return [
            (self.digest_morning_hour, self.digest_morning_minute),
            (self.digest_evening_hour, self.digest_evening_minute),
        ]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
