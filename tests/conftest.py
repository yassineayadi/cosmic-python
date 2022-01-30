import random
from datetime import date
from string import ascii_uppercase
from typing import Set, Tuple

import pytest

from allocation.core import domain
from allocation.core.domain import Batch, Customer, Order, OrderItem, Product, SKU
from allocation.entrypoints.app import create_app
from allocation.interfaces.database import db, orm


def make_test_sku() -> SKU:
    suffix = "".join([random.choice(ascii_uppercase) for _ in range(5)])
    sku_name = f"SKU-{suffix}"
    sku = domain.create_sku(sku_name)
    return sku


def make_test_product(
    sku=None, batches: Set[Batch] = None, order_items: Set[OrderItem] = None
) -> Product:
    sku = sku if sku else make_test_sku()
    batches = batches if batches else set()
    product = domain.create_product(sku, batches, order_items)
    return product


def make_test_customer() -> Customer:
    customer = domain.create_customer(first_name="Yassine", last_name="Ayadi")
    return customer


def make_test_order() -> Order:
    test_order_item = make_test_order_item()
    test_customer = make_test_customer()
    order = domain.create_order([test_order_item], test_customer)
    return order


def make_test_batch(sku=None, batch_qty=20, eta=None) -> Batch:
    eta = eta if eta else date.today()
    sku = sku if sku else make_test_sku()
    batch = domain.create_batch(sku, batch_qty, eta=eta)
    return batch


def make_test_order_item(sku=None, quantity=10) -> OrderItem:
    sku = sku if sku else make_test_sku()
    order_item = domain.create_order_item(sku, quantity=quantity)
    return order_item


def make_test_batch_and_order_item(
    sku, batch_qty, line_qty, eta=None
) -> Tuple[Batch, OrderItem]:
    sku = sku if sku else make_test_sku()
    batch, order_item = make_test_batch(sku, batch_qty, eta), make_test_order_item(
        sku, line_qty
    )
    return batch, order_item


def make_test_sku_and_product() -> Tuple[SKU, Product]:
    sku = make_test_sku()
    product = make_test_product(sku)
    return sku, product


def make_test_sku_product_and_batch() -> Tuple[SKU, Product, Batch]:
    sku = make_test_sku()
    batch = make_test_batch(sku, 20)
    product = make_test_product(sku, {batch})
    return sku, product, batch


def make_test_sku_product_and_order_item() -> Tuple[SKU, Product, OrderItem]:
    sku = make_test_sku()
    order_item = make_test_order_item(sku, 2)
    product = make_test_product(sku)
    return sku, product, order_item


@pytest.fixture(scope="session")
def client():
    app = create_app()

    with app.test_client() as flask_client:
        yield flask_client


@pytest.fixture(scope="session")
def sqlite_engine():
    return db.engine


@pytest.fixture(autouse=True, scope="session")
def init_sqlite3_memory_db(sqlite_engine):
    orm.mapper_registry.metadata.bind = sqlite_engine
    orm.mapper_registry.metadata.create_all()
