import sqlalchemy
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry, relationship
from sqlalchemy.pool import StaticPool

from allocation.config import get_config
from allocation.core import domain
from allocation.interfaces.database.datatypes import GUID

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
    Column("_product_id", GUID, ForeignKey("products._sku_id")),
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
    Column("version_number", Integer),
)

batches = Table(
    "batches",
    mapper_registry.metadata,
    Column("uuid", GUID, primary_key=True),
    Column("_sku_id", GUID, ForeignKey("skus.uuid")),
    Column("_product_id", GUID, ForeignKey("products._sku_id")),
    Column("quantity", Integer),
    Column("eta", Date),
    Column("allocated_quantity", Integer),
)

order_items_batches_association = Table(
    "association",
    mapper_registry.metadata,
    Column("order_item_id", ForeignKey("order_items.uuid")),
    Column("batches_id", ForeignKey("batches.uuid")),
)


def start_mappers():
    """Maps SQLAlchemy models to Domain models."""
    if not mapper_registry.mappers:
        mapper_registry.map_imperatively(domain.SKU, skus)
        mapper_registry.map_imperatively(domain.Customer, customers)
        mapper_registry.map_imperatively(
            domain.OrderItem,
            order_items,
            properties={
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
                    backref="batches",
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
                "order_items": relationship(
                    domain.OrderItem,
                    lazy="subquery",
                    backref="order_items",
                    cascade="all",
                    collection_class=set,
                ),
                "sku": relationship(
                    domain.SKU, backref="product", lazy="subquery", cascade="all"
                ),
            },
        )


start_mappers()


def create_engine():
    config = get_config()
    # Enable database sharing for in-memory SQlite3 DB
    poolclass = StaticPool if config.DB_TYPE == "MEMORY" else None
    engine = sqlalchemy.create_engine(
        config.SQLA_CONNECTION_STRING, poolclass=poolclass
    )
    return engine
