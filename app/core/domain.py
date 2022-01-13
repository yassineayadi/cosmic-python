from abc import ABC
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from app.core.events import Event, OutOfStockEvent


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
        """Adjust Batch available quantity with ordered quantities."""
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
        return self.quantity - self.available_quantity

    def __lt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return False
        return self.eta < other.eta


@dataclass
class Product:

    sku: SKU
    sku_id: Optional[UUID] = None
    events: List[Event] = field(default_factory=list)
    batches: Set[Batch] = field(default_factory=set)
    # order_items: Set[OrderItem] = field(default_factory=set)
    version_number: int = field(default=0)

    def __post_init__(self):
        self.sku_id = self.sku.uuid

    def allocate(self, order_item: OrderItem) -> Batch:
        try:
            allocatable_batch = next(
                batch
                for batch in sorted(self.batches)
                if batch.can_allocate(order_item)
            )
            allocatable_batch.allocate_available_quantity(order_item)
            self._increment_version()
            return allocatable_batch
        except StopIteration:
            event = OutOfStockEvent(self.sku.uuid)
            self.events.append(event)

    def register_batch(self, batch: Batch) -> None:
        if batch.sku == self.sku:
            self.batches.add(batch)
            self._increment_version()
        else:
            raise NonMatchingSKU(f"The batch {batch} does not match the Product SKU.")
    #
    # def register_order_item(self, order_item: OrderItem) -> None:
    #     if order_item.sku == self.sku:
    #         self.order_items.add(order_item)
    #         self._increment_version()
    #     else:
    #         raise NonMatchingSKU(f"The order item {order_item} does not match the Product SKU.")

    @property
    def order_items(self) -> List[OrderItem]:
        return [
            order_item
            for batch in self.batches
            for order_item in batch.allocated_order_items
        ]

    def _increment_version(self):
        self.version_number += 1


def create_sku(sku_name) -> SKU:
    return SKU(uuid4(), sku_name)


def create_order_item(sku: SKU, quantity: int, uuid=None) -> OrderItem:
    uuid = uuid if uuid else uuid4()
    return OrderItem(uuid, sku, quantity)


def create_customer_id(first_name: str, last_name: str) -> Customer:
    return Customer(uuid4(), first_name, last_name)


def create_order(order_item, customer) -> Order:
    return Order(uuid4(), order_item, customer)
