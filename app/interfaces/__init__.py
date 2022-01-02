from abc import abstractmethod

import sqlalchemy
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Config, get_current_config
from app.interfaces.models import mapper_registry, start_mappers


class Interface:
    @abstractmethod
    def execute(self):
        ...


class SQLiteInterface:
    def __init__(self, config: Config = get_current_config()):
        self.db_path = config.DB_PATH
        self.sessionmaker = sessionmaker
        self.engine = engine_factory()
        self.mapper_registry = mapper_registry

        self._create_database_if_no_exists()
        self._drop_and_create_all_tables()
        self._map_domain_models_to_database_models()

    # def _open_session(self, *args, **kwargs) -> Session:

    def _map_domain_models_to_database_models(self) -> None:
        start_mappers()

    def _drop_and_create_all_tables(self) -> None:
        self._bind_metadata()
        self.mapper_registry.metadata.drop_all()
        self.mapper_registry.metadata.create_all()

    def _bind_metadata(self) -> None:
        self.mapper_registry.metadata.bind = self.engine

    def _create_database_if_no_exists(self):
        if not self.db_path.exists():
            self.db_path.touch()

    def create_interface(self, *args, **kwargs) -> Session:
        SessionClass = scoped_session(self.sessionmaker(self.engine))
        return SessionClass(**kwargs)


def engine_factory():
    config = get_current_config()
    if config.DB_TYPE in ("MEMORY"):
        # Enable database sharing for in-memory SQlite3 DB
        poolclass = StaticPool
    else:
        poolclass = None
    engine = sqlalchemy.create_engine(
        config.SQLA_CONNECTION_STRING, poolclass=poolclass
    )
    return engine
