from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.orm import registry, relationship

from app.core import domain

from .datatypes import GUID

mapper_registry = registry()

skus = Table(
    "skus",
    mapper_registry.metadata,
    Column("uuid", GUID, primary_key=True),
    Column("name", String(255)),
)
customers = Table(
    "customers",
    mapper_registry.metadata,
    Column("uuid", GUID, primary_key=True),
    Column("first_name", String(100)),
    Column("last_name", String(100)),
)
order_items = Table(
    "order_items",
    mapper_registry.metadata,
    Column("uuid", GUID, primary_key=True),
    Column("_sku_id", GUID, ForeignKey("skus.uuid")),
    Column("quantity", Integer),
    Column("order_id", String(36)),
)
orders = Table(
    "orders",
    mapper_registry.metadata,
    Column("uuid", GUID, ForeignKey("skus.uuid"), primary_key=True),
    Column("order_items", String(36)),
)

products = Table(
    "products",
    mapper_registry.metadata,
    Column("_sku_id", GUID, ForeignKey("skus.uuid"), primary_key=True),
)

batches = Table(
    "batches",
    mapper_registry.metadata,
    Column("uuid", GUID, primary_key=True),
    Column("_sku_id", GUID, ForeignKey("skus.uuid")),
    Column("_product_id", GUID, ForeignKey("products._sku_id")),
    Column("quantity", Integer),
    Column("eta", Date),
    Column("available_quantity", Integer),
)

order_items_batches_association = Table(
    "association",
    mapper_registry.metadata,
    Column("order_item_id", ForeignKey("order_items.uuid")),
    Column("batches_id", ForeignKey("batches.uuid")),
)


def start_mappers():
    """Map SQLAlchemy models to Domain Models"""
    if not mapper_registry.mappers:
        mapper_registry.map_imperatively(domain.SKU, skus),
        mapper_registry.map_imperatively(domain.Customer, customers)
        mapper_registry.map_imperatively(
            domain.OrderItem,
            order_items,
            properties={
                "batches": relationship(
                    domain.Batch,
                    secondary=order_items_batches_association,
                    lazy="subquery",
                    back_populates="allocated_order_items",
                    # backref="batches",
                    cascade="all",
                    collection_class=set,
                ),
                "sku": relationship(
                    domain.SKU, backref="order_items", lazy="subquery", cascade="all"
                ),
            },
        )
        mapper_registry.map_imperatively(
            domain.Batch,
            batches,
            properties={
                "allocated_order_items": relationship(
                    domain.OrderItem,
                    secondary=order_items_batches_association,
                    lazy="subquery",
                    back_populates="batches",
                    # backref="batches",
                    cascade="all",
                    collection_class=set,
                ),
                "sku": relationship(
                    domain.SKU, backref="batches", lazy="subquery", cascade="all"
                ),
            },
        )
        mapper_registry.map_imperatively(domain.Order, orders)
        mapper_registry.map_imperatively(
            domain.Product,
            products,
            properties={
                "batches": relationship(
                    domain.Batch,
                    backref="product",
                    lazy="subquery",
                    cascade="all",
                    collection_class=set,
                ),
                "sku": relationship(
                    domain.SKU, backref="product", lazy="subquery", cascade="all"
                ),
            },
        )
