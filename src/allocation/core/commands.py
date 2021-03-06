import datetime
from dataclasses import asdict, dataclass, field
from typing import Dict
from uuid import UUID, uuid4

from allocation.core import domain


@dataclass
class Command:
    uuid: UUID = field(init=False, default_factory=uuid4)

    @property
    def cname(self) -> str:
        """Returns the command name."""
        return self.__class__.__name__

    def to_dict(self) -> Dict:
        return {**{"event": self.cname}, **asdict(self)}


class Discard(Command):
    """Discard sub-command."""


@dataclass
class Allocate(Command):
    sku_id: UUID
    order_item_id: UUID


@dataclass
class CreateOrderItem(Command):
    sku_id: UUID
    quantity: int


@dataclass
class DiscardOrderItem(Discard):
    sku_id: UUID
    order_item_id: UUID


@dataclass
class DiscardBatch(Discard):
    sku_id: UUID
    batch_id: UUID


@dataclass
class CreateProductCommand(Command):
    sku: domain.SKU


@dataclass
class CreateBatch(Command):
    sku_id: UUID
    quantity: int
    eta: datetime.datetime


@dataclass
class ChangeBatchQuantity(Command):
    sku_id: UUID
    batch_id: UUID
    new_quantity: int


@dataclass
class UpdateOrderItem(Command):
    sku_id: UUID
    order_item_id: UUID
    quantity: int


@dataclass
class UpdateProduct(Command):
    sku_id: UUID
    name: str


@dataclass
class DiscardProduct(Command):
    sku_id: UUID
