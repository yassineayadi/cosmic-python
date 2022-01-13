import copy
import os
import sys
import traceback
from abc import ABC, abstractmethod
from functools import reduce
from sqlite3 import OperationalError
from typing import Dict, List, Set, Type

from sqlalchemy.orm import Session

from app.core.domain import SKU, Batch, OrderItem, Product
from app.interfaces import SessionFactory


class AbstractRepo(ABC):
    @abstractmethod
    def get(self, reference) -> Product:
        """Retrieves Product by reference."""
        ...

    @abstractmethod
    def get_all_batches(self) -> Set[Batch]:
        """Retrieves all batches currently registered."""
        ...

    @abstractmethod
    def add(self, product: Product) -> None:
        """Adds individual Product to persistent storage."""
        ...

    @abstractmethod
    def add_all(self, products: List[Product]) -> None:
        """Adds list of Product  to persistent storage."""
        ...

    @abstractmethod
    def list(self) -> List[Product]:
        """Lists all Product."""
        ...

    @abstractmethod
    def delete(self, product: Product) -> None:
        """Deletes Product from persistent storage layer."""


class ProductsRepo(AbstractRepo):
    def __init__(self, session: Session):
        self.session = session

    def get(self, reference) -> Product:
        return self.session.get(Product, reference)

    def add(self, product: Product) -> None:
        self.session.add(product)

    def add_all(self, products: List[Product]) -> None:
        self.session.add_all(products)

    def list(self) -> List[Product]:
        return self.session.query(Product).all()

    def delete(self, product: Product) -> None:
        self.session.delete(product)

    def get_by_sku_uuid(self, uuid):
        return self.session.get(Product, uuid)

    def get_all_skus(self) -> List[SKU]:
        return [p.sku for p in self.list()]

    def get_all_order_items(self) -> Set[OrderItem]:
        order_item_sets = {order_item for order_item in self.list()}
        order_items = reduce(lambda a, b: {*a, *b}, order_item_sets)
        return order_items

    def get_all_batches(self) -> Set[Batch]:
        batch_sets = [p.batches for p in self.list()]
        batches = reduce(lambda a, b: {*a, *b}, batch_sets)
        return batches


class MockRepo(AbstractRepo, Dict):
    def add(self, product):
        self[product.sku_id] = product

    def get(self, reference):
        return self.__getitem__(reference)

    def list(self) -> List[Product]:
        return list(self.values())

    def add_all(self, products: List[Product]) -> None:
        for prod in products:
            self.update({prod.sku_id: prod})


class AbstractUnitOfWork(ABC):
    @abstractmethod
    def __init__(self, factory: SessionFactory):
        """Initializes UnitOfWork with repository and session factory."""
        self.session_factory = factory

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

    def rollback(self):
        return self._rollback()

    @abstractmethod
    def _close(self):
        raise NotImplementedError

    @abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _rollback(self):
        raise NotImplementedError


class MockUnitOfWork(AbstractUnitOfWork):
    def __init__(self, repo: MockRepo):
        self.repo = repo
        self.previous_repo_version = copy.deepcopy(repo)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.repo = self.previous_repo_version

    def _close(self):
        ...

    def _commit(self):
        self.previous_repo_version = self.repo

    def _rollback(self):
        self.repo = self.previous_repo_version


class UnitOfWork(AbstractUnitOfWork):
    session: Session
    products: ProductsRepo

    def __init__(self, session_factory: SessionFactory):
        self.session_factory = session_factory

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

    def _close(self) -> None:
        if self.session.is_active:
            self.session.close()

    def _commit(self):
        self.session.commit()

    def _rollback(self):
        self.session.rollback()


repos = {
    "development": ProductsRepo,
    "testing": MockRepo,
    "default": ProductsRepo,
    "mock": MockRepo,
}


def get_current_repo(config_name=None) -> AbstractRepo:
    if not config_name:
        config_name = os.environ.get("ENV") or "default"
    repo_class = repos[config_name]
    return repo_class()
