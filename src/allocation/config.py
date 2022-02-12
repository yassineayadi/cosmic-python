import os
from typing import Dict


class Config:
    DB_TYPE = os.getenv("DB_TYPE") or "SQLITE"
    SQLITE_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    SQLA_CONNECTION_STRING: str
    REDIS_HOST = os.getenv("REDIS_HOST") or "localhost"
    REDIS_PORT = os.getenv("REDIS_PORT") or 6379
    REDIS_DB = os.getenv("REDIS_DB") or 0
    SWAGGER = {"title": os.getenv("SWAGGER_TITLE") or "Allocation Service"}


class DevelopmentConfig(Config):
    SQLA_CONNECTION_STRING = f"sqlite:///dev.db" + Config.SQLITE_CONNECTION_SETTINGS


class TestingConfig(Config):
    DB_TYPE = os.getenv("DB_TYPE") or "MEMORY"
    SQLITE_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False&cache=shared"
    SQLA_CONNECTION_STRING = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or "sqlite:///:memory:" + SQLITE_CONNECTION_SETTINGS
    )


class ProductionConfig(Config):
    SQLA_CONNECTION_STRING = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or f"sqlite:///prod.db" + Config.SQLITE_CONNECTION_SETTINGS
    )
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
