from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from allocation.core.events import (
    OrderItemAllocated,
    OrderItemCreated,
    OrderItemDeallocated,
    OrderItemDiscarded,
    OutOfStock,
    ProductCreated,
)


class NonMatchingSKU(Exception):
    pass


class AllocationError(Exception):
    pass


@dataclass
class Entity:
    uuid: UUID
    discarded: bool

    def to_dict(self) -> Dict:
        return asdict(self)

    # @property
    # def discarded(self):
    #     return self._discarded
    #
    # @discarded.setter
    # def discarded(self, value):
    #     if isinstance(value, bool):
    #         self._discarded = value
    #
    # def __post_init__(self):
    #     self._discarded = False
    #


@dataclass(unsafe_hash=True)
class SKU(Entity):
    name: str


@dataclass
class Customer(Entity):
    first_name: str
    last_name: str


@dataclass(unsafe_hash=True)
class OrderItem(Entity):
    sku: SKU
    quantity: int
    _sku_id: Optional[UUID] = None

    def __post_init__(self):
        self._sku_id = self.sku.uuid


@dataclass(unsafe_hash=True)
class Order(Entity):
    order_items: List[OrderItem]
    customer: Customer


@dataclass
class Batch(Entity):
    sku: SKU
    quantity: int
    allocated_order_items: Set[OrderItem] = field(default_factory=set)
    allocated_quantity: int = 0
    eta: Optional[date] = None

    def __hash__(self):
        return hash(self.uuid)

    def __lt__(self, other):
        if self.eta is None or other.eta is None:
            return False
        return self.eta < other.eta

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.allocated_quantity

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
        return order_item in self.allocated_order_items

    def allocate_available_quantity(self, order_item: OrderItem) -> None:
        if self.can_allocate(order_item):
            self.allocated_quantity += order_item.quantity
            self.allocated_order_items.add(order_item)

    def deallocate_available_quantity(self, order_item: OrderItem) -> None:
        if self.can_deallocate(order_item):
            self.allocated_quantity -= order_item.quantity
            self.allocated_order_items.remove(order_item)


class Product:
    def __init__(self, sku, order_items=None, batches=None, discarded=None):
        batches: Set[Batch] = batches if batches else set()
        order_items: Set[OrderItem] = order_items if order_items else set()
        self.sku = sku
        self.sku_id = sku.uuid
        self.batches = batches
        self.order_items = order_items
        self.events = []
        self.version_number = 0
        self.discarded = discarded

        self.events.append(ProductCreated(sku.uuid))

    def __eq__(self, other):
        if self.sku == other.sku:
            return True
        return False

    def __hash__(self):
        return hash(self.sku.uuid)

    @property
    def events(self):
        if not hasattr(self, "_events"):
            self.events = []
        return self._events

    @events.setter
    def events(self, value):
        self._events = value

    def register_batch(self, batch: Batch) -> None:
        if batch.sku == self.sku:
            self.batches.add(batch)
            self._increment_version()
        else:
            raise NonMatchingSKU(f"The batch {batch} does not match the Product SKU.")

    def register_order_item(self, order_item: OrderItem) -> None:
        if self.sku == order_item.sku:
            self.order_items.add(order_item)
            self.events.append(OrderItemCreated(self.sku.uuid, order_item.quantity))
            self._increment_version()
        else:
            raise NonMatchingSKU(
                f"The Order Item {order_item} does not match the Product SKU."
            )

    def deregister_order_item(self, order_item: OrderItem) -> None:
        if self.sku == order_item.sku:
            self.order_items.remove(order_item)
            order_item.discarded = True
            self.events.append(OrderItemDiscarded(self.sku.uuid, order_item.uuid))

            self._increment_version()
        else:
            raise NonMatchingSKU(
                f"The Order Item {order_item} does not match the Product SKU."
            )

    def allocate(self, order_item: OrderItem) -> Batch:
        if order_item not in self.order_items:
            self.register_order_item(order_item)
        try:
            batch = next(
                batch
                for batch in sorted(self.batches)
                if batch.can_allocate(order_item)
            )
            batch.allocate_available_quantity(order_item)
            self.events.append(OrderItemAllocated(self.sku.uuid, order_item.uuid))
            self._increment_version()
            return batch
        except StopIteration:
            self.events.append(OutOfStock(self.sku.uuid))

    def change_batch_quantity(self, batch_id, new_quantity) -> Batch:
        batch = next(b for b in self.batches if b.uuid == batch_id)
        batch.quantity = new_quantity
        while batch.available_quantity < 0:
            order_item = next(order_item for order_item in batch.allocated_order_items)
            batch.deallocate_available_quantity(order_item)
            self.events.append(
                OrderItemDeallocated(
                    self.sku.uuid, order_item.uuid, order_item.quantity
                )
            )
        return batch

    def _increment_version(self) -> None:
        self.version_number += 1


def create_sku(name) -> SKU:
    return SKU(uuid4(), False, name)


def create_customer(first_name: str, last_name: str) -> Customer:
    return Customer(
        uuid=uuid4(), first_name=first_name, last_name=last_name, discarded=False
    )


def create_order(order_items: List[OrderItem], customer: Customer) -> Order:
    return Order(
        uuid=uuid4(), order_items=order_items, customer=customer, discarded=False
    )


def create_product(
    sku: SKU, batches: Set[Batch] = None, order_items: Set[OrderItem] = None
) -> Product:
    return Product(sku, batches=batches, order_items=order_items, discarded=False)


def create_order_item(sku: SKU, quantity: int) -> OrderItem:
    uuid = uuid4()
    return OrderItem(uuid=uuid, sku=sku, quantity=quantity, discarded=False)


def create_batch(sku: SKU, quantity: int, eta: date = None):
    uuid = uuid4()
    return Batch(uuid=uuid, sku=sku, quantity=quantity, eta=eta, discarded=False)
