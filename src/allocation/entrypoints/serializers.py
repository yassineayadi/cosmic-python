import inspect

from flask import Request, abort
from flask_marshmallow import Schema
from marshmallow import ValidationError, fields, post_load

from allocation.core import domain


class SKU(Schema):

    uuid = fields.UUID()
    name = fields.Str()

    @post_load
    def make_sku_schema(self, data, **kwargs):
        return domain.SKU(uuid=data["uuid"], name=data["name"], discarded=False)


class SKUListSchema(Schema):

    sku_ids = fields.List(fields.UUID())


class CreateSKU(Schema):

    name = fields.Str(required=True)


class CustomerSchema(Schema):

    uuid = fields.UUID()
    first_name = fields.Str()
    last_name = fields.Str()


class OrderItem(Schema):

    uuid = fields.UUID()
    sku = fields.Nested(SKU)
    quantity = fields.Integer()
    _sku_id = fields.UUID()

    @post_load
    def make_order_item(self, data, **kwargs):
        return domain.OrderItem(**data)


class OrderSchema(Schema):

    uuid = fields.UUID()
    order_items = fields.List(fields.Nested(OrderItem))
    customer = fields.Nested(CustomerSchema)


class Batch(Schema):

    uuid = fields.UUID()
    sku = fields.Nested(SKU)
    quantity = fields.Integer()
    eta = fields.Date()
    allocated_order_items = fields.List(fields.Nested(OrderItem))
    available_quantity = fields.Integer()


class CreateBatch(Schema):
    sku_id = fields.UUID()
    quantity = fields.Integer()
    eta = fields.Date()


class Product(Schema):
    sku = fields.Nested(SKU)
    sku_id = fields.UUID()
    batches = fields.Nested(Batch)
    order_items = fields.Nested(OrderItem)
    version_number = fields.Integer()


class UpdateProduct(Schema):
    sku_id = fields.UUID()
    name = fields.Str()


class Allocate(Schema):
    sku_id = fields.UUID()
    order_item_id = fields.UUID()


class DiscardOrderItem(Schema):
    sku_id = fields.UUID()
    order_item_id = fields.UUID()


class UpdateOrderItem(Schema):
    sku_id = fields.UUID()
    order_item_id = fields.UUID()
    quantity = fields.Integer()


class ChangeBatchQuantity(Schema):
    sku_id = fields.UUID()
    batch_id = fields.UUID()
    quantity = fields.Integer()


class CreateOrderItem(Schema):
    sku_id = fields.UUID()
    quantity = fields.Integer()


class DiscardBatch(Schema):
    sku_id = fields.UUID()
    batch_id = fields.UUID()


class DiscardProduct(Schema):
    sku_id = fields.UUID()


# All Schema definitions
definitions = tuple(
    s for s in locals().values() if inspect.isclass(s) and issubclass(s, Schema)
)


class Validate:
    """Wrapper for Marshmallow validation.

    Uses the provided schema to perform validation. Returns the deserialized data on __enter__,
    otherwise raises ValidationError."""

    def __init__(self, schema: Schema, request: Request):
        self.schema = schema
        self.request = request

    def __enter__(self):
        try:
            data = self.schema.load(self.request.json)
            return data
        except ValidationError as err:
            raise err

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...
