import datetime
from abc import ABC
from dataclasses import dataclass
from uuid import UUID

from core import domain


class Command(ABC):
    uuid: UUID


@dataclass
class AllocateCommand(Command):
    sku_id: UUID
    order_item_id: UUID
    quantity: int


@dataclass
class CreateOrderItem(Command):
    sku_id: UUID
    quantity: int


@dataclass
class CreateProductCommand(Command):
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
