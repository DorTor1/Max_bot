from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_mode: str = Field(default="polling", alias="BOT_MODE")

    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")
    webhook_path: str = Field(default="/max/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str | None = Field(default=None, alias="WEBHOOK_SECRET")
    webhook_public_url: str | None = Field(default=None, alias="WEBHOOK_PUBLIC_URL")

    database_url: str = Field(
        default="postgresql+psycopg2://passbot:passbot@localhost:5433/passbot",
        alias="DATABASE_URL",
    )

    consent_version: str = Field(default="2026-05-1", alias="CONSENT_VERSION")
    tech_admin_max_ids: str = Field(default="", alias="TECH_ADMIN_MAX_IDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def tech_admin_ids(self) -> list[str]:
        if not self.tech_admin_max_ids.strip():
            return []
        return [x.strip() for x in self.tech_admin_max_ids.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
