import time

from allocation import messagebus, services
from allocation.core import commands, events
from allocation.interfaces.database.db import session_factory
from allocation.interfaces.external_bus import create_redis_client
from allocation.unit_of_work import UnitOfWork
from tests.conftest import (
    make_test_batch,
    make_test_order_item,
    make_test_sku,
    make_test_sku_product_and_batch,
)


def test_redis_connection():
    client = create_redis_client()
    client.set("foo", "bar")
    assert client.get("foo") == b"bar"


def test_publish_event_to_redis_channel():
    client = create_redis_client()
    batch = make_test_batch(make_test_sku())
    event = events.BatchQuantityChanged(batch.uuid, 10)
    client.subscribe_to_channel(type(event))
    client.publish_channel_message(event)
    while True:
        retrieved_event = client.get_channel_message(type(event))
        if retrieved_event:
            assert event == retrieved_event
            break


def test_publish_event_to_redis_channel_via_handler():
    batch = make_test_batch(make_test_sku())
    event = events.BatchQuantityChanged(batch.uuid, 10)
    services.publish_message_to_external_bus(event)


def test_initiate_command_from_external_event():
    with UnitOfWork(session_factory) as uow:
        sku, product, batch = make_test_sku_product_and_batch()
        order_item_1, order_item_2 = make_test_order_item(sku), make_test_order_item(
            sku
        )
        product.allocate(order_item_1)
        product.allocate(order_item_2)
        uow.products.add(product)
        batch_id = batch.uuid
        sku_id = sku.uuid

    redis_client = create_redis_client()
    redis_client.subscribe_to_channel(commands.ChangeBatchQuantity)
    redis_client.subscribe_to_channel(events.OrderItemDeallocated)
    cmd = commands.ChangeBatchQuantity(sku_id, batch_id, 15)
    redis_client.publish_channel_message(cmd)

    while True:
        cmd = redis_client.get_channel_message(commands.ChangeBatchQuantity)
        if cmd:
            messagebus.QUEUE.append(cmd)
            messagebus.handle(messagebus.QUEUE, UnitOfWork(session_factory))
            break
        time.sleep(0.5)

    while True:
        event = redis_client.get_channel_message(events.OrderItemDeallocated)
        if event:
            assert isinstance(event, events.OrderItemDeallocated)
            break
        time.sleep(0.5)
