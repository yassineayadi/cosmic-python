import os
from abc import ABC, abstractmethod
from typing import Dict, List, Type

from app.core.domain import SKU, DomainObj, OrderItem
from app.interfaces import SQLiteInterface


class ABCRepo(ABC):
    @abstractmethod
    def get(self, obj: Type[DomainObj], reference) -> DomainObj:
        """Retrieves object of type obj: with reference:"""
        ...

    @abstractmethod
    def open_session(self):
        ...

    @abstractmethod
    def add(self, obj: DomainObj) -> None:
        """Adds individual object to persistent storage."""
        ...

    @abstractmethod
    def add_all(self, objs: List[DomainObj]) -> None:
        """Adds list of objects to persistent storage."""
        ...

    @abstractmethod
    def list(self, obj: Type[DomainObj]) -> List[DomainObj]:
        """Lists all objects of a given type."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Closes existing connection with persistent storage."""
        ...

    @abstractmethod
    def refresh(self, obj: DomainObj) -> None:
        """Refreshes object with persistent storage changes."""
        ...

    @abstractmethod
    def delete(self, obj: DomainObj) -> None:
        """Deletes object from persistent storage layer."""

    @abstractmethod
    def commit(self) -> None:
        """Commits changes to persistent storage."""
        ...

    @abstractmethod
    def merge(self, obj: DomainObj, **kwargs) -> DomainObj:
        """Merges object instance with session attached object instance."""
        ...

    @abstractmethod
    def revert(self):
        pass


class Repo(ABCRepo):
    def __init__(self, interface: SQLiteInterface = SQLiteInterface()):
        self.interface = interface

    def open_session(self):
        self.session = self.interface.create_interface(expire_on_commit=False)

    def get(self, obj: Type[DomainObj], reference) -> DomainObj:
        return self.session.get(obj, reference)

    def add(self, obj: DomainObj) -> None:
        self.session.add(obj)

    def add_all(self, objs: List[DomainObj]) -> None:
        self.session.add_all(objs)

    def list(self, obj: Type[DomainObj]) -> List[DomainObj]:
        return self.session.query(obj).all()

    def delete(self, obj: DomainObj) -> None:
        self.session.delete(obj)

    def close(self) -> None:
        if self.session.is_active:
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, obj: DomainObj) -> None:
        self.session.refresh(obj)

    def merge(self, obj: DomainObj, **kwargs) -> DomainObj:
        return self.session.merge(obj, **kwargs)

    def revert(self):
        self.session.rollback()

    # @property
    # def is_open(self) -> bool:
    #     return self.session.is_active


class UnitOfWorkABC(ABC):
    @abstractmethod
    def __init__(self, repo: ABCRepo):
        self.repo = repo

    @abstractmethod
    def __enter__(self):
        """scoped session"""
        self.repo.open_session()
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.close()
        # https://docs.sqlalchemy.org/en/14/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session
        # self.scoped_session.remove()


class UnitofWork(UnitOfWorkABC):
    def __init__(self, repo: ABCRepo):
        self.repo = repo

    def __enter__(self):
        self.repo.open_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.repo.commit()
        except:
            self.repo.revert()
        finally:
            self.repo.close()


class MockRepo(ABCRepo, Dict):
    def add(self, obj):
        self[obj.uuid] = obj

    def get(self, obj: Type[DomainObj], reference):
        return self.__getitem__(reference)

    def list(self, obj: Type[DomainObj]) -> List:
        return list(self.values())

    def add_all(self, values: List) -> None:
        for value in values:
            self.update({value.uuid: value})


repos = {"development": Repo, "testing": Repo, "default": Repo, "mock": MockRepo}


def get_current_repo(config_name=None) -> ABCRepo:
    if not config_name:
        config_name = os.environ.get("ENV") or "default"
    repo_class = repos[config_name]
    return repo_class()
