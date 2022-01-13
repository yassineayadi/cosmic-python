import sqlalchemy
from sqlalchemy import event
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Config, get_current_config
from app.interfaces import orm


class SessionFactory:
    def __init__(self, engine):
        self.sessionmaker = sessionmaker
        self.engine = engine
        self.mapper_registry = orm.mapper_registry

        self._create_database_if_no_exists()
        self._drop_and_create_all_tables()
        self._map_domain_models_to_database_models()

    def _map_domain_models_to_database_models(self) -> None:
        orm.start_mappers()

    def _drop_and_create_all_tables(self) -> None:
        self._bind_metadata()
        self.mapper_registry.metadata.drop_all()
        self.mapper_registry.metadata.create_all()

    def _bind_metadata(self) -> None:
        self.mapper_registry.metadata.bind = self.engine

    def _create_database_if_no_exists(self):
        orm.create_db_if_no_exists()


    def __call__(self, **kwargs) -> Session:
        session_class = scoped_session(self.sessionmaker(self.engine))  # pylint: ignore
        return session_class(**kwargs)


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


session_factory = SessionFactory(engine_factory())


@event.listens_for(session_factory.engine, "connect")
def do_connect(dbapi_connection, connection_record):
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


# @event.listens_for(session_factory.engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     dbapi_connection.isolation_level = None
#
#     # cursor = dbapi_connection.cursor()
#     # cursor.execute("PRAGMA journal_mode=WAL")
#     # cursor.close()


@event.listens_for(session_factory.engine, "begin")
def do_begin(conn: sqlalchemy.engine.Connection):
    # emit our own BEGIN
    if not conn.in_transaction():
        conn.exec_driver_sql("BEGIN")
