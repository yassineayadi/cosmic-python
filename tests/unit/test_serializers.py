import datetime
import json
import unittest
from uuid import UUID, uuid4

from allocation.entrypoints import serializers
from allocation.entrypoints.serializers import (
    Batch,
    CustomerSchema,
    OrderItem,
    OrderSchema,
    SKU,
)
from conftest import (
    make_test_batch,
    make_test_batch_and_order_item,
    make_test_customer,
    make_test_order,
    make_test_order_item,
    make_test_sku,
)


class TestSerializers(unittest.TestCase):
    def test_serialize_sku_schema_with_correct_schema(self):
        sku = make_test_sku()
        s_sku = SKU().dumps(sku)
        try:
            json.loads(s_sku)
        except ValueError as e:
            self.fail(f"{e}, failed with correct schema")

    def test_load_sku_with_correct_schema(self):
        uuid = uuid4()
        s_sku = json.dumps({"uuid": str(uuid), "name": "my correct test name"})
        # sku = make_test_sku()
        sku = SKU().loads(s_sku)
        self.assertTrue(sku.uuid == uuid)

    def test_serialize_customer_schema_with_correct_schema(self):
        customer = make_test_customer()
        s_customer = CustomerSchema().dumps(customer)
        try:
            json.loads(s_customer)
        except ValueError as err:
            self.fail(f"{err}, failed with correct schema")

    def test_load_customer_with_correct_schema(self):
        uuid = uuid4()
        first_name = "Yassine"
        last_name = "Ayadi"

        s_customer = json.dumps(
            {"uuid": str(uuid), "first_name": first_name, "last_name": last_name}
        )
        customer = CustomerSchema().loads(s_customer)
        self.assertTrue(customer["uuid"] == uuid)

    def test_serialize_order_item_with_correct_schema(self):
        order_item = make_test_order_item(make_test_sku(), 20)

        s_order_item = OrderItem().dumps(order_item)

        try:
            json.loads(s_order_item)
        except ValueError as err:
            self.fail(f"{err}, failed with correct schema")

    def test_serialize_order_with_correct_schema(self):
        order = make_test_order()

        s_order = OrderSchema().dumps(order)
        # try:
        data = json.loads(s_order)

        self.assertTrue(bool(data.get("uuid", None)) is True)
        self.assertTrue(bool(data.get("order_items", None)) is True)
        self.assertTrue(bool(data.get("customer", None)) is True)

    def test_serialize_batch_with_correct_schema(self):
        sku = make_test_sku()
        batch, order_item = make_test_batch_and_order_item(sku, 20, 2)
        s_batch = Batch().dumps(batch)

        data = Batch().loads(s_batch)
        self.assertTrue(bool(data.get("uuid", None)) is True)
        self.assertTrue(bool(data.get("sku", None)) is True)
        self.assertTrue(bool(data.get("quantity", None)) is True)
        self.assertTrue(bool(data.get("eta", None)) is True)
        self.assertTrue(bool(data.get("allocated_order_items", None)) is False)
        self.assertTrue(bool(data.get("available_quantity", None)) is True)

    def test_load_create_batch_with_correct_schema(self):
        batch = make_test_batch(make_test_sku())
        batch_data = json.dumps(
            {
                "sku_id": str(batch.sku.uuid),
                "quantity": str(batch.quantity),
                "eta": str(batch.eta),
            }
        )

        create_batch = serializers.CreateBatch().loads(batch_data)
        assert isinstance(create_batch["sku_id"], UUID)
        assert isinstance(create_batch["quantity"], int)
        assert isinstance(create_batch["eta"], datetime.date)
