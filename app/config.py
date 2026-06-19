from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    TESTING: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # ищет .env в корне проекта
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # игнорирует лишние переменные в .env
    )

#Кэширует настройки — не читает .env при каждом импорте
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = Settings()