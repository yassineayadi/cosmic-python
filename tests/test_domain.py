import unittest
from datetime import date, timedelta
from uuid import uuid4

from conftest import (
    make_test_batch,
    make_test_batch_and_order_item,
    make_test_customer,
    make_test_order_item,
    make_test_product,
    make_test_sku,
)

from app.core.domain import (
    SKU,
    Batch,
    Customer,
    NonMatchingSKU,
    Order,
    OrderItem,
    Product,
)
from app.core.events import OutOfStockEvent


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
        sku_1 = make_test_sku()
        batch_1, order_item_1 = make_test_batch_and_order_item(sku_1, 20, 10)
        product_1 = Product(sku_1)
        product_1.register_batch(batch_1)
        # successful_allocation = allocate(order_item_1, [batch_1])
        successful_allocation = product_1.allocate(order_item_1)
        self.assertTrue(successful_allocation is not None)

    def test_creates_OutOfStockEvent_on_non_matching_order_item_and_batches(self):
        sku_1 = make_test_sku()
        batch_1 = make_test_batch(sku_1)
        product_1 = Product(sku_1)
        product_1.register_batch(batch_1)
        non_matching_order_item_1 = make_test_order_item(make_test_sku())

        allocation = product_1.allocate(non_matching_order_item_1)
        assert allocation is None
        assert isinstance(product_1.events.pop(), OutOfStockEvent)

    class TestProduct(unittest.TestCase):
        def test_create_product(self):
            sku_1 = make_test_sku()
            product_1 = Product(sku_1)
            self.assertIsInstance(product_1, Product)

        def test_create_product_with_empty_batches(self):
            product_1 = make_test_product()
            self.assertTrue(bool(product_1.batches) is False)

        def test_raise_NonMatchingSKU_batch_with_incorrect_with_non_matching_sku(self):
            sku_1 = make_test_sku()
            product_1 = make_test_product(sku_1)
            non_matching_batch_1 = make_test_batch()
            self.assertRaises(
                NonMatchingSKU, product_1.register_batch, batch=non_matching_batch_1
            )
