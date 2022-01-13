from abc import ABC
from dataclasses import dataclass
from uuid import UUID


class Event(ABC):
    uuid: UUID


@dataclass
class OutOfStockEvent(Event):
    sku_id: UUID