import sqlalchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from allocation.interfaces.database import orm


class SessionFactory:
    def __init__(self, sqla_engine: Engine):
        self.sessionmaker = sessionmaker
        self.engine = sqla_engine
        self.mapper_registry = orm.mapper_registry

    def __call__(self, **kwargs) -> Session:
        """Returns a thread-local session instance."""
        session_class = scoped_session(self.sessionmaker(self.engine))
        return session_class(**kwargs)


engine = orm.create_engine()
session_factory = SessionFactory(engine)


@event.listens_for(engine, "connect")
def do_connect(dbapi_connection, connection_record):
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


@event.listens_for(engine, "begin")
def do_begin(conn: sqlalchemy.engine.Connection):
    # emit our own BEGIN
    if not conn.in_transaction():
        conn.exec_driver_sql("BEGIN")
