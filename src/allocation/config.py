import os
from typing import Dict


class Config:
    DB_PATH: str
    SQLA_CONNECTION_STRING: str
    DB_TYPE = os.getenv("DB_TYPE") or "SQLITE"
    REDIS_HOST = os.getenv("REDIS_HOST") or "localhost"
    REDIS_PORT = os.getenv("REDIS_PORT") or 6379
    REDIS_DB = os.getenv("REDIS_DB") or 0
    SWAGGER = {"title": os.getenv("SWAGGER_TITLE") or "Allocation Service"}


class DevelopmentConfig(Config):
    DB_PATH = os.getenv("DB_PATH") or "dev.db"
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}" + DB_CONNECTION_SETTINGS


class TestingConfig(Config):
    DB_TYPE = os.getenv("DB_TYPE") or "MEMORY"
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False&cache=shared"
    SQLA_CONNECTION_STRING = "sqlite:///:memory:" + DB_CONNECTION_SETTINGS


class ProductionConfig(Config):
    DB_PATH = os.getenv("DB_PATH") or "prod.db"
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}" + DB_CONNECTION_SETTINGS
    REDIS_HOST = os.getenv("REDIS_HOST") or "redis"


config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name=None) -> Config:
    if not config_name:
        config_name = os.environ.get("ENV") or "default"
    return config[config_name]


def get_redis_config() -> Dict:
    c = get_config()
    return {"host": c.REDIS_HOST, "port": c.REDIS_PORT, "db": c.REDIS_DB}
