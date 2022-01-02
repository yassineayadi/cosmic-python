import random
import unittest
from datetime import date, timedelta
from string import ascii_uppercase
from typing import Tuple
from uuid import uuid4

from app.core.domain import SKU, Batch, Customer, Order, OrderItem, OutOfStock, allocate


def make_test_batch_and_order_item(
    sku, batch_qty, line_qty, eta=None
) -> Tuple[Batch, OrderItem]:
    sku = sku if sku else make_test_sku()
    return make_test_batch(sku, batch_qty, eta), make_test_order_item(sku, line_qty)


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


class TestSKU(unittest.TestCase):
    def test_create_sku(self):

        uuid = uuid4()
        sku = SKU(uuid=uuid, name="my SKU name")
        self.assertEqual(sku.uuid, uuid)
        self.assertEqual(sku.name, "my SKU name")


class TestCustomer(unittest.TestCase):
    def test_create_customer(self):

        uuid = uuid4()
        customer = Customer(uuid=uuid, first_name="Yassine", last_name="Ayadi")
        self.assertEqual(customer.uuid, uuid)
        self.assertEqual(customer.first_name, "Yassine")
        self.assertEqual(customer.last_name, "Ayadi")


class TestOrderItem(unittest.TestCase):
    def test_create_order_item(self):
        sku = make_test_sku()
        uuid = uuid4()
        order_item = OrderItem(uuid=uuid, sku=sku, quantity=2)
        self.assertEqual(order_item.uuid, uuid)
        self.assertEqual(order_item.sku, sku)
        self.assertEqual(order_item.quantity, 2)


class TestOrder(unittest.TestCase):
    def test_create_order(self):
        uuid = uuid4()
        sku = make_test_sku()
        order_item = OrderItem(uuid=uuid, sku=sku, quantity=2)
        customer = make_test_customer()

        order = Order(uuid=uuid, order_items=[order_item], customer=customer)

        self.assertEqual(order.uuid, uuid)
        self.assertEqual(order.order_items, [order_item])
        self.assertEqual(order.customer, customer)


class TestBatch(unittest.TestCase):
    def test_create_batch(self):
        uuid = uuid4()

        sku = make_test_sku()
        batch = Batch(uuid=uuid, sku=sku, quantity=20, eta=date.today())

        self.assertEqual(batch.uuid, uuid)
        self.assertEqual(batch.sku, sku)
        self.assertEqual(batch.quantity, 20)
        self.assertEqual(batch.eta, date.today())

    def test_batch_allocation(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 2)
        batch.allocate_available_quantity(order_item)
        self.assertEqual(batch.available_quantity, 18)

    def test_can_allocate_if_available_less_then_required(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 2)
        self.assertTrue(bool(batch.can_allocate(order_item)))

    def test_can_allocate_if_available_is_equal_to_required(self):
        batch, order_item = make_test_batch_and_order_item(make_test_sku(), 20, 20)
        self.assertTrue(batch.can_allocate(order_item))

    def test_cannot_allocate_if_different_sku(self):
        batch_1, _ = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        order_item_2 = make_test_order_item(make_test_sku(), 10)
        self.assertFalse(batch_1.can_allocate(order_item_2))

    def test_can_only_deallocate_allocated_lines(self):
        batch_1, order_item_1 = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        self.assertFalse(bool(batch_1.deallocate_available_quantity(order_item_1)))

    def test_batch_sorting_based_on_eta(self):
        earlier_batch, _ = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        later_batch, _ = make_test_batch_and_order_item(
            make_test_sku(), 20, 10, date.today() + timedelta(1)
        )
        self.assertTrue(later_batch > earlier_batch)

    def test_allocate_function_with_matching_pair(self):
        batch_1, order_item_1 = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        successful_allocation = allocate(order_item_1, [batch_1])
        self.assertTrue(len(successful_allocation) >= 1)

    def test_raise_OutOfStock_on_non_matching_order_item_and_batches(self):
        non_matching_order_item_1 = make_test_order_item(make_test_sku())
        batch_1 = make_test_batch(make_test_sku())

        self.assertRaises(
            OutOfStock,
            allocate,
            batches=[batch_1],
            order_item=non_matching_order_item_1,
        )
