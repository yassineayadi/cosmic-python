import copy
from abc import ABC, abstractmethod
from sqlite3 import OperationalError

from sqlalchemy.orm import Session

from allocation.interfaces.database.db import SessionFactory, session_factory
from allocation.repositories import AbstractRepo, MockRepo, ProductsRepo


class AbstractUnitOfWork(ABC):
    products: AbstractRepo

    @abstractmethod
    def __enter__(self):
        """Creates a scoped with the provided session factory."""
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handles raised errors in with black or on commit."""
        ...

    def close(self) -> None:
        return self._close()

    def commit(self) -> None:
        return self._commit()

    def rollback(self) -> None:
        return self._rollback()

    @abstractmethod
    def _close(self):
        raise NotImplementedError

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def _rollback(self):
        raise NotImplementedError

    def collect_new_messages(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)


class MockUnitOfWork(AbstractUnitOfWork):
    products: MockRepo
    _rollback_version: MockRepo

    def __init__(self, products):
        self.products = products

    def __enter__(self):
        self._rollback_version = copy.copy(self.products)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    def _close(self):
        ...

    def _commit(self):
        self._rollback_version = self.products

    def _rollback(self):
        self.products = self._rollback_version


class UnitOfWork(AbstractUnitOfWork):
    session: Session
    products: ProductsRepo

    def __init__(self, factory: SessionFactory = session_factory):
        self.session_factory = factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = ProductsRepo(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        try:
            self.session.commit()
        except OperationalError:
            self.session.rollback()
        finally:
            self.session.close()

    def _close(self):
        if self.session.is_active:
            self.session.close()

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()
