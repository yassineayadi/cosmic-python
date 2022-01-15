from abc import ABC
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from app.core.events import (
    OrderItemAllocated,
    OrderItemCreated,
    OutOfStock,
    ProductCreated,
)


class NonMatchingSKU(Exception):
    pass


class AllocationError(Exception):
    pass


@dataclass
class DomainObj(ABC):
    uuid: UUID

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass(unsafe_hash=True)
class SKU(DomainObj):

    uuid: UUID
    name: str


@dataclass
class Customer(DomainObj):

    uuid: UUID
    first_name: str
    last_name: str


@dataclass(unsafe_hash=True)
class OrderItem(DomainObj):

    uuid: UUID
    sku: SKU
    quantity: int
    _sku_id: Optional[UUID] = None

    def __post_init__(self):
        self._sku_id = self.sku.uuid


@dataclass(unsafe_hash=True)
class Order(DomainObj):

    uuid: UUID
    order_items: List[OrderItem]
    customer: Customer


@dataclass
class Batch(DomainObj):

    sku: SKU
    uuid: UUID
    quantity: int
    eta: Optional[date] = None
    allocated_order_items: Set[OrderItem] = field(default_factory=set)
    available_quantity: Optional[int] = None

    def __post_init__(self):
        self.available_quantity = self.quantity

    def allocate_available_quantity(self, order_item: OrderItem) -> None:
        if self.can_allocate(order_item):
            self.available_quantity = self.available_quantity - order_item.quantity
            self.allocated_order_items.add(order_item)

    def deallocate_available_quantity(self, order_item: OrderItem) -> None:
        if self.can_deallocate(order_item):
            self.available_quantity += order_item.quantity
            self.allocated_order_items.remove(order_item)

    def can_allocate(self, order_item: OrderItem) -> bool:
        if order_item in self.allocated_order_items:
            raise AllocationError(f"{order_item} already allocated to {self}.")
        if (
            self.available_quantity >= order_item.quantity
            and self.sku == order_item.sku
        ):
            return True
        return False

    def can_deallocate(self, order_item: OrderItem) -> bool:
        if order_item in self.allocated_order_items:
            return True
        return False

    def __hash__(self):
        return hash(self.uuid)

    @property
    def allocated_quantity(self) -> int:
        # return self.quantity - sum(o.quantity for o in self.allocated_order_items)
        return sum(o.quantity for o in self.allocated_order_items)

    def __lt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return False
        return self.eta < other.eta


class Product:
    def __init__(self, sku, order_items=None, batches=None):
        batches = batches if batches else set()
        order_items = order_items if order_items else set()
        self.sku = sku
        self.sku_id = sku.uuid
        self.batches = batches
        self.order_items = order_items
        self.events = []
        self.version_number = 0

        self.events.append(ProductCreated(sku.uuid))

    @property
    def events(self):
        if not hasattr(self, "_events"):
            self.events = []
        return self._events

    @events.setter
    def events(self, value):
        self._events = value

    def __eq__(self, other):
        if self.sku == other.sku:
            return True
        return False

    def __hash__(self):
        return hash(self.sku.uuid)

    def allocate(self, order_item: OrderItem) -> Batch:
        try:
            batch = next(
                batch
                for batch in sorted(self.batches)
                if batch.can_allocate(order_item)
            )
            batch.allocate_available_quantity(order_item)
            event = OrderItemAllocated(self.sku.uuid, order_item.uuid)
            self.events.append(event)
            self._increment_version()
            return batch
        except StopIteration:
            event = OutOfStock(self.sku.uuid)
            self.events.append(event)

    def register_batch(self, batch: Batch) -> None:
        if batch.sku == self.sku:
            self.batches.add(batch)
            self._increment_version()
        else:
            raise NonMatchingSKU(f"The batch {batch} does not match the Product SKU.")

    def register_order_item(self, order_item: OrderItem) -> None:
        if self.sku == order_item.sku:
            self.order_items.add(order_item)
            event = OrderItemCreated(self.sku.uuid, order_item.quantity)
            self.events.append(event)
            self._increment_version()
        else:
            raise NonMatchingSKU(
                f"The Order Item {order_item} does not match the Product SKU."
            )

    def _increment_version(self) -> None:
        self.version_number += 1


def create_sku(sku_name) -> SKU:
    return SKU(uuid4(), sku_name)


def create_customer_id(first_name: str, last_name: str) -> Customer:
    return Customer(uuid4(), first_name, last_name)


def create_order(order_item, customer) -> Order:
    return Order(uuid4(), order_item, customer)


def create_product(sku: SKU) -> Product:
    return Product(sku)


def create_order_item(sku: SKU, quantity: int, uuid=None) -> OrderItem:
    uuid = uuid if uuid else uuid4()
    return OrderItem(uuid, sku, quantity)


def create_batch(sku: SKU, quantity: int, eta: date = None, uuid=None):
    uuid = uuid if uuid else uuid4()
    return Batch(uuid=uuid, sku=sku, quantity=quantity, eta=eta)
