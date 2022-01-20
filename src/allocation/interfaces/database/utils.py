from allocation.config import get_config


def create_db_if_no_exists():
    config = get_config()
    if not config.DB_PATH.exists():
        config.DB_PATH.touch()
