from typing import List

from app.core.domain import SKU, Batch, OrderItem
from app.repositories import ABCRepo, get_current_repo


def is_valid_sku(sku: SKU) -> bool:
    repo = get_current_repo()
    valid_skus = repo.list(SKU)
    return sku in {sku_.uuid for sku_ in valid_skus}


class InvalidSKU(Exception):
    pass


def allocate(order_item: OrderItem, repo: ABCRepo):
    """Takes an order item and allocates available stock from known batches."""
    if not is_valid_sku(order_item.sku):
        raise InvalidSKU(f"{SKU!r} is not a valid entry.")

    batches: List[Batch] = repo.list(Batch)
    for batch in batches:
        batch.allocate_available_quantity(order_item)
