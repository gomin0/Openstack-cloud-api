from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Envs(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_host: str
    database_port: str
    database_username: str
    database_password: str


@lru_cache
def get_envs() -> Envs:
    return Envs()
