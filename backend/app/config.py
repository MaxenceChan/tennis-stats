from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tennis.db"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    user_agent: str = "tennis-stats-bot/0.1 (contact@example.com)"
    scrape_delay_sec: float = 2.0
    scrape_timeout_sec: float = 20.0
    scrape_max_retries: int = 3

    enable_scheduler: bool = False
    rankings_cron: str = "0 6 * * *"
    matches_cron: str = "30 6 * * *"

    admin_token: str = ""  # vide = endpoints admin ouverts (dev). Définir en prod.

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
