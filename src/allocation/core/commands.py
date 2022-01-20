import datetime
from dataclasses import asdict, dataclass, field
from typing import Dict
from uuid import UUID, uuid4

from allocation.core import domain


@dataclass
class Command:
    uuid: UUID = field(init=False, default_factory=uuid4)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> Dict:
        return {**{"event": self.name}, **asdict(self)}


@dataclass
class Allocate(Command):
    sku_id: UUID
    order_item_id: UUID


@dataclass
class CreateOrderItem(Command):
    sku_id: UUID
    quantity: int


@dataclass
class CreateProductCommand(Command):
    # sku_name: str
    sku: domain.SKU


@dataclass
class CreateBatch(Command):
    sku_id: domain.SKU
    quantity: int
    eta: datetime.datetime


@dataclass
class ChangeBatchQuantity(Command):
    sku_id: UUID
    batch_id: UUID
    new_quantity: int
