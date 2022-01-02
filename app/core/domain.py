from abc import ABC
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4


@dataclass
class DomainObj(ABC):
    uuid: UUID
    ...

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

    uuid: UUID
    sku: SKU
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


class OutOfStock(Exception):
    pass


def allocate(order_item: OrderItem, batches: List[Batch]) -> Set[Batch]:
    allocated_batches = set(
        batch for batch in batches if batch.can_allocate(order_item)
    )
    if allocated_batches:
        return allocated_batches
    raise OutOfStock(f"{order_item.sku!r} is Out of Stock.")


def create_sku(sku_name) -> SKU:
    return SKU(uuid4(), sku_name)


def create_order_item(sku: SKU, quantity: int, uuid=None) -> OrderItem:
    uuid = uuid if uuid else uuid4()
    return OrderItem(uuid, sku, quantity)


def create_customer_id(first_name: str, last_name: str) -> Customer:
    return Customer(uuid4(), first_name, last_name)


def create_order(order_item, customer) -> Order:
    return Order(uuid4(), order_item, customer)
