import json
import pickle
import smtplib
from uuid import UUID

from app.core import commands, domain, events
from app.interfaces.redis import get_redis_client
from app.repositories import UnitOfWork, get_current_repo


def is_valid_sku(sku: domain.SKU) -> bool:
    repo = get_current_repo()
    valid_skus = repo.list(domain.SKU)
    return sku in {sku_.uuid for sku_ in valid_skus}


class InvalidSKU(Exception):
    pass


def send_email_notification(event: events.OutOfStock) -> None:
    server = smtplib.SMTP("localhost")
    server.sendmail(
        f"You are being notified that the following SKU {event.sku_id} is OutOfStock"
    )
    server.quit()


def mock_send_email_notification(event: events.Event) -> None:
    print("Sending Event notification to mock@staff.com...")
    print(event)
    print("Notification sent!")


def create_order_item(cmd: commands.CreateOrderItem, uow: UnitOfWork):
    with uow:
        product = uow.products.get(cmd.sku_id)
        order_item = domain.create_order_item(product.sku, cmd.quantity)
        product.register_order_item(order_item)
        return order_item.uuid


def create_product(cmd: commands.CreateProductCommand, uow: UnitOfWork):
    with uow:
        product = domain.create_product(cmd.sku)
        uow.products.add(product)
        return product.sku_id


def create_batch(cmd: commands.CreateBatch, uow: UnitOfWork) -> UUID:
    with uow:
        product = uow.products.get(cmd.sku_id)
        batch = domain.create_batch(product.sku, cmd.quantity, cmd.eta)
        product.register_batch(batch)
        return batch.uuid


def allocate(cmd: commands.AllocateCommand, uow: UnitOfWork) -> domain.Batch:
    """Takes an order item and allocates available stock from known batches."""

    with uow:
        product = uow.products.get(cmd.sku_id)
        all_order_items = uow.products.get_all_order_items()
        order_item = next(oi for oi in all_order_items if oi.uuid == cmd.order_item_id)
        batch = product.allocate(order_item)

    return batch


def change_batch_quantity(cmd: commands.ChangeBatchQuantity, uow: UnitOfWork) -> UUID:

    with uow:
        product = uow.products.get(cmd.sku_id)
        [batch] = [b for b in product.batches if b.uuid == cmd.batch_id]
        batch.quantity = cmd.new_quantity
        while batch.allocated_quantity > batch.quantity:
            order_item = next(order_item for order_item in batch.allocated_order_items)
            batch.deallocate_available_quantity(order_item)

        return batch.uuid


def publish_event_to_external_broker(event: events.Event) -> None:
    channel = event.name
    event_s = pickle.dumps(event)
    client = get_redis_client()
    client.publish(channel, event_s)
