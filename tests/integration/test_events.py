from conftest import make_test_product

from allocation.core import events


def test_product_created_event():
    product = make_test_product()
    event = product.events.pop()
    assert isinstance(event, events.ProductCreated)
