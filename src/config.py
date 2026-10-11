from datetime import time

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    database_url: str = "postgresql+asyncpg://devops:devops@db:5432/devops_quest"

    default_timezone: str = "Asia/Tashkent"
    default_reminder_time: time = time(9, 0)
    default_nudge_time: time = time(21, 0)

    penalty_threshold: int = 3      # ketma-ket o'tkazilgan kun >= 3 -> quiz jarima
    hardcore_threshold: int = 5     # >= 5 -> hardcore jarima
    rest_weekday: int = 6           # 6 = Yakshanba (streak buzilmaydi)

    admin_ids: list[int] = []

    @field_validator("default_reminder_time", "default_nudge_time", mode="before")
    @classmethod
    def _parse_hm(cls, v):
        if isinstance(v, str):
            h, m = v.split(":")
            return time(int(h), int(m))
        return v


settings = Settings()  # type: ignore[call-arg]
