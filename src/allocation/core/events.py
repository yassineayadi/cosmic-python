from dataclasses import asdict, dataclass, field
from typing import Dict
from uuid import UUID, uuid4


@dataclass
class Event:
    uuid: UUID = field(init=False, default_factory=uuid4)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> Dict:
        return {**{"event": self.name}, **asdict(self)}


@dataclass
class OutOfStock(Event):
    sku_id: UUID


@dataclass
class ProductCreated(Event):
    sku_id: UUID


@dataclass
class OrderItemCreated(Event):
    sku_id: UUID
    quantity: int


@dataclass
class OrderItemAllocated(Event):
    sku_id: UUID
    order_item_id: UUID


@dataclass
class BatchCreated(Event):
    sku_id: UUID
    batch_id: UUID
    quantity: int


@dataclass
class BatchQuantityChanged(Event):
    batch_id: UUID
    quantity: int


@dataclass
class OrderItemDeallocated(Event):
    sku_id: UUID
    order_item_id: UUID
    quantity: int
