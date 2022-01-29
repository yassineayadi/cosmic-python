import os
from pathlib import Path
from typing import Dict

CURRENT_DIRECTORY = Path(__file__).parent


class Config:
    DB_PATH: Path
    DB_URI: str
    SQLA_CONNECTION_STRING: str
    DB_TYPE: str
    REDIS_CONFIG = {"host": "localhost", "port": 6379, "db": 0}
    SWAGGER = {"title": "Allocation Service"}


class DevelopmentConfig(Config):
    DB_PATH = CURRENT_DIRECTORY / Path("dev.db")
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False"
    DB_URI = DB_PATH.as_uri() + DB_CONNECTION_SETTINGS
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}" + DB_CONNECTION_SETTINGS
    DB_TYPE = "SQlite3"


class TestingConfig(Config):
    DB_PATH = CURRENT_DIRECTORY
    DB_CONNECTION_SETTINGS = "?mode=rw&check_same_thread=False&cache=shared"
    DB_URI = ""
    SQLA_CONNECTION_STRING = "sqlite:///:memory:" + DB_CONNECTION_SETTINGS
    DB_TYPE = "MEMORY"


config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
    "testing": TestingConfig,
}


def get_config(config_name=None) -> Config:
    if not config_name:
        config_name = os.environ.get("ENV") or "default"
    return config[config_name]


def get_redis_config() -> Dict:
    config = get_config()
    return config.REDIS_CONFIG
