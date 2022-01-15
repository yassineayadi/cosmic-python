import copy
import os
from abc import ABC, abstractmethod
from functools import reduce
from sqlite3 import OperationalError
from typing import Dict, List, Set

from sqlalchemy.orm import Session

from app.core.domain import SKU, Batch, OrderItem, Product
from app.interfaces import SessionFactory


class AbstractRepo(ABC):
    def __init__(self):
        self.seen = set()

    def get(self, reference) -> Product:
        """Retrieves Product by reference."""
        product = self._get(reference)
        self.seen.add(product)
        return product

    def add(self, product: Product) -> None:
        """Adds individual Product to persistent storage."""
        self._add(product)
        self.seen.add(product)

    def delete(self, product: Product) -> None:
        """Deletes Product from persistent storage layer."""
        self._delete(product)
        self.seen.remove(product)

    def add_all(self, products: List[Product]) -> None:
        """Adds list of Product  to persistent storage."""
        self.seen.update(products)
        self._add_all(products)

    @abstractmethod
    def _get(self, reference):
        raise NotImplementedError

    @abstractmethod
    def _add(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def _delete(self, product: Product) -> None:
        raise NotImplementedError

    @abstractmethod
    def _add_all(self, products: List[Product]):
        raise NotImplementedError

    @abstractmethod
    def get_all_batches(self) -> Set[Batch]:
        """Retrieves all batches currently registered."""
        ...

    @abstractmethod
    def list(self) -> List[Product]:
        """Lists all Product."""
        ...


class ProductsRepo(AbstractRepo):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _get(self, reference) -> Product:
        return self.session.get(Product, reference)

    def _add(self, product: Product) -> None:
        self.session.add(product)

    def _add_all(self, products: List[Product]) -> None:
        self.session.add_all(products)

    def _delete(self, product: Product) -> None:
        self.session.delete(product)

    def list(self) -> List[Product]:
        products = self.session.query(Product).all()
        self.seen.update(products)
        return products

    def get_by_sku_uuid(self, uuid):
        product = self.session.get(Product, uuid)
        self.seen.add(product)
        return product

    def get_all_skus(self) -> List[SKU]:
        return [p.sku for p in self.list()]

    def get_all_order_items(self) -> Set[OrderItem]:
        order_item_sets = [p.order_items for p in self.list()]
        order_items = reduce(lambda a, b: {*a, *b}, order_item_sets)
        return order_items

    def get_all_batches(self) -> Set[Batch]:
        batch_sets = [p.batches for p in self.list()]
        batches = reduce(lambda a, b: {*a, *b}, batch_sets)
        return batches


class MockRepo(AbstractRepo, Dict):
    def _delete(self, product: Product) -> None:
        try:
            del self[product]
        except KeyError:
            pass

    def get_all_batches(self) -> Set[Batch]:
        pass

    def list(self) -> List[Product]:
        return list(self.values())

    def _add(self, product) -> None:
        self[product.sku_id] = product

    def _get(self, reference) -> Product:
        return self.__getitem__(reference)

    def _list(self) -> List[Product]:
        return list(self.values())

    def _add_all(self, products: List[Product]) -> None:
        for prod in products:
            self.update({prod.sku_id: prod})


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

    def collect_new_messages(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)


class MockUnitOfWork(AbstractUnitOfWork):
    products: MockRepo
    _previous_repo_version: MockRepo

    def __init__(self, products):
        self.products = products

    def __enter__(self):
        self._previous_repo_version = copy.copy(self.products)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._rollback()
        else:
            self.commit()

    def _close(self):
        ...

    def _commit(self):
        self._previous_repo_version = self.products

    def _rollback(self):
        self.products = self._previous_repo_version


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
