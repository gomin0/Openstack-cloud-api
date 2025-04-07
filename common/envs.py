from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Envs(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str


@lru_cache
def get_envs() -> Envs:
    return Envs()
