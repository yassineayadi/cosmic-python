from flask_marshmallow import Schema
from marshmallow import fields, post_load

from allocation.core.domain import SKU, OrderItem


class SKUSchema(Schema):

    uuid = fields.UUID()
    name = fields.Str()

    @post_load
    def make_sku_schema(self, data, **kwargs):
        return SKU(data["uuid"], data["name"])


class SKUListSchema(Schema):

    sku_ids = fields.List(fields.UUID())


class CreateSKUSchema(Schema):

    sku_names = fields.List(fields.Str)


class CustomerSchema(Schema):

    uuid = fields.UUID()
    first_name = fields.Str()
    last_name = fields.Str()


class OrderItemSchema(Schema):

    uuid = fields.UUID()
    sku = fields.Nested(SKUSchema)
    quantity = fields.Integer()
    _sku_id = fields.UUID()

    @post_load
    def make_order_item(self, data, **kwargs):
        return OrderItem(**data)


class OrderSchema(Schema):

    uuid = fields.UUID()
    order_items = fields.List(fields.Nested(OrderItemSchema))
    customer = fields.Nested(CustomerSchema)


class BatchSchema(Schema):

    uuid = fields.UUID()
    sku = fields.Nested(SKUSchema)
    quantity = fields.Integer()
    eta = fields.Date()
    allocated_order_items = fields.List(fields.Nested(OrderItemSchema))
    available_quantity = fields.Integer()
