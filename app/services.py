from app.core.domain import SKU, OrderItem
from app.repositories import AbstractRepo, get_current_repo


def is_valid_sku(sku: SKU) -> bool:
    repo = get_current_repo()
    valid_skus = repo.list(SKU)
    return sku in {sku_.uuid for sku_ in valid_skus}


class InvalidSKU(Exception):
    pass


def allocate(order_item: OrderItem, repo: AbstractRepo):
    """Takes an order item and allocates available stock from known batches."""
    if not is_valid_sku(order_item.sku):
        raise InvalidSKU(f"{SKU!r} is not a valid entry.")

    batches = repo.get_all_batches()
    for batch in batches:
        batch.allocate_available_quantity(order_item)


