from flask import Request, abort
from flask_marshmallow import Schema
from marshmallow import ValidationError, fields, post_load

from allocation.core.domain import SKU, OrderItem


class SKU(Schema):

    uuid = fields.UUID()
    name = fields.Str()

    @post_load
    def make_sku_schema(self, data, **kwargs):
        return SKU(data["uuid"], data["name"])


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
        return OrderItem(**data)


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


class Product(Schema):
    sku = fields.Nested(SKU)
    sku_id = fields.UUID()
    batches = fields.Nested(Batch)
    order_items = fields.Nested(OrderItem)
    version_number = fields.Integer()


class DataLoader:
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
