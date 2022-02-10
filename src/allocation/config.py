import os
from pathlib import Path
from typing import Dict

CURRENT_DIRECTORY = Path(__file__).parent


class Config:
    DB_PATH: str
    DB_URI: str
    SQLA_CONNECTION_STRING: str
    DB_TYPE: str
    REDIS_HOST = os.getenv("REDIS_HOST") or "localhost"
    REDIS_PORT = os.getenv("REDIS_PORT") or 6379
    REDIS_DB = os.getenv("REDIS_DB") or 0
    SWAGGER = {"title": "Allocation Service"}


class DevelopmentConfig(Config):
    DB_PATH = os.getenv("DB_PATH") or "dev.db"
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    DB_URI = f"file:{DB_PATH}" + DB_CONNECTION_SETTINGS
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}" + DB_CONNECTION_SETTINGS
    DB_TYPE = os.getenv("DB_TYPE") or "SQlite3"


class TestingConfig(Config):
    DB_PATH = CURRENT_DIRECTORY
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False&cache=shared"
    DB_URI = ""
    SQLA_CONNECTION_STRING = "sqlite:///:memory:" + DB_CONNECTION_SETTINGS
    DB_TYPE = os.getenv("DB_TYPE") or "MEMORY"


class ProductionConfig(Config):
    DB_PATH = os.getenv("DB_PATH") or "prod.db"
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    DB_URI = f"file:{DB_PATH}" + DB_CONNECTION_SETTINGS
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}" + DB_CONNECTION_SETTINGS
    DB_TYPE = "SQlite3"
    REDIS_HOST = os.getenv("REDIS_HOST") or "redis"
    REDIS_PORT = os.getenv("REDIS_PORT") or 6379
    REDIS_DB = os.getenv("REDIS_DB") or 0


config = {
    "development": DevelopmentConfig,
    "default": ProductionConfig,
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
