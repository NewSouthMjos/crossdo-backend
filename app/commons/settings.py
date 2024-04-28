from enum import StrEnum, unique
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


@unique
class EnvironmentEnum(StrEnum):
    development = "development"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    APP_ENV: EnvironmentEnum = EnvironmentEnum.development
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str | list[str] = [""]
    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SECRET_KEY: str


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print("FAULT WHILE LOADING ENVS:")
        raise e
