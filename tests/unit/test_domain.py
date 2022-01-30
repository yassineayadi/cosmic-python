from datetime import date, timedelta
from uuid import uuid4

import pytest

from conftest import (
    make_test_batch,
    make_test_batch_and_order_item,
    make_test_customer,
    make_test_order_item,
    make_test_product,
    make_test_sku,
    make_test_sku_product_and_batch,
    make_test_sku_product_and_order_item,
)

from allocation.core.domain import (
    SKU,
    Batch,
    Customer,
    NonMatchingSKU,
    Order,
    OrderItem,
    Product,
)
from allocation.core.events import OutOfStock


class TestSKU:
    def test_create_sku(self):
        uuid = uuid4()
        sku = SKU(uuid=uuid, name="my SKU name", discarded=False)
        assert sku.uuid == uuid
        assert sku.name == "my SKU name"
        assert sku.discarded is False


class TestCustomer:
    def test_create_customer(self):
        uuid = uuid4()
        customer = Customer(
            uuid=uuid, first_name="Yassine", last_name="Ayadi", discarded=False
        )
        assert customer.uuid == uuid
        assert customer.first_name == "Yassine"
        assert customer.last_name == "Ayadi"
        assert customer.discarded is False


class TestOrderItem:
    def test_create_order_item(self):
        sku = make_test_sku()
        uuid = uuid4()
        order_item = OrderItem(uuid=uuid, sku=sku, quantity=2, discarded=False)
        assert order_item.uuid == uuid
        assert order_item.sku == sku
        assert order_item.quantity == 2
        assert order_item.discarded is False


class TestOrder:
    def test_create_order(self):
        uuid = uuid4()
        sku = make_test_sku()
        order_item = OrderItem(uuid=uuid, sku=sku, quantity=2, discarded=False)
        customer = make_test_customer()

        order = Order(
            uuid=uuid, order_items=[order_item], customer=customer, discarded=False
        )

        assert order.uuid == uuid
        assert order.order_items == [order_item]
        assert order.customer == customer
        assert order.discarded is False


class TestBatch:
    def test_create_batch(self):
        uuid = uuid4()

        sku = make_test_sku()
        batch = Batch(
            uuid=uuid, sku=sku, quantity=20, eta=date.today(), discarded=False
        )

        assert batch.uuid == uuid
        assert batch.sku == sku
        assert batch.quantity == 20
        assert batch.eta == date.today()
        assert batch.discarded is False

    def test_batch_allocation(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 2)
        batch.allocate_available_quantity(order_item)
        assert batch.available_quantity == 18

    def test_can_allocate_if_available_less_then_required(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 2)
        assert bool(batch.can_allocate(order_item)) is True

    def test_can_allocate_if_available_is_equal_to_required(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 20)
        assert batch.can_allocate(order_item) is True

    def test_cannot_allocate_if_different_sku(self):
        batch_1 = make_test_batch(make_test_sku())
        order_item_2 = make_test_order_item(make_test_sku(), 10)
        assert batch_1.can_allocate(order_item_2) is False

    def test_can_only_deallocate_allocated_lines(self):
        batch_1, order_item_1 = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        assert bool(batch_1.deallocate_available_quantity(order_item_1)) is False

    def test_batch_sorting_based_on_eta(self):
        earlier_batch, _ = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        later_batch, _ = make_test_batch_and_order_item(
            make_test_sku(), 20, 10, date.today() + timedelta(1)
        )
        assert (later_batch > earlier_batch) is True

    def test_allocate_function_with_matching_pair(self):
        sku_1 = make_test_sku()
        batch_1, order_item_1 = make_test_batch_and_order_item(sku_1, 20, 10)
        product_1 = Product(sku_1)
        product_1.register_batch(batch_1)
        successful_allocation = product_1.allocate(order_item_1)
        assert (successful_allocation is not None) is True

    def test_create_outofstock_event_when_batch_has_insufficient_stock_available(self):
        sku, product, batch_with_insufficient_stock = make_test_sku_product_and_batch()
        product.register_batch(batch_with_insufficient_stock)
        order_item = make_test_order_item(sku, 30)

        allocation = product.allocate(order_item)
        assert allocation is None
        assert isinstance(product.events.pop(), OutOfStock)


class TestProduct:
    def test_create_product(self):
        sku = make_test_sku()
        product = Product(sku)
        assert isinstance(product, Product)

    def test_create_product_with_empty_batches(self):
        product = make_test_product()
        assert bool(product.batches) is False

    def test_raise_NonMatchingSKU_when_registering_batch_with_non_matching_sku(
        self,
    ):
        sku = make_test_sku()
        product = make_test_product(sku)
        non_matching_batch = make_test_batch()
        with pytest.raises(NonMatchingSKU):
            product.register_batch(non_matching_batch)

    def test_deregister_order_item(self):
        sku, product, order_item = make_test_sku_product_and_order_item()
        product.register_order_item(order_item)
        product.deregister_order_item(order_item)
        assert order_item.discarded is True
