import os
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List

from sqlalchemy.orm import Session

from allocation.core.domain import SKU, Batch, OrderItem, Product


class AbstractRepo(ABC):
    def __init__(self):
        self.seen = set()

    def get(self, reference) -> Product:
        """Retrieves Product by reference."""
        product = self._get(reference)
        if product and not product.discarded:
            self.seen.add(product)
            return product
        raise InvalidSKU(f"The SKU with uuid {reference} does not exist.")

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
    def get_all_batches(self) -> Iterator[Batch]:
        """Retrieves all batches currently registered."""
        ...

    @abstractmethod
    def get_all_order_items(self) -> Iterator[OrderItem]:
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

    def get_all_skus(self) -> Iterator[SKU]:
        return (p.sku for p in self.list())

    def get_all_order_items(self) -> Iterator[OrderItem]:
        return (o for p in self.list() for o in p.order_items)

    def get_all_batches(self) -> Iterator[Batch]:
        return (b for p in self.list() for b in p.batches if not b.discarded)


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

    def _list(self) -> Iterator[Product]:
        return list(self.values())

    def get_all_batches(self) -> Iterator[Batch]:
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


class InvalidSKU(Exception):
    pass
