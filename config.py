import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "password"
    DB_NAME: str = "mydb"

    DEBUG: bool = True
    SECRET_KEY: str = "dev"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    API_VERSION: str = "v1"
    MAX_PAGE_SIZE: int = 1000
    DEFAULT_PAGE_SIZE: int = 20

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def database_url_psycopg2(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


class DevConfig(BaseConfig):
    DEBUG: bool = True
    SECRET_KEY: str = "dev"
    LOG_LEVEL: str = "DEBUG"


class ProdConfig(BaseConfig):
    DEBUG: bool = False
    SECRET_KEY: str = "super-secret-prod"
    LOG_LEVEL: str = "WARNING"


class TestConfig(BaseConfig):
    DB_NAME: str = "test_db"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


def get_config():
    env = os.getenv("ENVIRONMENT", "dev")
    if env == "prod":
        return ProdConfig()
    elif env == "test":
        return TestConfig()
    return DevConfig()


settings = get_config()
