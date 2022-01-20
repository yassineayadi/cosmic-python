import smtplib
from uuid import UUID

from allocation.core import commands, domain, events
from allocation.interfaces.external_bus import create_redis_client
from allocation.repositories import get_repo
from allocation.unit_of_work import AbstractUnitOfWork


def is_valid_sku(sku: domain.SKU) -> bool:
    repo = get_repo()
    valid_products = repo.list()
    return sku in {p.sku.uuid for p in valid_products}


class InvalidSKU(Exception):
    pass


def send_email_notification(event: events.OutOfStock) -> None:
    server = smtplib.SMTP("localhost")
    server.sendmail(
        msg=f"You are being notified that the following SKU {event.sku_id} is OutOfStock",
        to_addrs="",
        from_addr="",
    )
    server.quit()


def mock_send_email_notification(event: events.Event) -> None:
    print("Sending Event notification to mock@staff.com...")
    print(event)
    print("Notification sent!")


def publish_message_to_external_bus(event: events.Event) -> None:
    redis_client = create_redis_client()
    redis_client.publish_channel_message(event)


def create_order_item(cmd: commands.CreateOrderItem, uow: AbstractUnitOfWork) -> UUID:
    with uow:
        product = uow.products.get(cmd.sku_id)
        order_item = domain.create_order_item(product.sku, cmd.quantity)
        product.register_order_item(order_item)
        return order_item.uuid


def create_product(cmd: commands.CreateProductCommand, uow: AbstractUnitOfWork) -> UUID:
    with uow:
        product = domain.create_product(cmd.sku)
        uow.products.add(product)
        return product.sku_id


def create_batch(cmd: commands.CreateBatch, uow: AbstractUnitOfWork) -> UUID:
    with uow:
        product = uow.products.get(cmd.sku_id)
        batch = domain.create_batch(product.sku, cmd.quantity, cmd.eta)
        product.register_batch(batch)
        return batch.uuid


def allocate(cmd: commands.Allocate, uow: AbstractUnitOfWork) -> UUID:
    """Takes an order item and allocates available stock from known batches."""
    with uow:
        product = uow.products.get(cmd.sku_id)
        all_order_items = uow.products.get_all_order_items()
        order_item = next(oi for oi in all_order_items if oi.uuid == cmd.order_item_id)
        batch = product.allocate(order_item)
        return batch.uuid


def change_batch_quantity(
    cmd: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork
) -> UUID:
    with uow:
        product = uow.products.get(cmd.sku_id)
        batch = product.change_batch_quantity(cmd.batch_id, cmd.new_quantity)
        return batch.uuid
