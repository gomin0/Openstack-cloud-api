from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Envs(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str

    CLOUD_ADMIN_OPENSTACK_ID: str
    CLOUD_ADMIN_PASSWORD: str
    CLOUD_ADMIN_DEFAULT_PROJECT_OPENSTACK_ID: str

    DEFAULT_DOMAIN_ID: int
    DEFAULT_DOMAIN_OPENSTACK_ID: str
    DEFAULT_ROLE_OPENSTACK_ID: str

    JWT_SECRET: str
    ACCESS_TOKEN_DURATION_MINUTES: int

    MAX_SYNC_ATTEMPTS_FOR_VOLUME_CREATION: int
    SYNC_INTERVAL_SECONDS_FOR_VOLUME_CREATION: int

    OPENSTACK_SERVER_URL: str
    KEYSTONE_PORT: int
    NEUTRON_PORT: int
    CINDER_PORT: int
    NEUTRON_PORT: int


@lru_cache
def get_envs() -> Envs:
    return Envs()
