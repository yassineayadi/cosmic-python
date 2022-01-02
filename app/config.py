import os
from pathlib import Path

CURRENT_DIRECTORY = Path(__file__).parent


class Config:
    DB_PATH: Path
    DB_URI: str
    SQLA_CONNECTION_STRING: str
    DB_TYPE: str


class DevelopmentConfig(Config):
    DB_PATH = Path(__file__).parent / Path("devdb.db")
    DB_URI = f"{DB_PATH.as_uri()}?mode=rw&check_same_thread=False"
    SQLA_CONNECTION_STRING = f"sqlite:///{DB_PATH}?mode=rw&check_same_thread=False"
    SQLA_ENGINE_CONNECTION_SETTINGS = {}
    DB_TYPE = "SQlite3"


class TestingConfig(Config):
    DB_PATH = Path(".")
    DB_URI = ""
    SQLA_CONNECTION_STRING = (
        "sqlite:///:memory:?mode=rw&check_same_thread=False&cache=shared"
    )
    DB_TYPE = "MEMORY"


config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
    "testing": TestingConfig,
}


def get_current_config(config_name=None) -> Config:
    if not config_name:
        config_name = os.environ.get("ENV") or "default"
    return config[config_name]
