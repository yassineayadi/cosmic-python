import os
from abc import ABC, abstractmethod
from functools import reduce
from typing import Dict, List, Set

from sqlalchemy.orm import Session

from allocation.core.domain import SKU, Batch, OrderItem, Product


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
        """Adds list of Product to persistent storage."""
        self.seen.update(products)
        self._add_all(products)

    @abstractmethod
    def _get(self, reference):
        raise NotImplementedError

    @abstractmethod
    def _add(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def _delete(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def _add_all(self, products: List[Product]):
        raise NotImplementedError

    @abstractmethod
    def get_all_batches(self) -> Set[Batch]:
        """Retrieves all batches currently registered."""
        ...

    @abstractmethod
    def get_all_order_items(self) -> Set[OrderItem]:
        """Retrieves all order items currently registered."""

    def list(self) -> List[Product]:
        """Lists all Product."""
        products = self._list()
        self.seen.update(products)
        return products

    @abstractmethod
    def _list(self) -> List[Product]:
        raise NotImplementedError


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

    def _list(self) -> List[Product]:
        products = self.session.query(Product).all()
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
    def _get(self, reference) -> Product:
        return self.__getitem__(reference)

    def _add(self, product) -> None:
        self[product.sku_id] = product

    def _add_all(self, products: List[Product]) -> None:
        for prod in products:
            self.update({prod.sku_id: prod})

    def _delete(self, product: Product) -> None:
        try:
            del self[product]
        except KeyError:
            pass

    def _list(self) -> List[Product]:
        return list(self.values())

    def get_all_batches(self) -> Set[Batch]:
        pass


repos = {
    "development": ProductsRepo,
    "testing": MockRepo,
    "default": ProductsRepo,
    "mock": MockRepo,
}


def get_repo(config_name=None) -> AbstractRepo:
    config_name = config_name if config_name else os.environ.get("ENV") or "default"
    repo_class = repos[config_name]
    return repo_class()