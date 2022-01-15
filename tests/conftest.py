import random
from datetime import date
from string import ascii_uppercase
from typing import Set, Tuple
from uuid import uuid4

import pytest

from app.core import domain
from app.core.domain import SKU, Batch, Customer, Order, OrderItem, Product
from app.entrypoints.flask_app import create_app


def make_test_batch_and_order_item(
    sku, batch_qty, line_qty, eta=None
) -> Tuple[Batch, OrderItem]:
    sku = sku if sku else make_test_sku()
    return make_test_batch(sku, batch_qty, eta), make_test_order_item(sku, line_qty)


def make_test_sku_product_and_batch() -> Tuple[SKU, Product, Batch]:
    sku = make_test_sku()
    batch = make_test_batch(sku, 20)
    product = make_test_product(sku, {batch})
    return sku, product, batch


def make_test_batch(sku=None, batch_qty=20, eta=None) -> Batch:
    eta = eta if eta else date.today()
    sku = sku if sku else make_test_sku()
    return Batch(uuid4(), sku, batch_qty, eta=eta)


def make_test_order() -> Order:
    test_order_item = make_test_order_item()
    test_customer = make_test_customer()
    return Order(uuid4(), [test_order_item], test_customer)


def make_test_sku() -> SKU:
    suffix = "".join([random.choice(ascii_uppercase) for _ in range(5)])
    return SKU(uuid4(), f"SKU-{suffix}")


def make_test_customer():
    return Customer(uuid=uuid4(), first_name="Yassine", last_name="Ayadi")


def make_test_order_item(sku=None, quantity=10):
    sku = sku if sku else make_test_sku()
    return OrderItem(uuid4(), sku, quantity=quantity)


def make_test_product(sku=None, batches: Set[Batch] = None):
    sku = sku if sku else make_test_sku()
    batches = batches if batches else set()
    product = domain.create_product(sku)
    [product.register_batch(b) for b in batches]
    return product


@pytest.fixture
def client():
    app = create_app()

    with app.test_client() as client:
        yield client
